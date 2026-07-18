# Task 2 Onboarding Automation

## Purpose

This folder contains the engineering documentation and Python implementation for a CSV-driven onboarding workflow. The code uses mock clients so it can be reviewed and tested locally without production Okta, Google, Iru, Slack, or OpenAI credentials.

## Folder Contents

| File | Purpose |
|---|---|
| `Architecture.md` | Engineering design and operational strategy. |
| `Role_Mapping.md` | Access mapping, country policy, and approval logic. |
| `onboarding.py` | CLI orchestration and structured report generation. |
| `config.py` | Environment and `.env` configuration. |
| `role_mapping.py` | Role, department, country, and blueprint mappings. |
| `validators.py` | Messy CSV parsing and validation. |
| `mock_okta.py` | Mock Okta user and group assignment. |
| `mock_google.py` | Mock Google Workspace user, license, and group assignment. |
| `mock_iru.py` | Mock Iru endpoint blueprint assignment. |
| `mock_slack.py` | Mock Slack posting and optional OpenAI welcome generation. |
| `sample_new_hires.csv` | Sample messy input data. |

## Setup in VS Code

```powershell
cd Assessment\Task2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python onboarding.py --csv sample_new_hires.csv --dry-run
```

## Environment Variables

Create a `.env` file in this folder if needed.

```env
DRY_RUN=true
LOG_LEVEL=INFO
BALTO_EMAIL_DOMAIN=balto.com
ALLOWED_COUNTRIES=United States,Canada,United Kingdom,Ireland,Germany,Netherlands,India,Australia
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OKTA_ORG_URL=
OKTA_API_TOKEN=
GOOGLE_CUSTOMER_ID=
GOOGLE_ADMIN_SUBJECT=
IRU_API_URL=
IRU_API_TOKEN=
SLACK_WEBHOOK_URL=
```

## Testing

Run the CLI against `sample_new_hires.csv`. Expected behavior:

- Avery is processed because Engineering has manager approval evidence.
- Mina is processed because Sales is not privileged in this mapping.
- Jordan is rejected during validation because the work email is not in the Balto domain.
- Casey is rejected because Spain is not in the supported country allowlist.
- Taylor is rejected because of duplicate work email and invalid start date.

## Security Notes

- The code never maps CSV group names directly to Okta or Google groups.
- Privileged or unknown roles require manager approval evidence before provisioning.
- Mocks are idempotent so repeated runs do not create duplicate users.
- Slack welcome generation sends only name, department, and role to OpenAI.
- Secrets are read from `.env` or environment variables and are never hardcoded.

## Future Improvements

| Improvement | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Add unit tests for validation and mappings. | Prevents access regressions. | More maintenance. | Mapping bugs can over-provision users. | Manual review only, rejected for production. |
| Replace mocks with official APIs. | Required for production provisioning. | API scopes and retries need careful design. | Over-scoped service tokens can violate least privilege. | Manual provisioning, acceptable during rollout only. |
| Add ticket integration for blocked rows. | HR and managers can resolve issues in a tracked queue. | Adds dependency. | Blocked rows may be missed. | Slack DM follow-up, weaker evidence. |
| Add pre-provisioning approval report. | Lets IT review access before execution. | Adds a step. | Bad mappings could provision access automatically. | Direct execution only, risky. |
