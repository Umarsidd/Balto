"""CSV parsing and validation for onboarding rows."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from config import Settings
from role_mapping import normalize_country, resolve_country_policy


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


HEADER_ALIASES: Dict[str, Sequence[str]] = {
    "first_name": ("first_name", "firstname", "first name", "given name"),
    "last_name": ("last_name", "lastname", "last name", "surname", "family name"),
    "personal_email": ("personal_email", "personal email", "home email"),
    "work_email": ("work_email", "work email", "email", "company email"),
    "department": ("department", "dept"),
    "job_title": ("job_title", "job title", "title", "role"),
    "country": ("country", "work country", "location country"),
    "start_date": ("start_date", "start date", "hire date", "first day"),
    "manager_email": ("manager_email", "manager email", "manager"),
    "manager_approval_ticket": (
        "manager_approval_ticket",
        "approval ticket",
        "manager approval",
        "manager approval ticket",
    ),
    "employment_type": ("employment_type", "employment type", "worker type"),
}


@dataclass(frozen=True)
class NewHireInput:
    """Raw normalized input from a CSV row."""

    row_number: int
    first_name: str
    last_name: str
    personal_email: str
    work_email: str
    department: str
    job_title: str
    country: str
    start_date: str
    manager_email: str
    manager_approval_ticket: str
    employment_type: str


@dataclass(frozen=True)
class ValidatedHire:
    """Validated hire data safe to pass into provisioning clients."""

    row_number: int
    first_name: str
    last_name: str
    personal_email: str
    work_email: str
    department: str
    job_title: str
    country: str
    start_date: date
    manager_email: str
    manager_approval_ticket: str
    employment_type: str

    @property
    def full_name(self) -> str:
        """Return display name."""

        return f"{self.first_name} {self.last_name}".strip()


@dataclass(frozen=True)
class ValidationIssue:
    """Validation issue attached to a source row."""

    row_number: int
    field: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating all CSV rows."""

    valid_hires: List[ValidatedHire]
    issues: List[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        """Return True if any error-level issue exists."""

        return any(issue.severity == "error" for issue in self.issues)


class CsvValidationError(Exception):
    """Raised when a CSV cannot be parsed at all."""


def parse_new_hire_csv(csv_path: str | Path) -> List[NewHireInput]:
    """Read and normalize an HR CSV export."""

    path = Path(csv_path)
    if not path.exists():
        raise CsvValidationError(f"CSV file does not exist: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CsvValidationError("CSV file has no header row.")

        header_lookup = build_header_lookup(reader.fieldnames)
        rows: List[NewHireInput] = []

        for row_index, row in enumerate(reader, start=2):
            if is_blank_row(row):
                continue

            rows.append(
                NewHireInput(
                    row_number=row_index,
                    first_name=value_for(row, header_lookup, "first_name"),
                    last_name=value_for(row, header_lookup, "last_name"),
                    personal_email=value_for(row, header_lookup, "personal_email"),
                    work_email=value_for(row, header_lookup, "work_email"),
                    department=value_for(row, header_lookup, "department"),
                    job_title=value_for(row, header_lookup, "job_title"),
                    country=value_for(row, header_lookup, "country"),
                    start_date=value_for(row, header_lookup, "start_date"),
                    manager_email=value_for(row, header_lookup, "manager_email"),
                    manager_approval_ticket=value_for(row, header_lookup, "manager_approval_ticket"),
                    employment_type=value_for(row, header_lookup, "employment_type") or "Full-time",
                )
            )

    return rows


def build_header_lookup(fieldnames: Sequence[str]) -> Dict[str, str]:
    """Map canonical field names to actual CSV header names."""

    normalized_to_actual = {normalize_header(name): name for name in fieldnames if name}
    lookup: Dict[str, str] = {}

    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            actual = normalized_to_actual.get(normalize_header(alias))
            if actual:
                lookup[canonical] = actual
                break

    return lookup


def normalize_header(header: str) -> str:
    """Normalize header names for messy CSV exports."""

    return re.sub(r"[^a-z0-9]+", " ", header.strip().lower()).strip()


def value_for(row: Mapping[str, str], header_lookup: Mapping[str, str], canonical_name: str) -> str:
    """Return a stripped CSV value for a canonical field."""

    actual_header = header_lookup.get(canonical_name)
    if not actual_header:
        return ""
    return str(row.get(actual_header, "") or "").strip()


def is_blank_row(row: Mapping[str, str]) -> bool:
    """Return True when a row has no meaningful values."""

    return all(not str(value or "").strip() for value in row.values())


def validate_hires(inputs: Iterable[NewHireInput], settings: Settings) -> ValidationResult:
    """Validate all new hire rows and return valid hires plus issues."""

    issues: List[ValidationIssue] = []
    valid_hires: List[ValidatedHire] = []
    seen_emails: set[str] = set()

    for hire in inputs:
        row_issues = validate_required_fields(hire)

        work_email = hire.work_email.strip().lower()
        manager_email = hire.manager_email.strip().lower()
        personal_email = hire.personal_email.strip().lower()

        if work_email:
            if not EMAIL_PATTERN.match(work_email):
                row_issues.append(issue(hire, "work_email", "Work email is not a valid email address."))
            elif not work_email.endswith(f"@{settings.email_domain}"):
                row_issues.append(issue(hire, "work_email", f"Work email must use @{settings.email_domain}."))
            elif work_email in seen_emails:
                row_issues.append(issue(hire, "work_email", "Duplicate work email in CSV."))
            else:
                seen_emails.add(work_email)

        if personal_email and not EMAIL_PATTERN.match(personal_email):
            row_issues.append(issue(hire, "personal_email", "Personal email is not valid."))

        if manager_email:
            if not EMAIL_PATTERN.match(manager_email):
                row_issues.append(issue(hire, "manager_email", "Manager email is not valid."))
            elif not manager_email.endswith(f"@{settings.email_domain}"):
                row_issues.append(issue(hire, "manager_email", f"Manager email must use @{settings.email_domain}."))
            elif manager_email == work_email:
                row_issues.append(issue(hire, "manager_email", "Manager cannot be the new hire."))

        start_date = parse_start_date(hire.start_date)
        if start_date is None:
            row_issues.append(issue(hire, "start_date", "Start date is missing or invalid."))

        country_policy = resolve_country_policy(hire.country, settings.allowed_countries)
        if not country_policy.supported:
            row_issues.append(
                issue(
                    hire,
                    "country",
                    f"Country '{normalize_country(hire.country)}' is not in the supported country allowlist.",
                )
            )

        issues.extend(row_issues)

        if not any(row_issue.severity == "error" for row_issue in row_issues) and start_date is not None:
            valid_hires.append(
                ValidatedHire(
                    row_number=hire.row_number,
                    first_name=hire.first_name.strip(),
                    last_name=hire.last_name.strip(),
                    personal_email=personal_email,
                    work_email=work_email,
                    department=hire.department.strip(),
                    job_title=hire.job_title.strip(),
                    country=country_policy.country,
                    start_date=start_date,
                    manager_email=manager_email,
                    manager_approval_ticket=hire.manager_approval_ticket.strip(),
                    employment_type=hire.employment_type.strip() or "Full-time",
                )
            )

    return ValidationResult(valid_hires=valid_hires, issues=issues)


def validate_required_fields(hire: NewHireInput) -> List[ValidationIssue]:
    """Validate required fields before semantic checks."""

    required_fields = {
        "first_name": hire.first_name,
        "last_name": hire.last_name,
        "work_email": hire.work_email,
        "department": hire.department,
        "job_title": hire.job_title,
        "country": hire.country,
        "start_date": hire.start_date,
        "manager_email": hire.manager_email,
    }

    return [
        issue(hire, field_name, "Required field is missing.")
        for field_name, value in required_fields.items()
        if not str(value or "").strip()
    ]


def parse_start_date(value: str) -> date | None:
    """Parse common HR date formats.

    Ambiguous numeric formats are supported because HR exports are often messy.
    The report preserves the normalized ISO date so reviewers can spot errors.
    """

    cleaned = str(value or "").strip()
    if not cleaned:
        return None

    formats = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d %Y", "%B %d %Y")
    for date_format in formats:
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    return None


def issue(hire: NewHireInput, field: str, message: str, severity: str = "error") -> ValidationIssue:
    """Create a validation issue."""

    return ValidationIssue(row_number=hire.row_number, field=field, message=message, severity=severity)
