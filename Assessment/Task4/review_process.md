# Task 4 - Access Review Implementation Plan

## Implementation Steps

1. Create a quarterly Google Drive folder restricted to IT, Security, and auditors as needed.
2. Export Okta users, groups, app assignments, and admin roles.
3. Export Google Workspace users, groups, admin roles, and suspended users.
4. Export key app access for GitHub, CRM, HRIS, finance, support, and production tools.
5. Add non-SSO tools from the vendor inventory.
6. Normalize all exports into the Access Review workbook.
7. Identify privileged, admin, shared, service, and non-SSO access.
8. Send manager and tool owner review packets.
9. Track decisions and missing responses.
10. Remediate access marked for removal or modification.
11. Document exceptions with owner and expiration.
12. Export final evidence package.

## Manager Review Packet

Include:

- Direct reports.
- Systems and access names.
- Access type and data classification.
- Last login if available.
- Decision dropdown.
- Required reason for privileged access.
- Deadline.

## Remediation Rules

| Decision | Action |
|---|---|
| Approved | Record reviewer, timestamp, and reason if privileged. |
| Remove | Create ticket, remove access, attach evidence. |
| Modify | Create ticket, adjust role or group, attach evidence. |
| Needs info | Assign to IT and manager for follow-up. |
| No response | Escalate after ten business days. |

## Evidence Retention

Retain access review evidence according to Balto's SOC2 evidence retention policy. At minimum, retain final workbooks, exports, approvals, remediation tickets, and exceptions for the audit period.

## Future Automation

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Automate exports from Okta and Google. | Reduces manual effort and copy errors. | Requires API scopes and secure token handling. | Over-scoped tokens can expose identity data. | Manual exports, acceptable for v1. |
| Add Slack reminders for managers. | Improves completion rate. | Notification noise. | Reviews stall without reminders. | Manual reminders, workable at low scale. |
| Migrate to Vanta or Drata after process stabilizes. | Avoids automating a poorly understood process. | Delays GRC benefits. | Manual process may drift. | Buy GRC first, risky if ownership is unclear. |
