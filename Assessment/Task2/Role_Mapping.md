# Task 2 - Role Mapping

## Mapping Principles

| Principle | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|
| Start with baseline access and add role-specific groups. | Limits default exposure. | Some users need follow-up access requests. | Overbroad baseline creates invisible privilege. | Department-only access, rejected because departments contain varied roles. |
| Do not map CSV-provided group names directly. | Prevents arbitrary access assignment. | Requires maintained mappings. | CSV tampering could grant privileged access. | Trust HR export group columns, rejected. |
| Privileged roles require manager approval evidence. | Supports separation of duties and SOC2. | Slower onboarding. | Privileged access without evidence is an audit finding. | Grant first, approve later, rejected. |
| Imperfect Okta RBAC is expected. | The process documents compensating controls. | Some access remains manual. | False confidence in automation can create orphaned access. | Wait for perfect RBAC, rejected. |

## Baseline Groups

| Group | Applies to | Purpose | Notes |
|---|---|---|---|
| `okta-group-all-employees` | All employees | SSO portal baseline and security training. | Must not grant sensitive app access. |
| `google-group-all` | All employees | Company announcements. | Posting restricted to approved senders. |
| `google-group-security-training` | All employees | Security awareness and policy acknowledgements. | Evidence can support SOC2 training control. |

## Role to Okta Mapping

| Role pattern | Department | Okta groups | Privileged | Manager approval required | Reason |
|---|---|---|---:|---:|---|
| Software Engineer | Engineering | `okta-group-engineering-baseline`, `okta-group-github-standard`, `okta-group-dev-tools` | Yes | Yes | Engineering can access code and development systems. |
| Senior Software Engineer | Engineering | `okta-group-engineering-baseline`, `okta-group-github-standard`, `okta-group-dev-tools` | Yes | Yes | Seniority does not automatically grant admin. |
| Engineering Manager | Engineering | `okta-group-engineering-baseline`, `okta-group-github-standard`, `okta-group-eng-manager` | Yes | Yes | Manager access includes team systems but not production admin by default. |
| Sales Development Representative | Sales | `okta-group-sales-baseline`, `okta-group-crm-standard` | No | No | CRM access is needed, admin access is not. |
| Account Executive | Sales | `okta-group-sales-baseline`, `okta-group-crm-standard`, `okta-group-contract-viewer` | No | No | Contract viewing is business justified. |
| Customer Success Manager | Customer Success | `okta-group-cs-baseline`, `okta-group-support-standard` | No | No | Customer workflows need support tools with standard permissions. |
| Finance Analyst | Finance | `okta-group-finance-baseline`, `okta-group-expense-standard` | Yes | Yes | Finance systems contain sensitive business and employee data. |
| People Operations | People | `okta-group-people-baseline`, `okta-group-hris-standard` | Yes | Yes | HR systems contain personal data. |
| IT Operations | IT | `okta-group-it-baseline` | Yes | Yes | IT admin access must be explicitly approved outside automation. |
| Unknown role | Any | `okta-group-all-employees` only | Conditional | Yes | Unknown roles should not receive elevated access. |

## Department to Google Workspace Groups

| Department | Groups | Reason |
|---|---|---|
| Engineering | `engineering@balto.com`, `product-engineering@balto.com` | Team communication and engineering calendar access. |
| Sales | `sales@balto.com`, `revenue@balto.com` | Revenue communications and enablement. |
| Customer Success | `customer-success@balto.com`, `customers@balto.com` | Customer operations communication. |
| Finance | `finance@balto.com`, `g-and-a@balto.com` | Finance and admin communications. |
| People | `people@balto.com`, `g-and-a@balto.com` | HR communications. |
| IT | `it@balto.com`, `security-alerts@balto.com` | Operational and security notices. |
| Unknown | `all@balto.com` only | Avoids accidental department access. |

## Department to Iru Blueprint

| Department | Blueprint | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Engineering | `iru-blueprint-engineering` | Developer tools and endpoint posture. | Larger software footprint. | More local attack surface. | Baseline only, rejected for slow ramp. |
| Sales | `iru-blueprint-sales` | CRM, calling, and presentation tools. | Needs regular updates. | Missing revenue tools. | Manual installs, rejected. |
| Customer Success | `iru-blueprint-customer-success` | Support and customer collaboration tools. | Some overlap with Sales. | Overbroad access if reused blindly. | Sales blueprint, rejected. |
| Finance | `iru-blueprint-finance` | Finance workstation controls and tools. | More restrictive. | User friction. | General admin blueprint, rejected for sensitive data. |
| People | `iru-blueprint-people` | HR tools and privacy posture. | More maintenance. | HR data exposure. | General admin blueprint, rejected. |
| IT | `iru-blueprint-it` | Admin utilities with strict controls. | Requires strong approval. | IT endpoint compromise is high impact. | Engineering blueprint, rejected. |
| Unknown | `iru-blueprint-baseline` | Safe default. | More manual follow-up. | New hire may lack tools on day one. | Guess based on title, rejected. |

## Country Policies

| Country | Status | Notes |
|---|---|---|
| United States | Supported | Standard onboarding. |
| Canada | Supported | Standard onboarding with local payroll checks. |
| United Kingdom | Supported | Standard onboarding with privacy awareness. |
| Ireland | Supported | EU privacy considerations. |
| Germany | Supported | EU privacy considerations. |
| Netherlands | Supported | EU privacy considerations. |
| India | Supported | Device logistics and regional policy acknowledgement. |
| Australia | Supported | Device logistics and regional policy acknowledgement. |
| Other | Requires review | HR, Legal, Finance, and IT must confirm employment and device support. |

## Manager Approval Rules

| Condition | Required action |
|---|---|
| Role is privileged | Manager approval ticket required before privileged groups are assigned. |
| Role cannot be mapped | Assign baseline only and require manager clarification. |
| Manager email missing | Skip row until HR fixes data. |
| Manager email equals new hire email | Skip row due to invalid approval chain. |
| Department is Finance, People, IT, or Engineering | Require stronger review for privileged apps. |

## Quarterly Review Tie-In

Every group assigned by this mapping should appear in the quarterly access review inventory. Groups marked privileged require manager attestation and IT review. Non-SSO tools created outside Okta must be manually added to the review workbook.
