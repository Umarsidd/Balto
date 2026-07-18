"""Hardened Slack-approved access workflow.

This file rewrites a broken access automation pattern with controls expected in
an IT Operations and SOC2 environment: signed approval verification, manager
validation, idempotency, audit logging, least privilege, retry handling, and
secure group transition checks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


LOGGER = logging.getLogger(__name__)
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class WorkflowError(Exception):
    """Base class for workflow failures."""


class AuthorizationError(WorkflowError):
    """Raised when the requester is not allowed to invoke the workflow."""


class ApprovalVerificationError(WorkflowError):
    """Raised when Slack approval verification fails."""


class ValidationError(WorkflowError):
    """Raised when request data is invalid."""


class IdempotencyConflictError(WorkflowError):
    """Raised when an idempotency key is already in progress."""


@dataclass(frozen=True)
class WorkflowConfig:
    """Security-sensitive workflow configuration."""

    allowed_requesters: frozenset[str]
    group_allowlist: frozenset[str]
    privileged_groups: frozenset[str]
    manager_directory: Mapping[str, str]
    slack_signing_secret: str
    audit_log_path: Path = Path("access_workflow_audit.jsonl")
    security_approval_required_groups: frozenset[str] = frozenset()
    retry_attempts: int = 3
    retry_base_seconds: float = 0.25
    slack_max_age_seconds: int = 300
    exclusive_group_sets: Tuple[frozenset[str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TransitionRequest:
    """Access change request produced by a trusted intake system."""

    request_id: str
    requester_email: str
    target_user_email: str
    requested_group: str
    manager_email: str
    business_reason: str
    security_approval_ticket: str = ""


@dataclass(frozen=True)
class VerifiedSlackApproval:
    """Approval data extracted from a signed Slack action."""

    request_id: str
    approver_email: str
    action: str
    approved_at: str


@dataclass(frozen=True)
class AuditEvent:
    """Structured audit event for SOC2 evidence."""

    timestamp: str
    request_id: str
    event_type: str
    actor: str
    status: str
    details: Mapping[str, object]


@dataclass
class InMemoryIdempotencyStore:
    """Simple idempotency store for tests and local runs."""

    states: MutableMapping[str, str] = field(default_factory=dict)

    def claim(self, key: str) -> None:
        """Claim an idempotency key before side effects."""

        state = self.states.get(key)
        if state == "completed":
            raise IdempotencyConflictError("Request was already completed.")
        if state == "in_progress":
            raise IdempotencyConflictError("Request is already in progress.")
        self.states[key] = "in_progress"

    def complete(self, key: str) -> None:
        """Mark an idempotency key complete after side effects."""

        self.states[key] = "completed"

    def fail(self, key: str) -> None:
        """Release an idempotency key after a failed attempt."""

        self.states.pop(key, None)


@dataclass
class JsonlAuditLogger:
    """Append-only JSONL audit logger.

    Production should send these events to immutable logging or a ticketing
    system. JSONL is used here because it is simple, reviewable, and testable.
    """

    path: Path

    def log(self, event: AuditEvent) -> None:
        """Write a redacted audit event."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(redact_mapping(asdict(event)), sort_keys=True) + "\n")


@dataclass
class MockGroupProvisioner:
    """Mock least-privilege group provisioner."""

    group_allowlist: frozenset[str]
    user_groups: MutableMapping[str, set[str]] = field(default_factory=dict)

    def current_groups(self, user_email: str) -> set[str]:
        """Return current groups for secure transition checks."""

        return set(self.user_groups.get(user_email, set()))

    def assign_group(self, user_email: str, group: str) -> Dict[str, object]:
        """Assign one allowlisted group idempotently."""

        if group not in self.group_allowlist:
            raise AuthorizationError(f"Group is not automation-assignable: {group}")

        groups = self.user_groups.setdefault(user_email, set())
        if group in groups:
            return {"status": "already_member", "user": user_email, "group": group, "idempotent": True}

        groups.add(group)
        return {"status": "assigned", "user": user_email, "group": group, "idempotent": False}


def process_access_request(
    request: TransitionRequest,
    raw_slack_body: bytes,
    slack_headers: Mapping[str, str],
    config: WorkflowConfig,
    provisioner: MockGroupProvisioner,
    idempotency_store: InMemoryIdempotencyStore,
    audit_logger: Optional[JsonlAuditLogger] = None,
) -> Dict[str, object]:
    """Process a signed Slack-approved access request."""

    audit_logger = audit_logger or JsonlAuditLogger(config.audit_log_path)
    idempotency_key = build_idempotency_key(request)

    try:
        audit(audit_logger, request, "REQUEST_RECEIVED", request.requester_email, "started", {})
        validate_transition_request(request, config)
        authorize_requester(request.requester_email, config.allowed_requesters)

        approval = verify_slack_approval(raw_slack_body, slack_headers, config)
        validate_approval(request, approval, config)
        validate_secure_transition(request, provisioner.current_groups(request.target_user_email), config)

        idempotency_store.claim(idempotency_key)

        result = retry(
            lambda: provisioner.assign_group(request.target_user_email, request.requested_group),
            attempts=config.retry_attempts,
            base_seconds=config.retry_base_seconds,
        )
        idempotency_store.complete(idempotency_key)

        audit(
            audit_logger,
            request,
            "ACCESS_GRANTED",
            approval.approver_email,
            "success",
            {"provisioning_result": result, "idempotency_key": idempotency_key},
        )
        return {"status": "success", "request_id": request.request_id, "result": result}

    except IdempotencyConflictError as exc:
        audit(audit_logger, request, "IDEMPOTENCY_CONFLICT", request.requester_email, "blocked", {"error": str(exc)})
        return {"status": "already_processed_or_in_progress", "request_id": request.request_id, "message": str(exc)}
    except Exception as exc:
        idempotency_store.fail(idempotency_key)
        audit(audit_logger, request, "WORKFLOW_FAILED", request.requester_email, "failure", {"error": str(exc)})
        raise


def validate_transition_request(request: TransitionRequest, config: WorkflowConfig) -> None:
    """Validate required fields and allowlisted group."""

    required = {
        "request_id": request.request_id,
        "requester_email": request.requester_email,
        "target_user_email": request.target_user_email,
        "requested_group": request.requested_group,
        "manager_email": request.manager_email,
        "business_reason": request.business_reason,
    }
    missing = [field_name for field_name, value in required.items() if not str(value).strip()]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    for field_name in ("requester_email", "target_user_email", "manager_email"):
        value = getattr(request, field_name)
        if not EMAIL_PATTERN.match(value):
            raise ValidationError(f"Invalid email in {field_name}.")

    if request.requested_group not in config.group_allowlist:
        raise AuthorizationError("Requested group is not in the automation allowlist.")

    expected_manager = config.manager_directory.get(request.target_user_email)
    if not expected_manager:
        raise ValidationError("Target user's manager is not present in the trusted directory.")
    if expected_manager.lower() != request.manager_email.lower():
        raise ValidationError("Request manager does not match trusted directory manager.")

    if request.requested_group in config.security_approval_required_groups and not request.security_approval_ticket:
        raise ApprovalVerificationError("Security approval ticket is required for this group.")


def authorize_requester(requester_email: str, allowed_requesters: Iterable[str]) -> None:
    """Authorize the system or IT account invoking the workflow."""

    if requester_email.lower() not in {email.lower() for email in allowed_requesters}:
        raise AuthorizationError("Requester is not allowed to invoke access automation.")


def verify_slack_approval(
    raw_body: bytes,
    headers: Mapping[str, str],
    config: WorkflowConfig,
) -> VerifiedSlackApproval:
    """Verify Slack signature and parse approval data."""

    signature = header_value(headers, "X-Slack-Signature")
    timestamp = header_value(headers, "X-Slack-Request-Timestamp")
    if not signature or not timestamp:
        raise ApprovalVerificationError("Missing Slack signature headers.")

    verify_slack_signature(
        signing_secret=config.slack_signing_secret,
        timestamp=timestamp,
        raw_body=raw_body,
        provided_signature=signature,
        max_age_seconds=config.slack_max_age_seconds,
    )

    payload = parse_slack_payload(raw_body)
    action = payload.get("actions", [{}])[0]
    user = payload.get("user", {})
    approver_email = str(user.get("email", "")).lower()

    if not approver_email:
        # In production, resolve Slack user ID to email using Slack Web API.
        raise ApprovalVerificationError("Slack payload does not include approver email.")

    return VerifiedSlackApproval(
        request_id=str(action.get("value", "")),
        approver_email=approver_email,
        action=str(action.get("action_id", "")),
        approved_at=datetime.now(timezone.utc).isoformat(),
    )


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    raw_body: bytes,
    provided_signature: str,
    max_age_seconds: int,
) -> None:
    """Verify Slack request signature and freshness."""

    if not signing_secret:
        raise ApprovalVerificationError("Slack signing secret is not configured.")

    try:
        request_time = int(timestamp)
    except ValueError as exc:
        raise ApprovalVerificationError("Invalid Slack timestamp.") from exc

    if abs(int(time.time()) - request_time) > max_age_seconds:
        raise ApprovalVerificationError("Slack approval payload is too old.")

    base = b"v0:" + timestamp.encode("utf-8") + b":" + raw_body
    digest = hmac.new(signing_secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    expected = f"v0={digest}"

    if not hmac.compare_digest(expected, provided_signature):
        raise ApprovalVerificationError("Slack signature verification failed.")


def parse_slack_payload(raw_body: bytes) -> Mapping[str, object]:
    """Parse Slack interactive payload from JSON or form-encoded body."""

    body_text = raw_body.decode("utf-8")
    if body_text.strip().startswith("{"):
        parsed = json.loads(body_text)
    else:
        form = urllib.parse.parse_qs(body_text)
        payload_values = form.get("payload")
        if not payload_values:
            raise ApprovalVerificationError("Slack body did not include payload.")
        parsed = json.loads(payload_values[0])

    if not isinstance(parsed, dict):
        raise ApprovalVerificationError("Slack payload was not an object.")
    return parsed


def validate_approval(
    request: TransitionRequest,
    approval: VerifiedSlackApproval,
    config: WorkflowConfig,
) -> None:
    """Validate the signed Slack approval matches the request and manager."""

    if approval.action != "approve_access":
        raise ApprovalVerificationError("Slack action is not approve_access.")
    if approval.request_id != request.request_id:
        raise ApprovalVerificationError("Slack approval request ID does not match.")
    if approval.approver_email == request.target_user_email.lower():
        raise ApprovalVerificationError("Target user cannot approve their own access.")
    if approval.approver_email != request.manager_email.lower():
        raise ApprovalVerificationError("Approver is not the target user's validated manager.")

    if request.requested_group in config.privileged_groups and not request.business_reason.strip():
        raise ApprovalVerificationError("Privileged access requires business justification.")


def validate_secure_transition(
    request: TransitionRequest,
    current_groups: set[str],
    config: WorkflowConfig,
) -> None:
    """Detect unsafe group transitions before provisioning."""

    for exclusive_set in config.exclusive_group_sets:
        if request.requested_group not in exclusive_set:
            continue
        conflicts = sorted(group for group in current_groups if group in exclusive_set and group != request.requested_group)
        if conflicts:
            raise ValidationError(
                "Requested group conflicts with existing mutually exclusive groups: " + ", ".join(conflicts)
            )


def retry(operation, attempts: int, base_seconds: float) -> object:
    """Retry transient provisioning operations with bounded backoff."""

    last_error: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(base_seconds * (2 ** (attempt - 1)))
    raise last_error or WorkflowError("Retry operation failed without an exception.")


def build_idempotency_key(request: TransitionRequest) -> str:
    """Build a deterministic idempotency key for safe retries."""

    value = f"{request.request_id}:{request.target_user_email.lower()}:{request.requested_group}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def audit(
    audit_logger: JsonlAuditLogger,
    request: TransitionRequest,
    event_type: str,
    actor: str,
    status: str,
    details: Mapping[str, object],
) -> None:
    """Write a structured audit event."""

    audit_logger.log(
        AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request.request_id,
            event_type=event_type,
            actor=actor,
            status=status,
            details=details,
        )
    )


def header_value(headers: Mapping[str, str], name: str) -> str:
    """Return a header value case-insensitively."""

    target = name.lower()
    for header_name, value in headers.items():
        if header_name.lower() == target:
            return value
    return ""


def redact_mapping(value: object) -> object:
    """Redact sensitive keys from audit events."""

    if isinstance(value, dict):
        redacted: Dict[str, object] = {}
        for key, nested_value in value.items():
            if re.search(r"(token|secret|signature|password|authorization)", str(key), re.I):
                redacted[key] = "REDACTED"
            else:
                redacted[key] = redact_mapping(nested_value)
        return redacted
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value


def build_test_slack_headers(raw_body: bytes, signing_secret: str, timestamp: Optional[int] = None) -> Dict[str, str]:
    """Build signed Slack headers for unit tests."""

    request_time = timestamp or int(time.time())
    base = b"v0:" + str(request_time).encode("utf-8") + b":" + raw_body
    digest = hmac.new(signing_secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return {
        "X-Slack-Request-Timestamp": str(request_time),
        "X-Slack-Signature": f"v0={digest}",
    }
