# Task 1 - New Software Tool Evaluation Workflow

## Operating Model

Balto should use Google Forms, Google Sheets, Google Apps Script, Slack, and an LLM API to automate the first-pass evaluation of new software requests. The automation does not approve tools by itself. It gathers evidence, summarizes risk, proposes routing, and creates a consistent review artifact for IT, Security, Finance, Legal, and the business owner.

This is intentionally lightweight because Balto has a 75-person remote workforce and a one-person IT team. The system favors managed services and auditable workflows over custom infrastructure.

## Core Recommendation

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Use Google Form and Sheet as the system of record for intake. | Balto already likely operates in Google Workspace, and Forms/Sheets provide access control, timestamps, and auditability without hosting an app. | Complex branching is less elegant than a custom portal. | Sheet permissions must be tightly managed to avoid exposing vendor/security data. | Custom web app, rejected because maintenance burden is too high for one IT owner. |
| Use Apps Script for orchestration. | Apps Script is close to Forms, Sheets, and Google identity, and avoids new infrastructure. | Apps Script has runtime limits and weaker local testing than Python. | Complex vendor research could hit quotas. | Serverless function, acceptable future improvement but unnecessary for v1. |
| Use Slack only as a notification and approval discussion surface. | Slack is fast for reviewers, but the Sheet remains evidence source. | Slack messages can be edited or deleted. | Treating Slack as the sole audit trail would be weak. | Email approvals, rejected because they are harder to operationalize. |
| Use LLM output as advisory. | LLMs are useful for summarization and routing, not final approvals. | Human reviewers still need to read the record. | Hallucinated vendor facts could cause bad decisions. | Manual-only reviews, rejected because it does not scale. |

## Architecture

| Component | Responsibility | Security considerations | SOC2 evidence |
|---|---|---|---|
| Google Form | Structured intake and requester attestation | Domain-restricted, required sign-in, no anonymous responses | Request timestamp, requester email, form answers |
| Google Sheet | Source of truth for requests, evaluations, and audit logs | Restricted editor group, protected ranges, version history | Review record, status history, prompt and response capture |
| Apps Script | Event handler and workflow orchestrator | Script properties for secrets, least privilege service account, retries | Execution log, status changes, errors |
| LLM API | Summarizes risk and suggests approval routing | No secrets in prompt, minimize sensitive data, log model and prompt | Prompt, model response, risk rationale |
| Vendor research module | Collects vendor context | Mock fallback for v1; production should use approved sources | Vendor facts used in evaluation |
| Slack webhook | Posts review summary to IT/Security channel | Webhook secret in Script Properties, channel restricted | Link to Sheet row and reviewer discussion |

## Trigger

The Apps Script uses an installable `On form submit` trigger attached to the destination Sheet. It reads the submitted row, determines the `Request Type`, and exits unless the request is `New Software Tool Evaluation`.

The script must use an installable trigger rather than a simple trigger because it needs authenticated access to `UrlFetchApp`, Script Properties, and the destination Sheet.

## Workflow Steps

1. Receive form submission event.
2. Acquire a document lock to avoid concurrent updates to the same Sheet.
3. Normalize headers and answers from the submitted row.
4. Detect request type.
5. If request type is not `New Software Tool Evaluation`, append an audit log event and exit.
6. Build a correlation ID and dedupe key.
7. Create or update a row in the `Evaluations` Sheet.
8. Run vendor research.
9. Build the LLM prompt using only necessary data.
10. Call configured LLM provider with retry logic.
11. Parse and validate the JSON response.
12. Write evaluation fields, prompt, raw model response, status, timestamps, and errors to the Sheet.
13. Post a Slack summary with approval gates and reviewer links.
14. Append an immutable audit log row for each major step.
15. Release the lock.

## Sheet Schema

### Form Responses Sheet

The default Google Forms response Sheet is preserved as raw evidence. IT should protect this Sheet from manual editing.

### Evaluations Sheet

| Column | Purpose |
|---|---|
| Correlation ID | Stable ID for logs and Slack references. |
| Form Row Number | Links evaluation to source submission. |
| Submitted At | Form timestamp. |
| Requester Email | Identity evidence. |
| Tool Name | Vendor identifier. |
| Vendor Website | Vendor URL. |
| Vendor Domain | Dedupe and research key. |
| Business Owner | Ongoing owner. |
| Data Classification | Risk input. |
| Estimated Annual Cost | Finance routing input. |
| Risk Rating | LLM advisory rating. |
| Recommendation | Approve, approve with conditions, reject, or needs review. |
| Approval Gates | Required reviewers. |
| Key Risks | Summarized risk list. |
| Compensating Controls | Required controls if approved. |
| Vendor Research JSON | Research facts used by the model. |
| Prompt | Exact prompt sent to model. |
| Model Provider | OpenAI or Anthropic. |
| Model Name | Model version used. |
| Model Response JSON | Parsed model result. |
| Raw Model Response | Original response text. |
| Slack Status | Posted, skipped, or failed. |
| Workflow Status | Completed, needs manual review, failed, skipped. |
| Error Message | Truncated safe error details. |
| Created At | Evaluation record created timestamp. |
| Updated At | Last update timestamp. |

### Audit_Log Sheet

| Column | Purpose |
|---|---|
| Timestamp | Event time. |
| Correlation ID | Joins events to request. |
| Event Type | Trigger received, skipped, LLM called, Slack posted, error, etc. |
| Actor | Automation account or requester. |
| Status | Success, warning, failure. |
| Details JSON | Structured event details with sensitive values removed. |

## Slack Posting

Post to a restricted channel such as `#it-security-approvals`.

The message should include:

- Tool name and requester.
- Business owner and technical owner.
- Risk rating.
- Recommendation.
- Approval gates.
- Top risks.
- Required compensating controls.
- Link to the evaluation Sheet row.
- Reminder that the Slack message is not the source of truth.

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Post concise Slack summaries, not full prompts or raw model output. | Reviewers need signal without exposing unnecessary request details in Slack. | Reviewers must open the Sheet for full evidence. | Overly detailed Slack posts can leak sensitive vendor or customer data. | Full Slack dump, rejected for data minimization. |

## Approval Gates

| Gate | Trigger | Required approver | Evidence |
|---|---|---|---|
| Manager approval | Any new tool affecting a team workflow | Requester's manager | Approval comment or ticket link |
| Business owner approval | Any tool entering pilot or production | Named business owner | Approval status in Sheet |
| IT approval | All tools | IT owner | Evaluation record and access plan |
| Security approval | Sensitive data, broad OAuth, AI training risk, production integration, no SSO | Security owner | Security review notes |
| Finance approval | Annual cost >= 5000 USD | Budget owner or Finance | Budget approval evidence |
| Executive approval | Annual cost >= 25000 USD or multi-year contract | CFO, COO, or delegated exec | Executive approval evidence |
| Legal approval | DPA, MSA, personal data, vendor terms, AI training ambiguity | Legal owner or delegate | Contract review evidence |

## Escalation Logic

| Condition | Escalation |
|---|---|
| Customer data and no SOC2 Type II | Security review plus compensating controls. |
| Personal data and no DPA | Legal review before pilot. |
| Password-only authentication | IT exception, named deprovisioning owner, quarterly manual access review. |
| AI training by default | Security and Legal review; prohibit sensitive data until contract terms are verified. |
| Broad OAuth scopes | Technical owner and Security review; require scope reduction if possible. |
| Vendor cannot support deletion | Security and Legal review for retention risk. |
| Requester asks for urgent approval | Same controls apply; IT can flag priority but cannot bypass approval evidence. |

## Vendor Lookup

The v1 implementation uses mock vendor research when no approved vendor research API is configured. The mock explicitly labels facts as `MOCK` and should not be treated as verified evidence.

Production improvements:

- Pull vendor security URLs from an approved vendor inventory.
- Integrate with a procurement platform or Vanta/Drata vendor module.
- Cache vendor facts by domain to reduce LLM calls.
- Require human verification before final approval.
- Add allowlisted external sources instead of open internet scraping.

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Start with mocked vendor lookup but require human verification. | It keeps the assessment deterministic and deployable without buying another tool. | Vendor facts are incomplete. | Reviewers may over-trust mock output if labeling is unclear. | Build a scraper, rejected because web scraping is brittle and risky for one IT owner. |

## Error Handling

| Failure | Handling |
|---|---|
| Missing request type | Write `FAILED_VALIDATION`, post no Slack message, log error. |
| Non-target request type | Write `SKIPPED_NON_TARGET_REQUEST`, log event. |
| LLM API timeout | Retry with exponential backoff, then mark `NEEDS_MANUAL_REVIEW`. |
| LLM invalid JSON | Store raw response, mark `NEEDS_MANUAL_REVIEW`, include parse error. |
| Slack webhook failure | Store evaluation and mark Slack status failed. |
| Sheet write failure | Retry; if still failing, Apps Script execution log becomes emergency evidence. |
| Concurrent submissions | Use document lock and correlation IDs. |

## Security Controls

- Store API keys and Slack webhook URLs in Script Properties.
- Restrict script editor access to IT.
- Restrict destination Sheet editors to least privilege reviewer groups.
- Do not include secrets, API keys, passwords, or customer records in prompts.
- Log prompt and model response because they are part of the approval artifact.
- Protect formula columns and audit log Sheets.
- Use a dedicated Slack channel with limited membership.
- Rotate webhook and API keys when IT ownership changes.

## SOC2 Evidence Map

| Control objective | Evidence |
|---|---|
| Vendor review before use | Form response, evaluation row, approval gates. |
| Access and authentication consideration | Form answers and LLM risk summary. |
| Security review of sensitive vendors | Security approval gate and notes. |
| Change management | Request timestamp, business justification, approvals. |
| Audit logging | Audit_Log Sheet and Apps Script execution history. |
| Least privilege | Authentication fields, group/access owner, manual review requirements. |

## Production Improvements

| Improvement | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Move approvals into a ticketing system when volume grows. | Tickets provide stronger workflow states and assignment. | Adds licensing and admin overhead. | Staying in Sheets too long can create process drift. | Build custom approval UI, rejected for maintainability. |
| Add Vanta or Drata vendor management integration. | Reduces manual evidence collection during SOC2. | Cost and implementation time. | Duplicate evidence if not integrated cleanly. | Manual folders, acceptable for v1 but not ideal long term. |
| Add reviewer SLA and reminders. | Prevents requests from stalling. | More automation complexity. | Too many reminders create alert fatigue. | Manual follow-up, accepted initially for low volume. |
| Add signed approval records. | Stronger evidence than Slack comments. | Requires additional tooling or process. | Slack reactions alone are weak evidence. | Email approvals, less structured. |
