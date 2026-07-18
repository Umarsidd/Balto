# Task 1 - Tooling Decision Table

## Recommended v1 Tooling

| Tool | Use | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Google Forms | Request intake | Native to Google Workspace and fast to maintain. | Limited UI flexibility. | Branching can become hard to manage if too many request types are added. | Custom portal, rejected due to maintenance. |
| Google Sheets | Workflow record and evidence repository | Easy audit export, familiar, access controlled. | Not a full workflow engine. | Manual edits can alter evidence if protections are weak. | Jira or ServiceNow, good later but heavier for 75 people. |
| Google Apps Script | Event orchestration | Runs near the data with low operational burden. | Runtime and testing limitations. | Quotas can be hit if volume grows. | Cloud Functions, better for scale but more infrastructure. |
| Slack Incoming Webhook | Reviewer notifications | Low friction and visible to reviewers. | Webhook cannot validate interactive approvals by itself. | Slack message deletion or channel sprawl. | Slack bot app, better for approvals but more setup. |
| OpenAI or Anthropic API | Structured first-pass evaluation | Produces consistent summaries and routing. | Requires prompt governance and review. | Hallucination if treated as authoritative. | Manual review only, too slow for one-person IT. |
| Script Properties | Secret storage | Avoids hardcoded secrets in Apps Script files. | Access tied to script editors. | Overbroad script editor access exposes secrets. | Hardcoded constants, rejected. |
| Protected Sheets and ranges | Evidence integrity | Reduces accidental edits. | Adds setup work. | Owners can still override protections. | Separate database, better but heavier. |
| Vanta or Drata later | Evidence automation and vendor inventory | Reduces SOC2 manual effort. | Adds cost and implementation. | Poor integration can duplicate work. | Manual evidence folders, acceptable for v1. |

## LLM Provider Decision

| Option | Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| OpenAI API | Preferred default if already approved by Balto | Strong structured output support and broad engineering familiarity. | Requires approved vendor status and API key handling. | Sending sensitive request context to an unapproved provider would be unacceptable. | Anthropic API, equally viable if approved. |
| Anthropic API | Supported fallback | Useful if already contracted or preferred by Security. | Different response format and prompt tuning. | Inconsistent JSON if not constrained. | OpenAI only, rejected to avoid vendor lock-in. |
| No LLM | Manual review mode | Safest for sensitive data if LLM vendor is not approved. | More IT time. | Inconsistent reviews. | Unapproved API use, rejected. |

## Access Model

| Asset | Editors | Viewers | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|---|
| Form | IT only | Domain users can submit | Prevents unauthorized changes to questions and branching. | IT becomes bottleneck for form edits. | Edited questions can break automation. | Department editors, rejected. |
| Response Sheet | IT, Security, Finance as needed | Restricted approvers | Keeps sensitive vendor details controlled. | Reviewers need access requests. | Overexposure of vendor data. | Open to all employees, rejected. |
| Apps Script project | IT only, backup engineer optional | None | Protects secrets and workflow logic. | Single owner risk. | Account loss or role change can break ownership. | Broad admin access, rejected. |
| Slack approval channel | IT, Security, Finance, Legal delegates, exec delegates | No public access | Keeps review discussions contained. | Less transparency to requesters. | Sensitive vendor data in public channels. | Public channel, rejected. |

## Monitoring and Alerting

| Control | Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Failure visibility | Add `Workflow Status`, `Slack Status`, and `Error Message` columns. | IT can scan failures without opening logs. | Requires disciplined status updates. | Silent failures cause missed requests. | Email only, rejected because inbox evidence is weak. |
| Audit trail | Append-only `Audit_Log` Sheet. | Easy SOC2 evidence export. | Sheet can grow large. | Manual edits if protections are weak. | Apps Script execution logs only, rejected because retention is less convenient. |
| Retry logic | Retry external API calls with exponential backoff. | Handles transient failures. | Increases execution time. | Duplicate calls if idempotency is weak. | No retries, rejected due to brittle workflow. |
| Manual review fallback | Mark `NEEDS_MANUAL_REVIEW` instead of failing closed invisibly. | Ensures requests remain visible. | More manual work. | Reviewer might ignore queue. | Auto-reject on error, rejected because system failures should not decide business outcomes. |

## When to Upgrade Tooling

| Signal | Upgrade path |
|---|---|
| More than 10 requests per week | Move state and approvals into ticketing or workflow automation. |
| Frequent sensitive vendor reviews | Integrate Vanta or Drata vendor management. |
| Repeated Slack approval ambiguity | Build a Slack app with signed interactive approvals. |
| Complex multi-step procurement | Integrate procurement and contract lifecycle tooling. |
| Apps Script quota failures | Move orchestration to Cloud Functions or a small internal service. |
