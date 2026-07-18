# Final Writeup

## Executive Summary

This assessment delivers a complete IT Operations and Security automation package for Balto Software. The work covers new software tool evaluation, onboarding automation, access workflow security review, quarterly access review design, and employee communications.

The recommendations are intentionally realistic for a 75-person remote SaaS company with a one-person IT function. The design uses Google Forms, Google Sheets, Apps Script, Slack, Python, and mock service clients because those are maintainable without building a large internal platform. Where the workflow touches security decisions, the design preserves human approval, least privilege, audit evidence, and SOC2 readiness.

## Time Log

| Activity | Estimated time |
|---|---:|
| Task 1 intake design, workflow, diagrams, approvals, tooling, LLM prompt, and reflection | 3.0 hours |
| Task 1 Apps Script implementation and deployment documentation | 2.0 hours |
| Task 2 onboarding architecture, role mapping, Python implementation, mocks, and README | 3.0 hours |
| Task 3 security review, code review comment, hardened workflow, and notes | 2.0 hours |
| Task 4 quarterly access review runbook and implementation plan | 1.5 hours |
| Task 5 communications | 0.5 hours |
| Final review, validation, and packaging | 1.0 hour |

## AI Usage Log

| Use | Description | Human review required |
|---|---|---:|
| Drafting | Generated structured markdown documentation for all tasks. | Yes |
| Code generation | Generated Apps Script and Python source code. | Yes |
| Security reasoning | Identified access workflow flaws and recommended controls. | Yes |
| Prompt design | Generated LLM prompts for vendor review and access review summarization. | Yes |
| Communications | Drafted Slack and company announcement copy. | Yes |

## Prompts Used

The assessment was generated from the two provided user prompts:

1. Build a full IT Operations, Security, and SOC2 assessment for Balto Software with five tasks, markdown deliverables, workflow diagrams, reasoning, tradeoffs, security, least privilege, edge cases, and final writeup.
2. Generate production-quality source code for the IT Operations assessment, including Google Apps Script for software evaluation, Python onboarding automation, a fixed security workflow, access review plan, and communications.

## What AI Generated

- Google Form intake design.
- New Software Tool Evaluation workflow documentation.
- Mermaid diagrams.
- Approval matrix and tooling table.
- Tradeoff analysis.
- LLM prompt and expected JSON schema.
- Task 1 Apps Script source code.
- Task 2 onboarding architecture and role mapping.
- Task 2 Python source code and mock clients.
- Task 3 security findings and professional code review comment.
- Task 3 hardened workflow implementation.
- Task 4 quarterly access review process.
- Task 5 Slack and company communications.
- Repository README and deployment notes.

## What Was Edited Manually

No separate human edits were applied during this generation. The content was reviewed and refined within the same Codex work session for consistency, security posture, and folder completeness.

## What Was Discarded

| Discarded idea | Reason |
|---|---|
| Custom web portal for software requests | Too much maintenance for a one-person IT team. |
| Auto-approval by LLM | Inappropriate for security and SOC2 accountability. |
| Web scraping vendor security pages | Brittle and risky without approved source controls. |
| Slack reactions as approval evidence | Too ambiguous for access control. |
| Direct CSV-to-group mapping | Creates privilege escalation risk. |
| Perfect Okta RBAC assumption | Unrealistic and unsafe for Balto's operating model. |

## Lessons Learned

1. Lightweight automation can be strong if the evidence model is deliberate.
2. The Sheet or ticket must remain the source of truth; Slack is useful for visibility but weak as the only audit record.
3. LLMs are valuable for consistency and summarization, but they should not approve access or vendors.
4. Imperfect Okta RBAC is not a blocker if compensating controls are explicit and reviewed.
5. Non-SSO tools need named owners and quarterly review from day one.

## Production Improvements

| Improvement | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Integrate Vanta or Drata for vendor and access evidence. | Reduces audit preparation work. | Adds cost and implementation. | Manual evidence can become stale. | Continue Sheets, acceptable for v1. |
| Replace Slack webhook with signed Slack app approvals. | Stronger approval evidence. | More setup and maintenance. | Webhook-only approvals can be ambiguous. | Email approvals, weaker workflow. |
| Replace mock vendor research with approved vendor inventory. | Improves review accuracy. | Requires tool or data source. | Mock context can be over-trusted. | Internet scraping, rejected. |
| Replace mock onboarding clients with scoped production APIs. | Enables real provisioning. | Requires careful API scopes and retries. | Over-scoped tokens are high risk. | Manual provisioning, short-term only. |
| Add automated access review exports. | Reduces manual work and errors. | Requires API integrations. | Manual exports can miss systems. | Keep manual, acceptable at low scale. |

## Final Assessment Status

All requested deliverables are included under `Assessment/`:

- Task 1 assessment documentation and Apps Script implementation.
- Task 2 engineering documentation and Python onboarding automation.
- Task 3 security review and fixed workflow code.
- Task 4 quarterly access review design.
- Task 5 polished communications.
- Final writeup and repository README.
