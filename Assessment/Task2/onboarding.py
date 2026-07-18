"""Balto onboarding automation assessment implementation.

The module is intentionally unit-test-friendly: parsing, validation, mapping,
and provisioning orchestration are separated and injectable mock clients are
used by default.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from config import Settings, configure_logging, load_settings
from mock_google import MockGoogleClient
from mock_iru import MockIruClient
from mock_okta import MockOktaClient
from mock_slack import MockSlackClient
from role_mapping import (
    resolve_country_policy,
    resolve_department_access,
    resolve_role_access,
    unique_preserving_order,
)
from validators import (
    CsvValidationError,
    ValidatedHire,
    ValidationIssue,
    parse_new_hire_csv,
    validate_hires,
)


LOGGER = logging.getLogger(__name__)


@dataclass
class ProvisioningStep:
    """Single provisioning step result."""

    name: str
    status: str
    details: Dict[str, object] = field(default_factory=dict)


@dataclass
class HireProvisioningResult:
    """Provisioning result for one hire."""

    row_number: int
    work_email: str
    full_name: str
    status: str
    role_profile: str
    department_profile: str
    country: str
    warnings: List[str] = field(default_factory=list)
    steps: List[ProvisioningStep] = field(default_factory=list)
    welcome_message: str = ""


@dataclass
class OnboardingReport:
    """Structured report emitted by the onboarding automation."""

    generated_at: str
    dry_run: bool
    source_csv: str
    valid_row_count: int
    invalid_issue_count: int
    processed_count: int
    blocked_count: int
    validation_issues: List[Dict[str, object]]
    results: List[Dict[str, object]]


@dataclass
class OnboardingClients:
    """Provisioning client bundle for dependency injection."""

    okta: MockOktaClient
    google: MockGoogleClient
    iru: MockIruClient
    slack: MockSlackClient


def build_default_clients(settings: Settings) -> OnboardingClients:
    """Build default mock clients."""

    return OnboardingClients(
        okta=MockOktaClient(dry_run=settings.dry_run),
        google=MockGoogleClient(dry_run=settings.dry_run),
        iru=MockIruClient(dry_run=settings.dry_run),
        slack=MockSlackClient(settings=settings),
    )


def process_onboarding(
    csv_path: str | Path,
    settings: Settings,
    clients: Optional[OnboardingClients] = None,
) -> OnboardingReport:
    """Process a new-hire CSV and return a structured onboarding report."""

    source_csv = str(csv_path)
    clients = clients or build_default_clients(settings)

    raw_hires = parse_new_hire_csv(csv_path)
    validation_result = validate_hires(raw_hires, settings)

    results: List[HireProvisioningResult] = []
    for hire in validation_result.valid_hires:
        results.append(provision_hire(hire, settings, clients))

    blocked_count = sum(1 for result in results if result.status == "blocked")
    report = OnboardingReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        dry_run=settings.dry_run,
        source_csv=source_csv,
        valid_row_count=len(validation_result.valid_hires),
        invalid_issue_count=len(validation_result.issues),
        processed_count=sum(1 for result in results if result.status == "processed"),
        blocked_count=blocked_count,
        validation_issues=[asdict(issue) for issue in validation_result.issues],
        results=[serialize_result(result) for result in results],
    )
    return report


def provision_hire(
    hire: ValidatedHire,
    settings: Settings,
    clients: OnboardingClients,
) -> HireProvisioningResult:
    """Provision one validated hire through mock services."""

    role_access = resolve_role_access(hire.job_title, hire.department)
    department_access = resolve_department_access(hire.department)
    country_policy = resolve_country_policy(hire.country, settings.allowed_countries)
    warnings: List[str] = []

    if country_policy.notes:
        warnings.append(country_policy.notes)

    manager_approval_needed = (
        role_access.requires_manager_approval
        or role_access.privileged
        or department_access.privileged_department
    )

    if manager_approval_needed and not hire.manager_approval_ticket:
        # SOC2 and least privilege: privileged access is not granted without
        # manager evidence. We block provisioning rather than silently reducing
        # access because day-one access should be intentionally reviewed.
        return HireProvisioningResult(
            row_number=hire.row_number,
            work_email=hire.work_email,
            full_name=hire.full_name,
            status="blocked",
            role_profile=role_access.name,
            department_profile=department_access.department,
            country=hire.country,
            warnings=warnings
            + [
                "Manager approval ticket is required before provisioning privileged or unknown-role access."
            ],
        )

    okta_groups = unique_preserving_order(list(role_access.okta_groups))
    google_groups = unique_preserving_order(list(department_access.google_groups))
    steps: List[ProvisioningStep] = []

    okta_user_response = clients.okta.create_user(hire)
    okta_user = okta_user_response["user"]
    steps.append(ProvisioningStep(name="okta_create_user", status=str(okta_user_response["status"]), details=okta_user_response))

    okta_group_response = clients.okta.assign_groups(str(okta_user["id"]), okta_groups)
    steps.append(
        ProvisioningStep(
            name="okta_assign_groups",
            status="completed",
            details={"groups": okta_group_response, "rationale": role_access.rationale},
        )
    )

    google_user_response = clients.google.create_workspace_user(hire)
    steps.append(
        ProvisioningStep(
            name="google_create_user",
            status=str(google_user_response["status"]),
            details=google_user_response,
        )
    )

    license_response = clients.google.assign_license(hire.work_email, hire.employment_type)
    steps.append(ProvisioningStep(name="google_assign_license", status="completed", details=license_response))

    google_group_response = clients.google.add_to_groups(hire.work_email, google_groups)
    steps.append(
        ProvisioningStep(
            name="google_add_groups",
            status="completed",
            details={"groups": google_group_response, "rationale": department_access.rationale},
        )
    )

    iru_response = clients.iru.assign_blueprint(hire, department_access.iru_blueprint)
    steps.append(ProvisioningStep(name="iru_assign_blueprint", status=str(iru_response["status"]), details=iru_response))

    welcome = clients.slack.generate_welcome_message(hire)
    slack_response = clients.slack.send_message("#new-hires", str(welcome["message"]))
    steps.append(
        ProvisioningStep(
            name="slack_welcome",
            status=str(slack_response["status"]),
            details={"fallback_used": welcome["fallback_used"], "reason": welcome["reason"]},
        )
    )

    return HireProvisioningResult(
        row_number=hire.row_number,
        work_email=hire.work_email,
        full_name=hire.full_name,
        status="processed",
        role_profile=role_access.name,
        department_profile=department_access.department,
        country=hire.country,
        warnings=warnings,
        steps=steps,
        welcome_message=str(welcome["message"]),
    )


def serialize_result(result: HireProvisioningResult) -> Dict[str, object]:
    """Serialize result dataclasses into JSON-friendly dictionaries."""

    serialized = asdict(result)
    serialized["steps"] = [asdict(step) for step in result.steps]
    return serialized


def write_report(report: OnboardingReport, output_path: str | Path | None) -> None:
    """Write report JSON to stdout or a file."""

    payload = json.dumps(asdict(report), indent=2, sort_keys=True, default=str)
    if output_path:
        Path(output_path).write_text(payload + "\n", encoding="utf-8")
        LOGGER.info("Report written to %s", output_path)
        return
    print(payload)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Process Balto onboarding CSV.")
    parser.add_argument("--csv", default="sample_new_hires.csv", help="Path to HR CSV export.")
    parser.add_argument("--output", default="", help="Optional path for JSON report.")
    parser.add_argument("--env-file", default=".env", help="Path to .env file.")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    args = parse_args(argv)
    settings = load_settings(args.env_file)
    if args.dry_run:
        settings = Settings(**{**settings.__dict__, "dry_run": True})

    configure_logging(settings.log_level)

    try:
        report = process_onboarding(args.csv, settings)
        write_report(report, args.output or None)
    except CsvValidationError as exc:
        LOGGER.error("CSV validation failed: %s", exc)
        return 2
    except Exception:
        LOGGER.exception("Onboarding automation failed.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
