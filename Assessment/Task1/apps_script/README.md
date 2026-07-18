# Task 1 Apps Script Deployment

## Files

| File | Purpose |
|---|---|
| `Code.gs` | Installable trigger entry point and workflow orchestration. |
| `Config.gs` | Runtime configuration, Sheet headers, and header aliases. |
| `LLM.gs` | OpenAI or Anthropic API calls, retries, and marked MOCK fallback. |
| `VendorResearch.gs` | Configured vendor lookup and marked MOCK vendor context. |
| `Slack.gs` | Slack webhook notification with retry handling. |

## Deployment

1. Create the Google Form described in `../Intake_Form_Questions.md`.
2. Link the Form to a Google Sheet.
3. Open the Sheet, select Extensions, then Apps Script.
4. Add the `.gs` files from this folder.
5. In Apps Script, configure Script Properties.
6. Create an installable trigger:
   - Function: `onFormSubmit`
   - Event source: From spreadsheet
   - Event type: On form submit
7. Submit a test form response with `Request Type = New Software Tool Evaluation`.
8. Verify the `Evaluations` and `Audit_Log` Sheets are created.
9. Verify Slack notification behavior.

## Script Properties

| Property | Required | Example | Notes |
|---|---:|---|---|
| `LLM_PROVIDER` | No | `openai` | `openai` or `anthropic`. |
| `OPENAI_API_KEY` | Conditional | Secret | Required for OpenAI provider. |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | Keep current with approved Balto model list. |
| `ANTHROPIC_API_KEY` | Conditional | Secret | Required for Anthropic provider. |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-latest` | Use only if Anthropic is approved. |
| `SLACK_WEBHOOK_URL` | No | Secret | If missing, Slack is skipped and logged. |
| `VENDOR_RESEARCH_ENDPOINT` | No | HTTPS endpoint | Optional approved vendor lookup service. |
| `ENABLE_MOCK_VENDOR_RESEARCH` | No | `true` | Set `false` in production if mock research is unacceptable. |
| `TARGET_REQUEST_TYPE` | No | `New Software Tool Evaluation` | Must match the Form option exactly. |
| `MAX_RETRIES` | No | `3` | Used for external API calls. |
| `RETRY_BASE_MS` | No | `750` | Exponential retry base delay. |

## Security Notes

- Do not hardcode secrets in `.gs` files.
- Restrict Apps Script editor access to IT and a documented backup owner.
- Restrict the destination Sheet to least privilege reviewer groups.
- Protect the `Audit_Log` Sheet from edits.
- Treat LLM output as advisory only.
- Do not include production secrets or customer records in form free text.
- Rotate Slack webhook and API keys when ownership changes.

## Testing

Use three test submissions:

1. `Request Type = Access to Existing Tool` to verify skip logging.
2. `Request Type = New Software Tool Evaluation` with no LLM API key to verify MOCK LLM fallback.
3. `Request Type = New Software Tool Evaluation` with a configured API key to verify real model output.

Expected artifacts:

- One raw Form response row.
- One `Audit_Log` row for every major event.
- One `Evaluations` row for target requests.
- Slack status of `POSTED`, `SKIPPED_NO_WEBHOOK`, or `FAILED`.

## Future Improvements

| Improvement | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Replace webhook with Slack app approvals. | Signed interactive approvals are stronger evidence. | More setup and maintenance. | Webhook-only approvals can be ambiguous. | Continue webhook only, acceptable for notification v1. |
| Integrate Vanta or Drata vendor records. | Reduces SOC2 evidence collection work. | Adds cost and vendor dependency. | Manual evidence may become stale. | Manual uploads, acceptable short term. |
| Add stale request reminders. | Prevents requests from lingering. | More notification noise. | Requests may bypass process if approvals stall. | Manual follow-up, workable at low volume. |
