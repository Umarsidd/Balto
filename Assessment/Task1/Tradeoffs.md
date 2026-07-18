# Task 1 - Tradeoffs and Edge Cases

## Design Tradeoffs

| Decision | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Use managed Google tooling instead of a custom application. | Maintains a low support burden for a one-person IT team. | Less polished UX and fewer workflow controls. | Sheet-based workflows can drift without ownership. | Custom app, rejected for ongoing maintenance cost. |
| Keep LLM advisory only. | Human approvers remain accountable for business and security decisions. | Reviewers still need to read and decide. | Over-trusting model output can create bad approvals. | Full auto-approval for low-risk requests, rejected initially. |
| Store prompts and model responses. | SOC2 evidence should show what the automation used. | Prompts may include sensitive context and need access control. | Overexposure if the Sheet is broadly shared. | Do not store prompts, rejected because decisions become hard to reconstruct. |
| Use mock vendor research in v1. | Avoids brittle scraping and extra vendor dependencies. | Research quality is limited. | Mock data may be mistaken for verified data. | Internet scraping, rejected for reliability and security. |
| Use Slack webhook for notifications. | Fast to deploy. | Webhook posts are not strong signed approvals. | Approval comments may be missed. | Slack app, stronger but more operational overhead. |

## Edge Cases

| Edge case | Expected handling | SOC2 impact |
|---|---|---|
| Requester submits an urgent request after already using the tool | Mark as policy exception, route to manager and Security, document remediation. | Shows exception handling rather than pretending the control worked. |
| Vendor uses subprocessors not listed by requester | Security reviewer updates evaluation record before approval. | Maintains evidence quality. |
| Tool is free but handles customer data | Cost does not reduce security review. | Demonstrates risk based review. |
| Tool is already in use by another team | Link requests, assign shared owner, verify access review coverage. | Prevents duplicate vendor records. |
| Requester cannot determine OAuth scopes | Treat as unknown risk and require technical owner review. | Avoids approving broad access blindly. |
| Vendor supports SSO only on enterprise plan | Finance and IT decide whether SSO plan is required or manual review is acceptable. | Shows compensating control decision. |
| Contractor requests a tool | Employee sponsor must submit and own the request. | Maintains accountable Balto owner. |
| Business owner leaves Balto | Quarterly review reassigns ownership before renewal. | Prevents orphaned vendors. |
| LLM service unavailable | Request remains visible with `NEEDS_MANUAL_REVIEW`. | Evidence shows system failure and manual fallback. |
| Sensitive data accidentally entered in free text | IT should redact from Slack summary and restrict Sheet access; do not send unnecessary raw data to LLM in future submissions. | Shows data minimization and incident awareness. |

## Security Boundaries

The automation must not:

- Approve a vendor by itself.
- Provision access to a new tool.
- Send production secrets to an LLM.
- Treat Slack reactions as final approval evidence.
- Trust requester classification without review.
- Assume Okta group membership perfectly maps to job responsibility.

## Operational Risks

| Risk | Mitigation |
|---|---|
| One IT owner is unavailable | Document deployment, keep backup owner, store config in Script Properties, and export Sheet periodically. |
| Apps Script ownership tied to a user | Use a shared IT automation account where policy permits. |
| Form changes break header mapping | Apps Script uses normalized header names and logs missing required fields. |
| Too many manual exceptions | Review trends quarterly and prioritize SSO or tooling consolidation. |
| Reviewers ignore Slack | Add status queue in Sheet and weekly reminder. |

## Implementation Recommendation

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Launch with a narrow scope: only New Software Tool Evaluation. | Keeps v1 reliable and auditable. | Other request types remain manual. | Users may expect all branches to be automated. | Automate every branch immediately, rejected because scope would be too broad. |
| Add a monthly audit of the evaluation Sheet for stale requests. | Prevents requests from disappearing. | Adds recurring task. | Open requests can become unmanaged shadow IT. | Rely on Slack reminders only, rejected. |
| Keep approval thresholds simple. | Reviewers can remember and enforce them. | Some edge cases need judgment. | Overly complex rules break down in practice. | Highly granular scoring model, rejected for maintainability. |
