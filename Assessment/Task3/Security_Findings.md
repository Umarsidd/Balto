# Task 3 - Security Findings

## Review Scope

This review assesses a representative broken IT workflow automation used to grant access based on Slack approvals. The assessment focuses on logic bugs, security bugs, SOC2 issues, race conditions, approval flaws, authentication flaws, audit issues, error handling issues, least privilege issues, and idempotency issues.

The recommended fixed implementation is provided in `fixed_workflow.py`.

## Findings

| ID | Category | Finding | Why it matters | Recommendation | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|---|---|
| SEC-01 | Authentication flaw | Slack approval payload is trusted without verifying Slack signature. | Anyone who can reach the endpoint could forge an approval. | Verify `X-Slack-Signature` and `X-Slack-Request-Timestamp` using the Slack signing secret. | Requires storing and rotating another secret. | Forged privileged access. | Trust source IP, rejected because IP ranges change and are weaker than request signing. |
| SEC-02 | Approval flaw | Approver identity is taken from request text rather than signed Slack metadata. | A requester can type a manager's email and appear approved. | Extract approver from verified Slack payload and compare to manager directory. | Requires Slack user email resolution in production. | Self-approval and separation of duties failure. | Manual approval review, acceptable fallback but not automation. |
| SEC-03 | Manager validation | The workflow does not verify that the approver is the user's manager. | Manager approval evidence is meaningless if any employee can approve. | Compare target user to HR or directory manager record. | Directory data must be kept current. | Unauthorized access approved by wrong person. | Department approver only, weaker for individual access. |
| SEC-04 | Authorization flaw | Any requester can trigger access changes. | Access automation should only accept requests from approved systems or IT roles. | Enforce requester allowlist or service account identity. | Requires maintenance when IT staff changes. | Abuse by compromised employee account. | Open endpoint, rejected. |
| SEC-05 | Least privilege | Workflow accepts arbitrary group names from request payload. | A malformed or malicious request can assign admin groups. | Use a group allowlist and map business roles to approved groups. | New groups require mapping updates. | Privilege escalation. | Regex blocklist, rejected because deny lists miss new sensitive groups. |
| SEC-06 | Privileged access | High-risk groups do not require additional evidence. | Finance, IT, source code, and production groups need stronger review. | Mark privileged groups and require manager evidence plus Security ticket where appropriate. | More friction for privileged roles. | SOC2 access control failure. | Treat all groups equally, rejected. |
| SEC-07 | Race condition | Concurrent approvals can process the same request twice. | Duplicate actions can cause inconsistent state and confusing evidence. | Use idempotency keys and atomic claim/complete behavior. | Requires state store. | Double provisioning or conflicting transitions. | Rely on API idempotency only, incomplete because not all services support it. |
| SEC-08 | Idempotency | Re-running a request creates duplicate grants or repeated Slack messages. | Automations must be safe to retry. | Use deterministic key from request ID, user, and target group. | Requires tracking completed operations. | Duplicate access and noisy evidence. | Manual dedupe, rejected. |
| SEC-09 | Audit issue | Logs are unstructured and omit request IDs, actor, decision, and target. | Auditors cannot reconstruct what happened. | Write JSONL audit events with correlation IDs and statuses. | More log volume. | SOC2 evidence gap. | Console logs only, rejected. |
| SEC-10 | Audit integrity | Sensitive tokens and raw payloads are logged. | Logs can become a secret exposure path. | Redact signatures, tokens, and secrets before logging. | Debugging is slightly harder. | Credential leakage. | Full raw logs, rejected. |
| SEC-11 | Error handling | API failures are swallowed and workflow reports success. | IT may believe access was granted or denied when it was not. | Raise typed exceptions and record failure status. | More explicit failure handling. | Missed onboarding or unauthorized partial state. | Best-effort silent retry, rejected. |
| SEC-12 | Retry handling | External API calls are not retried. | Temporary failures become manual incidents. | Retry transient operations with bounded exponential backoff. | Longer runtime. | Workflow brittleness. | Infinite retry, rejected because it can duplicate changes and hide failure. |
| SEC-13 | Secure transition logic | Workflow removes old groups and adds new groups without checking conflicts. | Role changes can accidentally remove required access or combine conflicting access. | Detect mutually exclusive group conflicts and require manual review. | Some transitions need human intervention. | Excessive or broken access. | Automatically remove all old groups, rejected as destructive. |
| SEC-14 | Input validation | Emails and request IDs are not validated. | Bad inputs can target wrong users or corrupt audit evidence. | Validate email format and required fields before action. | Additional validation code. | Access granted to wrong identity. | Trust upstream form, rejected because defense in depth matters. |
| SEC-15 | SOC2 evidence | Approvals lack reason, timestamp, and reviewer identity. | SOC2 auditors need proof of authorization and review. | Store request, approver, timestamp, reason, result, and system response. | Requires structured event schema. | Audit finding. | Screenshot Slack thread manually, weak and labor-intensive. |
| SEC-16 | Separation of duties | Requester can approve their own request. | Self-approval undermines access control. | Reject approvals where requester, target user, and approver relationships violate policy. | Edge cases need delegate handling. | Unauthorized access. | Allow self-approval below threshold, rejected. |
| SEC-17 | Secret management | Signing secret and API tokens are hardcoded. | Source code leaks become credential leaks. | Read secrets from environment variables or secret manager. | Requires deployment configuration. | Persistent unauthorized access. | Config file in repo, rejected. |
| SEC-18 | Non-repudiation | Slack reactions are treated as approvals. | Reactions do not carry enough structured context and are easy to misread. | Use signed Slack interactive actions or recorded manager comments with ticket links. | More setup. | Ambiguous approval evidence. | Emoji approvals, rejected. |
| SEC-19 | Partial failure | User is added to one system but workflow fails before logging. | Actual access can diverge from evidence. | Log before and after each action and reconcile failed operations. | More logging. | Orphaned access. | End-only logging, rejected. |
| SEC-20 | Overbroad service account | Automation token can administer all groups. | A compromised automation account becomes a broad privilege escalation path. | Scope token to only allowed groups and required actions. | Requires platform support and careful setup. | Major breach impact. | Full admin token, rejected. |

## Priority Fixes

1. Verify Slack signatures and timestamps before parsing approval data.
2. Enforce requester authorization and manager validation.
3. Replace arbitrary group input with group allowlists.
4. Add idempotency and audit logging before production use.
5. Treat privileged access as a separate approval path.

## Residual Risks

| Risk | Mitigation |
|---|---|
| HR manager directory is stale | Add manager reconciliation with HRIS before relying on approvals. |
| Slack email may be unavailable in payload | Production Slack app should resolve user ID to email through Slack API. |
| Some group transitions require nuance | Detect conflicts and route to manual review instead of auto-changing access. |
| Audit logs can be edited if stored locally | Production should write to immutable logging or ticketing system. |
