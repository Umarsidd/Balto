# Task 3 - Fixed Workflow Security Notes

## What `fixed_workflow.py` Implements

| Control | Implementation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Slack authentication | HMAC verification of Slack signature and timestamp. | Proves request originated from Slack and is fresh. | Requires signing secret handling. | Forged approvals if skipped. | Source IP allowlist, weaker. |
| Requester authorization | `allowed_requesters` allowlist. | Only trusted systems or IT can invoke access automation. | Allowlist maintenance. | Employee abuse if open. | Open endpoint, rejected. |
| Manager validation | Compares request manager to trusted directory. | Prevents arbitrary approvers. | Requires accurate HR data. | Wrong manager can approve access. | Trust form field only, rejected. |
| Approval verification | Slack action, request ID, approver email, and self-approval checks. | Ensures approval matches the exact request. | Slack app must expose or resolve approver email. | Replay or mismatched approvals. | Emoji approvals, rejected. |
| Least privilege | `group_allowlist` enforced at validation and provisioner. | Prevents arbitrary group assignment. | Requires mapping updates. | Privilege escalation. | Regex blocklist, rejected. |
| Privileged groups | Optional security approval ticket for defined groups. | Stronger evidence for high-risk access. | Adds approval friction. | High-risk access without review. | Same path for every group, rejected. |
| Idempotency | Deterministic key and claim/complete state. | Safe retries and duplicate approval handling. | Requires state store. | Duplicate provisioning. | Rely on API behavior only, incomplete. |
| Audit logging | JSONL events before and after decisions. | SOC2 evidence and incident reconstruction. | Local JSONL is not immutable. | Weak audit trail. | Console logs only, rejected. |
| Retry handling | Bounded exponential retry for provisioning calls. | Handles transient API failures. | Longer execution time. | Noisy failures. | Infinite retry, rejected. |
| Secure transition | Mutually exclusive group conflict detection. | Prevents unsafe role transitions. | Some changes require manual review. | Conflicting access combinations. | Auto-remove conflicts, rejected as destructive. |

## Deployment Notes

Production deployment should replace:

- `InMemoryIdempotencyStore` with Redis, DynamoDB, Postgres, or the ticketing system.
- `JsonlAuditLogger` with immutable logging, SIEM, or ticket audit fields.
- `MockGroupProvisioner` with scoped Okta or Google group APIs.
- Inline `manager_directory` with HRIS or directory lookup.

## Environment Variables

| Variable | Purpose |
|---|---|
| `SLACK_SIGNING_SECRET` | Verify Slack interactive request signatures. |
| `ACCESS_WORKFLOW_ALLOWED_REQUESTERS` | Comma-separated IT service accounts. |
| `ACCESS_WORKFLOW_GROUP_ALLOWLIST` | Comma-separated groups automation can assign. |
| `ACCESS_WORKFLOW_PRIVILEGED_GROUPS` | Comma-separated groups requiring stronger review. |

## Testing Strategy

1. Unit test Slack signature verification with valid and invalid signatures.
2. Unit test stale Slack timestamps.
3. Unit test self-approval rejection.
4. Unit test wrong-manager rejection.
5. Unit test group allowlist rejection.
6. Unit test idempotent duplicate processing.
7. Unit test mutually exclusive group conflict detection.
8. Unit test audit redaction for secret-like fields.

## Production Risk Notes

Local JSONL audit logs are acceptable for an assessment but not enough for production. A real deployment should write audit events to an immutable logging platform or ticket system with retention aligned to SOC2 evidence requirements.
