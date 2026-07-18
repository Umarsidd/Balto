# Task 1 - Reflection

## Why This Design Fits Balto

Balto needs a process that is structured enough for SOC2 and light enough for a one-person IT team. A full procurement platform may be appropriate later, but the first version should use tools Balto can operate tomorrow: Google Forms, Sheets, Apps Script, Slack, and an approved LLM API.

The design intentionally separates automation from approval. The AI agent produces a consistent first-pass evaluation, but humans decide. This matters because vendor risk decisions require business context, contract context, and risk acceptance that should not be delegated to a model.

## Maintainability

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Keep configuration in Script Properties. | Non-developers can rotate keys without editing code if granted script admin access. | Script Properties are still visible to script editors. | Too many script editors expose secrets. | Hardcoded config, rejected. |
| Use normalized headers instead of column numbers. | Form edits are less likely to break the workflow. | Header aliases must be maintained. | Renamed questions can still fail validation. | Fixed column numbers, rejected because Forms change over time. |
| Write all major events to `Audit_Log`. | Another engineer can reconstruct workflow behavior later. | More rows and storage. | Without logs, failures become invisible. | Rely on Apps Script logs, rejected for audit convenience. |
| Keep vendor research mocked until an approved source exists. | Avoids fragile scraping and unapproved third-party calls. | Human reviewers do more verification. | Mock data may be over-trusted. | Build custom web research, rejected. |

## Security Posture

The system applies least privilege by limiting form editing, Sheet editing, script editing, Slack channel access, and API secret access. It also avoids using LLM output as a final authority. Unknown answers are treated as risk, not as approval.

The main residual risk is process drift. Sheet-based workflows are easy to start and easy to mutate. Balto should designate an owner, review the workflow quarterly, and migrate to a formal vendor management platform if request volume or audit expectations increase.

## SOC2 Evidence Value

The workflow creates evidence for:

- Who requested the tool.
- What business problem the tool solves.
- What data and integrations are involved.
- Which risks were identified.
- Which approvals were required.
- What the model was asked and how it responded.
- What Slack notification was sent.
- What final human decision was recorded.

This is stronger than ad hoc Slack approvals because it gives auditors a consistent artifact instead of a conversation archaeology project.

## What I Would Improve in Production

1. Replace mock vendor research with Vanta, Drata, procurement, or approved vendor inventory data.
2. Add signed Slack interactive approvals or move approval state to a ticketing tool.
3. Add periodic stale request reminders.
4. Add automated vendor inventory updates after approval.
5. Add a quarterly reconciliation between approved tools, Okta apps, Google OAuth grants, expense data, and access review records.
