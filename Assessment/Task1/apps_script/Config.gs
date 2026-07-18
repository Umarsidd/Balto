/**
 * Configuration helpers for the software evaluation workflow.
 *
 * Secrets are intentionally read from Script Properties. Keeping API keys and
 * webhooks out of source code supports least privilege and SOC2 evidence that
 * secrets are not embedded in automation logic.
 */

function getRuntimeConfig() {
  var properties = PropertiesService.getScriptProperties();

  return {
    llmProvider: (properties.getProperty('LLM_PROVIDER') || 'openai').toLowerCase(),
    openAiApiKey: properties.getProperty('OPENAI_API_KEY') || '',
    openAiModel: properties.getProperty('OPENAI_MODEL') || 'gpt-4.1-mini',
    anthropicApiKey: properties.getProperty('ANTHROPIC_API_KEY') || '',
    anthropicModel: properties.getProperty('ANTHROPIC_MODEL') || 'claude-3-5-sonnet-latest',
    slackWebhookUrl: properties.getProperty('SLACK_WEBHOOK_URL') || '',
    vendorResearchEndpoint: properties.getProperty('VENDOR_RESEARCH_ENDPOINT') || '',
    evaluationSheetName: properties.getProperty('EVALUATION_SHEET_NAME') || 'Evaluations',
    auditSheetName: properties.getProperty('AUDIT_SHEET_NAME') || 'Audit_Log',
    targetRequestType: properties.getProperty('TARGET_REQUEST_TYPE') || 'New Software Tool Evaluation',
    maxRetries: parsePositiveInteger_(properties.getProperty('MAX_RETRIES'), 3),
    retryBaseMs: parsePositiveInteger_(properties.getProperty('RETRY_BASE_MS'), 750),
    enableMockVendorResearch: parseBoolean_(properties.getProperty('ENABLE_MOCK_VENDOR_RESEARCH'), true),
    sheetTimeZone: Session.getScriptTimeZone() || 'UTC'
  };
}

function getEvaluationHeaders() {
  return [
    'Correlation ID',
    'Form Row Number',
    'Submitted At',
    'Requester Email',
    'Tool Name',
    'Vendor Website',
    'Vendor Domain',
    'Business Owner',
    'Data Classification',
    'Estimated Annual Cost',
    'Risk Rating',
    'Recommendation',
    'Approval Gates',
    'Key Risks',
    'Compensating Controls',
    'Vendor Research JSON',
    'Prompt',
    'Model Provider',
    'Model Name',
    'Model Response JSON',
    'Raw Model Response',
    'Slack Status',
    'Workflow Status',
    'Error Message',
    'Created At',
    'Updated At'
  ];
}

function getAuditHeaders() {
  return [
    'Timestamp',
    'Correlation ID',
    'Event Type',
    'Actor',
    'Status',
    'Details JSON'
  ];
}

function getHeaderAliases() {
  return {
    requestType: ['Request Type'],
    requesterEmail: ['Email Address', 'Username', 'Requester Email'],
    requesterName: ['Requester Name', 'Name'],
    requesterDepartment: ['Requester Department', 'Department'],
    requesterManager: ['Requester Manager', 'Manager'],
    businessOwner: ['Business Owner'],
    requestedDueDate: ['Requested Due Date'],
    toolName: ['Tool Name', 'Software Tool Name', 'Vendor Name'],
    vendorWebsite: ['Vendor Website', 'Tool Website', 'Website'],
    vendorContactEmail: ['Vendor Contact Email'],
    requestedUsersOrTeams: ['Requested Users or Teams', 'Users or Teams'],
    estimatedNumberOfUsers: ['Estimated Number of Users', 'Number of Users'],
    businessProblem: ['Business Problem'],
    desiredOutcome: ['Desired Outcome'],
    alternativesConsidered: ['Alternatives Considered'],
    existingToolsConsidered: ['Existing Balto tools considered'],
    usageStage: ['Is this a trial, pilot, or production purchase?'],
    expectedAnnualCost: ['Expected Annual Cost', 'Annual Cost'],
    contractTerm: ['Contract Term'],
    dataClassification: ['Data Classification'],
    customerData: ['Will customer data be uploaded or viewed?'],
    personalData: ['Will personal data be processed?'],
    sourceCodeOrCredentials: ['Will source code, API keys, or production credentials be entered?'],
    authenticationMethod: ['Authentication method supported'],
    adminRoles: ['Does the tool support admin roles?'],
    integrations: ['Does the tool integrate with Google, Slack, Okta, GitHub, CRM, or production systems?'],
    oauthScopes: ['OAuth scopes requested'],
    vendorSecurityUrl: ['Vendor security page or trust center URL'],
    soc2Available: ['SOC2 Type II available?'],
    dpaAvailable: ['Data Processing Agreement available?'],
    retentionControls: ['Data retention controls available?'],
    aiTrainingUse: ['AI or model training use'],
    customerFacing: ['Is this tool customer-facing or used to deliver customer service?'],
    vendorSystemAccess: ['Does the vendor need access to Balto systems?'],
    contractDocuments: ['Will a contract, MSA, DPA, BAA, or order form be signed?'],
    proposedDataOwner: ['Proposed data owner'],
    proposedTechnicalOwner: ['Proposed technical owner'],
    budgetApprovalObtained: ['Budget owner approval already obtained?'],
    budgetApproverEmail: ['Budget approver email'],
    approvalEvidenceLink: ['Approval evidence link'],
    securityExceptionRequested: ['Security exception requested?'],
    exceptionJustification: ['Exception justification'],
    requestedGoLiveDate: ['Requested go-live date'],
    additionalContext: ['Additional context']
  };
}

function parsePositiveInteger_(value, fallback) {
  var parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed < 1) {
    return fallback;
  }
  return parsed;
}

function parseBoolean_(value, fallback) {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }
  return String(value).toLowerCase() === 'true';
}
