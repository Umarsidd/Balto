# Task 1 - LLM Prompt Design

## Usage Rules

The LLM is used to produce a structured advisory evaluation. It does not approve, reject, or provision software by itself. Human reviewers remain responsible for final decisions.

Security rules:

- Do not include passwords, API keys, customer records, or production secrets.
- Include only the minimum request fields needed for vendor and risk evaluation.
- Label mock vendor research clearly.
- Store the final prompt and raw response in the restricted Sheet for auditability.
- Treat every model result as untrusted until JSON validation succeeds.

## System Prompt

```text
You are an IT, Security, Vendor Risk, and SOC2 review assistant for Balto Software, a 75-person remote SaaS company.

Your task is to evaluate a new software tool request using only the supplied request data and vendor context.

You must:
- Be conservative when data classification, authentication, AI training, or vendor assurance is unknown.
- Assume Okta RBAC is imperfect and recommend compensating controls when needed.
- Prefer least privilege, SSO, SCIM, limited OAuth scopes, named owners, and quarterly access review.
- Never claim a vendor fact unless it appears in the supplied vendor context.
- Treat MOCK vendor context as unverified.
- Return valid JSON only.

Do not approve tools. Recommend approval routing and conditions for human reviewers.
```

## User Prompt Template

```text
Evaluate this New Software Tool Evaluation request.

Company context:
- Company: Balto Software
- Size: 75 employees
- Workforce: remote
- IT staffing: one-person IT team
- Identity provider: Okta, with imperfect RBAC
- Collaboration: Google Workspace and Slack
- Compliance: SOC2

Request JSON:
{{REQUEST_JSON}}

Vendor context JSON:
{{VENDOR_CONTEXT_JSON}}

Return JSON matching this schema exactly:
{
  "risk_rating": "low | medium | high | critical",
  "recommendation": "approve_with_conditions | needs_manual_review | reject",
  "summary": "string",
  "approval_gates": [
    {
      "gate": "manager | business_owner | it | security | finance | legal | executive",
      "required": true,
      "reason": "string"
    }
  ],
  "key_risks": [
    {
      "risk": "string",
      "why_it_matters": "string",
      "severity": "low | medium | high | critical",
      "mitigation": "string"
    }
  ],
  "least_privilege_requirements": [
    "string"
  ],
  "soc2_evidence_needed": [
    "string"
  ],
  "data_use_restrictions": [
    "string"
  ],
  "open_questions": [
    "string"
  ],
  "reviewer_notes": "string"
}
```

## Expected JSON Output Example

```json
{
  "risk_rating": "high",
  "recommendation": "needs_manual_review",
  "summary": "The request involves customer data and an integration with Google Workspace. Security and Legal review are required before any pilot with real data.",
  "approval_gates": [
    {
      "gate": "manager",
      "required": true,
      "reason": "The manager must confirm the business need and team priority."
    },
    {
      "gate": "security",
      "required": true,
      "reason": "The tool may process customer data and requests OAuth access."
    },
    {
      "gate": "legal",
      "required": true,
      "reason": "A DPA is needed before personal or customer data is processed."
    }
  ],
  "key_risks": [
    {
      "risk": "Unknown SOC2 status",
      "why_it_matters": "Balto needs vendor assurance before allowing sensitive data in a third-party system.",
      "severity": "high",
      "mitigation": "Obtain SOC2 Type II or document compensating controls before production use."
    }
  ],
  "least_privilege_requirements": [
    "Use SSO if available.",
    "Limit OAuth scopes to the minimum required.",
    "Assign a named admin owner and backup owner."
  ],
  "soc2_evidence_needed": [
    "Form submission",
    "Security review notes",
    "DPA or privacy review evidence",
    "Access review owner"
  ],
  "data_use_restrictions": [
    "No customer data during trial until Security approval is complete."
  ],
  "open_questions": [
    "Does the vendor support SCIM deprovisioning?",
    "Can AI training be disabled contractually?"
  ],
  "reviewer_notes": "Treat the vendor research as unverified if the context is marked MOCK."
}
```

## JSON Validation Rules

| Field | Validation |
|---|---|
| `risk_rating` | Must be one of low, medium, high, critical. |
| `recommendation` | Must be one of approve_with_conditions, needs_manual_review, reject. |
| `approval_gates` | Must include IT for every target request. |
| `key_risks` | Must include `why_it_matters` for every risk. |
| `soc2_evidence_needed` | Must not be empty. |
| `open_questions` | Can be empty only for low-risk requests. |

## Prompt Tradeoffs

| Recommendation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Require JSON only. | Apps Script can parse and write structured fields. | The model may fail if the prompt is too complex. | Invalid JSON requires manual fallback. | Free text summary, rejected because it is harder to audit. |
| Include company context in every prompt. | The model needs to tailor recommendations to Balto's size and tooling. | More tokens per request. | Missing context produces generic advice. | Store context only in system prompt, acceptable but less explicit. |
| Instruct the model not to claim unsupplied facts. | Reduces hallucinated vendor claims. | The output may include more unknowns. | Unsupported vendor claims can mislead approvers. | Ask model to infer vendor details, rejected. |
