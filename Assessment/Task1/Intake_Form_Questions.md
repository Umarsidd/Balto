# Task 1 - Google Form Intake Design

## Purpose

This Google Form is the controlled intake path for software, SaaS, browser extension, AI tool, and integration requests at Balto Software. The design assumes a 75-person remote SaaS company, a one-person IT team, imperfect Okta role based access control, and a SOC2 audit expectation that every tool decision can be reconstructed later.

The form should be owned by IT, stored in a restricted Google Drive folder, and configured to write to a dedicated Google Sheet. Only IT, Security, Finance, and the automation service account should have editor access to the destination Sheet.

## Form Settings

| Setting | Value | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Collect email addresses | Enabled | Creates requester identity evidence without relying on free text. | Contractors without Balto accounts cannot submit directly. | If disabled, approval and audit trails are weaker. | Allow public submissions, rejected because vendor access requests should originate from an accountable employee. |
| Limit to Balto domain | Enabled | Reduces spam and unauthorized external requests. | External vendors must route through a sponsor. | Misconfigured domain settings could block newly acquired domains. | Public form plus CAPTCHA, rejected for unnecessary exposure. |
| Allow response edits | Disabled after submission | Prevents silent post-approval changes. | Requesters must submit corrections as comments or a new request. | Editable responses can undermine SOC2 evidence integrity. | Allow edits and diff them with Apps Script, rejected as higher maintenance. |
| Send respondent copy | Enabled | Gives requester a timestamped receipt. | Slightly more email noise. | If disabled, requesters may bypass the workflow by asking in Slack. | Manual acknowledgement, rejected because it does not scale for one IT owner. |
| Required sign-in | Enabled | Supports least privilege and accountability. | Requires valid Google session. | Shared accounts would weaken attribution; shared accounts should be prohibited by policy. | Anonymous intake, rejected. |

## Branching Overview

The first required question is `Request Type`. Branching keeps the New Software Tool Evaluation path focused while allowing the same form to support related requests later.

| Request type | Branch destination | Automation behavior |
|---|---|---|
| New Software Tool Evaluation | Full vendor evaluation workflow | Runs AI evaluation, writes evaluation record, posts Slack approval summary. |
| Access to Existing Tool | Existing access request section | Does not run Task 1 vendor agent; routes to access workflow. |
| Tool Renewal or Contract Change | Renewal section | Does not run Task 1 vendor agent; routes to Finance and Security review. |
| Browser Extension Request | Browser extension section | Can reuse vendor evaluation fields with extra browser risk questions. |
| Unsure | Triage section | Posts lightweight triage notification only. |

## Section 1 - Requester and Request Type

| Question | Type | Required | Validation | Branching | Compliance or security purpose |
|---|---|---:|---|---|---|
| Request Type | Multiple choice | Yes | Must select one defined option | Branch by response | Separates new vendor review from access and renewal workflows. |
| Requester Name | Short answer | Yes | 2 to 80 characters | None | Human readable audit trail. |
| Requester Department | Dropdown | Yes | Controlled values from HR departments | None | Supports routing and future trend analysis. |
| Requester Manager | Short answer | Yes | Must be a Balto email address | None | Enables approval validation even when Okta RBAC is imperfect. |
| Business Owner | Short answer | Yes | Must be a Balto email address | None | Identifies who owns the tool after approval. |
| Requested Due Date | Date | No | Must be today or later | None | Helps prioritize without treating urgency as approval. |
| Is this replacing an existing tool? | Multiple choice | Yes | Yes, No, Unsure | If Yes, show replacement details | Prevents duplicate tooling and shadow IT. |
| Existing tool being replaced | Short answer | Conditional | Required only if replacement is Yes | None | Supports deprovisioning and spend rationalization. |

## Section 2 - New Software Tool Evaluation

This section is required only when `Request Type = New Software Tool Evaluation`.

| Question | Type | Required | Validation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---:|---|---|---|---|---|
| Tool Name | Short answer | Yes | 2 to 100 characters | Primary identifier for vendor research and approval records. | Similar products may have ambiguous names. | Wrong vendor could be evaluated. | Ask only for URL, rejected because names are needed in Slack summaries. |
| Vendor Website | URL | Yes | Must be valid HTTPS URL | Helps verify vendor identity and security pages. | Some early vendors have poor websites. | Typos can cause incorrect evaluation. | Free text website, rejected due to parsing errors. |
| Vendor Contact Email | Short answer | No | Email format if provided | Gives Procurement a handoff path. | Not always known early. | Sales contacts may not know security details. | Require vendor contact, rejected because it blocks early evaluation. |
| Requested Users or Teams | Paragraph | Yes | 10 to 1000 characters | Defines scope and blast radius. | Free text requires review. | Ambiguous scope can lead to over-provisioning. | User picker, rejected because Forms cannot reliably query all groups without custom UI. |
| Estimated Number of Users | Number | Yes | Integer 1 to 500 | Drives licensing, access review, and risk. | Early estimates can be inaccurate. | Underestimated user count can bypass approval gates. | Optional estimate, rejected because cost and scope need evidence. |
| Business Problem | Paragraph | Yes | 30 to 2000 characters | Forces a legitimate business justification. | Takes requester time. | Weak justification increases tool sprawl. | Short answer, rejected because context is too thin for approval. |
| Desired Outcome | Paragraph | Yes | 20 to 1500 characters | Enables evaluation against success criteria. | Some users may write vague answers. | Lack of outcome makes renewals hard to justify. | No outcome question, rejected for weak spend governance. |
| Alternatives Considered | Paragraph | Yes | 10 to 1500 characters | Shows whether existing tools could satisfy the need. | Requesters may not know all tools. | Duplicative SaaS increases cost and data exposure. | IT-only alternative research, rejected because requester context matters. |
| Existing Balto tools considered | Checkbox | Yes | Select one or more, includes Not sure | Encourages reuse of current stack. | List must be maintained. | Stale list can mislead requesters. | Open ended text, rejected because structured evidence is better. |
| Is this a trial, pilot, or production purchase? | Multiple choice | Yes | Trial, Pilot, Production, Unsure | Sets approval threshold and data limits. | Some requests evolve. | Production use may start as a trial without controls. | Treat all requests the same, rejected because it slows low-risk trials. |
| Expected Annual Cost | Number | Yes | USD 0 to 250000 | Drives Finance approval and budget evidence. | Estimates may be rough. | Hidden cost can bypass procurement. | Ask only for monthly cost, rejected because annual spend is clearer. |
| Contract Term | Dropdown | Yes | Trial only, Monthly, Annual, Multi-year, Unknown | Flags long-term commitments. | Unknown may need follow-up. | Multi-year contracts can create lock-in. | Leave to Procurement, rejected because early routing needs term. |

## Section 3 - Data and Security

| Question | Type | Required | Validation | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---:|---|---|---|---|---|
| Data Classification | Checkbox | Yes | At least one | Determines security review depth. | Requester may misclassify data. | Under-classification can expose sensitive data. | IT classifies alone, rejected because requester knows intended use. |
| Will customer data be uploaded or viewed? | Multiple choice | Yes | Yes, No, Unsure | SOC2 relevant customer data handling evidence. | Unsure creates extra review. | Customer data in unreviewed tools can violate commitments. | Only ask broad data category, rejected because customer data needs explicit gate. |
| Will personal data be processed? | Multiple choice | Yes | Yes, No, Unsure | Privacy and regional compliance screening. | Adds complexity. | Personal data in vendor systems needs DPA and retention checks. | Defer to Legal, rejected because intake should route early. |
| Will source code, API keys, or production credentials be entered? | Multiple choice | Yes | Yes, No, Unsure | Flags high-risk secrets and IP exposure. | May alarm requesters. | Secrets in SaaS tools can cause incident response events. | Ask only about confidential data, rejected as too vague. |
| Authentication method supported | Checkbox | Yes | SSO, SCIM, SAML, OIDC, Password, Magic link, Unknown | Drives identity and deprovisioning controls. | Requester may not know. | Password-only tools have higher offboarding risk. | Vendor research only, rejected because early answer helps triage. |
| Does the tool support admin roles? | Multiple choice | Yes | Yes, No, Unknown | Supports least privilege design. | Not always known. | Flat admin models create excessive access. | Ask during implementation only, rejected because approval should know risk. |
| Does the tool integrate with Google, Slack, Okta, GitHub, CRM, or production systems? | Checkbox | Yes | At least one, includes None and Unknown | Identifies third-party access paths. | Requires follow-up for details. | OAuth grants can bypass Okta and expose data. | Ask for integrations later, rejected because integrations can change approval path. |
| OAuth scopes requested | Paragraph | Conditional | Required if Google, Slack, GitHub, or CRM selected | Captures least privilege review evidence. | Requester may need vendor help. | Broad scopes create excessive exposure. | IT research only, rejected because vendor docs vary. |
| Vendor security page or trust center URL | URL | No | HTTPS URL if provided | Speeds security review. | Not all vendors publish this. | Fake or stale trust pages can mislead. | Required trust center, rejected because smaller vendors may lack one. |
| SOC2 Type II available? | Multiple choice | Yes | Yes, No, Under NDA, Unknown | Central vendor assurance evidence. | Type II is not always necessary for low-risk tools. | Missing SOC2 may require compensating controls. | Ignore SOC2 for small vendors, rejected because customer data may be involved. |
| Data Processing Agreement available? | Multiple choice | Yes | Yes, No, Under NDA, Unknown | Privacy and contractual evidence. | Legal may need follow-up. | Personal data without DPA increases compliance risk. | Ask Legal later, rejected because routing needs early signal. |
| Data retention controls available? | Multiple choice | Yes | Yes, No, Unknown | Supports offboarding and deletion obligations. | Requester often does not know. | Data can persist after account closure. | Skip for trials, rejected because trials often become production. |
| AI or model training use | Multiple choice | Yes | No training, Training opt-out, Training by default, Unknown | Critical for confidential and customer data. | Vendor claims can be nuanced. | Data used for training may violate customer or security commitments. | Only ask if tool is AI, rejected because non-AI vendors can still use subprocessors. |

## Section 4 - Compliance and Vendor Management

| Question | Type | Required | Validation | Compliance purpose |
|---|---|---:|---|---|
| Is this tool customer-facing or used to deliver customer service? | Multiple choice | Yes | Yes, No, Unsure | Flags SOC2 system boundary impact. |
| Does the vendor need access to Balto systems? | Multiple choice | Yes | Yes, No, Unsure | Drives third-party access controls. |
| Will a contract, MSA, DPA, BAA, or order form be signed? | Checkbox | Yes | At least one option, includes None and Unknown | Captures procurement and legal evidence. |
| Is a security questionnaire required from customers or prospects for this tool? | Multiple choice | Yes | Yes, No, Unsure | Flags downstream sales assurance impact. |
| Is implementation reversible within 30 days? | Multiple choice | Yes | Yes, No, Unsure | Supports exit planning and business continuity. |
| Proposed data owner | Short answer | Yes | Balto email address | Assigns ongoing accountability for access reviews. |
| Proposed technical owner | Short answer | Yes | Balto email address | Assigns operational accountability for integrations and deprovisioning. |

## Section 5 - Approval Routing Inputs

| Question | Type | Required | Validation | Branching |
|---|---|---:|---|---|
| Budget owner approval already obtained? | Multiple choice | Yes | Yes, No, Not needed, Unsure | If Yes, ask approver and evidence. |
| Budget approver email | Short answer | Conditional | Balto email required if approval obtained | None |
| Approval evidence link | URL | Conditional | Google Drive, Slack, or ticket URL | None |
| Security exception requested? | Multiple choice | Yes | Yes, No | If Yes, show exception section. |
| Exception justification | Paragraph | Conditional | 30 to 2000 characters | None |
| Requested go-live date | Date | No | Today or later | None |

## Section 6 - Final Attestation

| Question | Type | Required | Validation | Reason |
|---|---|---:|---|---|
| I confirm this request is accurate to the best of my knowledge. | Checkbox | Yes | Must be checked | Creates requester attestation evidence. |
| I understand approval is required before uploading Balto customer data. | Checkbox | Yes | Must be checked | Prevents informal trials with regulated data. |
| Additional context | Paragraph | No | Max 3000 characters | Gives nuance without making unstructured text the main evidence. |

## Branching Logic

| Condition | Destination | Automation status |
|---|---|---|
| Request Type is New Software Tool Evaluation | Section 2 | Run AI vendor evaluation. |
| Data Classification includes Customer Data, Personal Data, Source Code, Credentials, or Production Data | Security deep review | Require Security approval before pilot. |
| Expected Annual Cost greater than or equal to 5000 | Finance approval | Require budget owner and Finance approval. |
| Expected Annual Cost greater than or equal to 25000 or Contract Term is Multi-year | Executive approval | Require CFO or COO approval. |
| Authentication is Password or Magic link only | Identity exception | Require IT exception and documented deprovisioning owner. |
| AI training is Training by default or Unknown and sensitive data selected | AI risk review | Require Security and Legal review before use. |
| OAuth scopes include admin, write, delete, full access, or all repositories | Integration security review | Require technical owner and Security approval. |

## Validation Rules

| Field | Validation |
|---|---|
| Balto email fields | Must match `^[A-Za-z0-9._%+-]+@balto\\.com$` or approved subsidiary domains. |
| URLs | Must use HTTPS except internal ticket links with approved domains. |
| Annual cost | Number, minimum 0, maximum 250000. |
| User count | Integer, minimum 1, maximum 500. |
| Paragraph justifications | Minimum length enforced to prevent empty approvals. |
| Conditional approvals | If approval evidence is claimed, approver email and evidence link are required. |

## Edge Cases Before Implementation

| Edge case | Handling | Reason | Tradeoff | Risk | Alternative considered |
|---|---|---|---|---|---|
| Requester submits the same tool twice | Apps Script computes a dedupe key from requester, vendor domain, and timestamp window, then flags possible duplicate. | Prevents duplicate approval threads. | False positives require manual review. | Duplicate records may confuse auditors. | Hard block duplicates, rejected because multiple teams may evaluate same vendor differently. |
| Vendor has no SOC2 | Route to compensating control review. | Small vendors may still be acceptable for low-risk use. | More manual judgment. | Unreviewed vendor controls could be weak. | Blanket rejection, rejected because it blocks useful low-risk tools. |
| Tool starts as a free trial | Allow only non-sensitive data until approval. | Balances speed and control. | Requires requester discipline. | Trial may quietly become production use. | Ban trials, rejected as too slow for a small SaaS company. |
| Requester marks all data as Not sure | Treat as medium risk and require IT follow-up. | Avoids unsafe default approval. | Adds queue load. | Inaccurate risk classification. | Reject automatically, rejected because education is better for small teams. |
| Okta cannot enforce perfect app access | Require named owner and quarterly review. | Imperfect RBAC is realistic. | More evidence collection. | Orphaned users can persist in non-SSO tools. | Wait for perfect RBAC, rejected as unrealistic. |
| Slack webhook fails | Write Sheet status as `SLACK_POST_FAILED` and continue audit logging. | Approval evidence should not disappear because Slack is down. | IT must monitor failure column. | Request may be delayed. | Fail entire workflow, rejected because the Sheet remains source of truth. |

## Question Justification Summary

| Question category | Why it exists | SOC2 evidence created |
|---|---|---|
| Requester identity | Proves who initiated the change. | Access/change request evidence, timestamp, accountable owner. |
| Business justification | Shows approval was based on a documented business need. | Vendor approval rationale and renewal justification. |
| Data classification | Determines risk and review depth. | Security review input and control scoping. |
| Authentication and integration | Identifies access control and deprovisioning requirements. | Least privilege and third-party access evidence. |
| Cost and contract | Routes budget approval. | Procurement approval and spend governance evidence. |
| Owner fields | Assigns ongoing accountability. | Access review owner and vendor inventory owner. |
| Attestation | Makes requester obligations explicit. | Policy acknowledgement evidence. |
