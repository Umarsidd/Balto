# Task 1 - Approval Matrix

## Approval Principles

| Principle | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Approval depends on risk, not requester seniority. | Senior requesters can still introduce high-risk tools. | Executives may expect faster approval. | Bypassing controls for leadership weakens SOC2 evidence. | Executive-only fast lane, rejected. |
| The Sheet is the source of truth. | It preserves structured evidence and timestamps. | Reviewers must open the record for full context. | Slack-only approvals are difficult to audit. | Slack reactions as approvals, rejected. |
| Trials can be approved with data limits. | Enables business speed while reducing exposure. | Requires clear restrictions and follow-up. | Users may forget trial constraints. | Ban all trials, rejected as impractical. |
| No one self-approves their own request. | Preserves separation of duties. | Slower for small teams. | Self-approval undermines audit credibility. | Self-approval under cost threshold, rejected. |

## Standard Approval Matrix

| Scenario | Manager | Business Owner | IT | Security | Finance | Legal | Executive |
|---|---:|---:|---:|---:|---:|---:|---:|
| Free or low-cost tool, no sensitive data, no integration | Required | Required | Required | Not required | Not required | Not required | Not required |
| Trial with only public or test data | Required | Required | Required | Conditional | Not required | Not required | Not required |
| Customer data, personal data, source code, credentials, or production data | Required | Required | Required | Required | Conditional | Conditional | Conditional |
| Annual cost >= 5000 USD | Required | Required | Required | Conditional | Required | Conditional | Not required |
| Annual cost >= 25000 USD | Required | Required | Required | Conditional | Required | Conditional | Required |
| Multi-year contract | Required | Required | Required | Conditional | Required | Required | Required |
| Password-only authentication | Required | Required | Required | Required | Conditional | Not required | Conditional |
| Broad OAuth scopes or production integration | Required | Required | Required | Required | Conditional | Conditional | Conditional |
| AI tool with confidential or customer data | Required | Required | Required | Required | Conditional | Required | Conditional |
| Vendor lacks SOC2 and handles sensitive data | Required | Required | Required | Required | Conditional | Required | Conditional |

## Approval Gate Detail

| Gate | Approver | What they approve | Required evidence | Failure handling |
|---|---|---|---|---|
| Manager | Requester's manager | Business priority and team need | Comment, ticket, or Sheet approval cell | Request returns to requester. |
| Business Owner | Named owner | Ownership, acceptable operational impact | Owner acceptance and renewal responsibility | Cannot proceed without named owner. |
| IT | IT owner | Identity, provisioning, deprovisioning, supportability | Access plan, admin model, owner list | Tool may be approved only with manual control notes. |
| Security | Security owner | Data risk, vendor posture, integration risk | Security review notes and conditions | Tool blocked or approved with compensating controls. |
| Finance | Budget owner or Finance | Spend and budget alignment | Budget approval link | Request paused until budget approved. |
| Legal | Legal or delegated reviewer | Contract, privacy, DPA, terms | Contract review evidence | No production use until legal approval. |
| Executive | CFO, COO, or delegated executive | Material spend or strategic risk | Executive approval record | Request deferred or rejected. |

## Risk Based Routing

| Risk rating | Definition | Minimum approval path | Typical conditions |
|---|---|---|---|
| Low | Public or internal non-sensitive data, no integration, low cost | Manager, Business Owner, IT | Pilot with sample data only. |
| Medium | Business confidential data, limited integration, moderate cost | Manager, Business Owner, IT, conditional Security or Finance | SSO preferred, manual access review required if no SCIM. |
| High | Customer, personal, source code, credentials, production systems, broad OAuth, or AI training ambiguity | Manager, Business Owner, IT, Security, Legal as needed | No sensitive data until contract and security evidence are accepted. |
| Critical | Production credentials, privileged integration, no vendor assurance, high spend, or multi-year lock-in | All applicable gates including Executive | Usually reject or require compensating controls before pilot. |

## Escalation Rules

| Trigger | Escalation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Requester asks to upload customer data before approval | Escalate to Security and manager. | Customer data use changes risk immediately. | Slows urgent testing. | Unauthorized data exposure. | Allow test use after submission, rejected. |
| Vendor refuses DPA for personal data | Escalate to Legal and block production. | Personal data needs contractual terms. | May block a preferred vendor. | Privacy and contractual non-compliance. | Accept clickwrap terms, rejected for sensitive use. |
| No SSO for a production tool | Require identity exception and quarterly manual review. | Imperfect RBAC needs compensating controls. | Adds manual work. | Orphaned accounts after offboarding. | Ban all non-SSO tools, rejected as unrealistic for a small company. |
| Finance approval missing over threshold | Pause request. | Budget owner must approve spend. | Business owner may need to wait. | Unauthorized spend. | Reimburse later, rejected. |
| Security reviewer is the requester | Assign alternate reviewer or executive delegate. | Prevents self-review. | Harder in small teams. | Conflict of interest. | Permit with documentation, rejected unless emergency exception. |

## Approval Evidence Requirements

| Evidence type | Acceptable source | Retention |
|---|---|---|
| Manager approval | Sheet approval field, ticket comment, or linked Slack thread captured in Sheet | Retain for SOC2 audit period. |
| Security review | Sheet notes, attached questionnaire, vendor SOC2, DPA notes | Retain with vendor record. |
| Finance approval | Budget approval ticket, procurement approval, or Finance comment | Retain with vendor record. |
| Legal approval | Contract review ticket or legal approval note | Retain with contract folder. |
| Exception approval | Exception register link and expiration date | Review quarterly. |

## Emergency Exception

Emergency approval should be rare and time-boxed.

Minimum requirements:

- Written business emergency reason.
- Manager and IT approval before use.
- Security approval before any sensitive data is uploaded.
- Expiration date no longer than 14 days.
- Follow-up review scheduled before expiration.
- Explicit rollback or deprovisioning plan.

Emergency access without follow-up becomes a SOC2 finding risk because it proves the process can be bypassed without closure.
