# Balto IT Operations Assessment

## Overview

This repository contains a complete IT Operations, Security, and SOC2-oriented assessment for Balto Software. It includes documentation, Google Apps Script automation, Python onboarding automation, a security workflow rewrite, an access review process, and communications.

The design assumes:

- 75-person remote SaaS company.
- One-person IT team.
- Google Workspace, Okta, Slack, and Iru.
- Imperfect Okta RBAC.
- SOC2 evidence expectations.
- Secrets stored in `.env` or platform secret stores.

## Folder Structure

```text
Assessment/
  Task1/
    Intake_Form_Questions.md
    Workflow_Document.md
    Workflow_Diagrams.md
    Approval_Matrix.md
    Tooling_Table.md
    Tradeoffs.md
    LLM_Prompt.md
    Reflection.md
    apps_script/
      Code.gs
      Config.gs
      Slack.gs
      LLM.gs
      VendorResearch.gs
      README.md
  Task2/
    Architecture.md
    Role_Mapping.md
    onboarding.py
    config.py
    role_mapping.py
    validators.py
    mock_okta.py
    mock_google.py
    mock_iru.py
    mock_slack.py
    requirements.txt
    sample_new_hires.csv
    README.md
  Task3/
    Security_Findings.md
    CodeReview.md
    fixed_workflow.py
    security_notes.md
  Task4/
    AccessReview.md
    review_process.md
  Task5/
    Communication.md
    responses.md
  Final_Writeup.md
  README.md
```

## Deployment Summary

### Task 1

Use the Google Form design in `Task1/Intake_Form_Questions.md`, then deploy the Apps Script files from `Task1/apps_script/` into the linked response Sheet. Configure Script Properties for LLM and Slack settings. Full deployment instructions are in `Task1/apps_script/README.md`.

### Task 2

Run the onboarding automation locally:

```powershell
cd Assessment\Task2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python onboarding.py --csv sample_new_hires.csv --dry-run
```

### Task 3

Review `Task3/Security_Findings.md` and `Task3/CodeReview.md`, then use `Task3/fixed_workflow.py` as the hardened reference implementation.

### Task 4

Use `Task4/AccessReview.md` as the quarterly access review runbook and `Task4/review_process.md` as the implementation checklist.

### Task 5

Use `Task5/Communication.md` or `Task5/responses.md` for Slack and company announcement copy.

## Configuration and Secrets

Never hardcode secrets.

Task 1 secrets belong in Apps Script Properties:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SLACK_WEBHOOK_URL`
- `VENDOR_RESEARCH_ENDPOINT`

Task 2 secrets belong in `.env`:

- `OPENAI_API_KEY`
- `OKTA_API_TOKEN`
- `GOOGLE_CUSTOMER_ID`
- `IRU_API_TOKEN`
- `SLACK_WEBHOOK_URL`

Task 3 production secrets should come from environment variables or a secret manager:

- `SLACK_SIGNING_SECRET`
- scoped group provisioning API token

## Testing

Recommended local checks:

```powershell
python -m py_compile Assessment\Task2\*.py Assessment\Task3\fixed_workflow.py
cd Assessment\Task2
python onboarding.py --csv sample_new_hires.csv --dry-run
```

## Security Notes

- LLM output is advisory and must not approve tools or access.
- Slack posts are notifications unless signed interactive approvals are implemented.
- CSV data must not map directly to group names.
- Non-SSO tools require named owners and quarterly review.
- Privileged access requires manager approval evidence.
- Audit logs should be immutable in production.

## Future Improvements

| Improvement | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Vanta or Drata integration | Automates SOC2 evidence and access reviews. | Cost and setup. | Manual evidence drift. | Continue manual Sheets for v1. |
| Slack app approvals | Signed, structured approvals. | More operational work. | Webhook and reaction ambiguity. | Email approvals, weaker. |
| Production API clients | Real onboarding and access automation. | Requires scoped credentials and tests. | Over-scoped tokens. | Manual provisioning, temporary only. |
| Unit test suite | Protects mappings and security controls. | Maintenance overhead. | Access regressions. | Manual testing, rejected for production. |
