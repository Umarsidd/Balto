/**
 * Entry point for the installable Google Sheets "On form submit" trigger.
 */
function onFormSubmit(event) {
  handleFormSubmit(event);
}

function handleFormSubmit(event) {
  var config = getRuntimeConfig();
  var lock = LockService.getDocumentLock();
  var correlationId = createCorrelationId_();
  var actor = 'apps-script-automation';
  var evaluationRowNumber = null;

  lock.waitLock(30000);

  try {
    ensureWorkflowSheets_(config);

    var request = extractRequestFromEvent_(event);
    actor = request.requesterEmail || actor;
    appendAuditLog(config, correlationId, 'TRIGGER_RECEIVED', actor, 'SUCCESS', {
      formRowNumber: request.formRowNumber,
      requestType: request.requestType
    });

    if (request.requestType !== config.targetRequestType) {
      appendAuditLog(config, correlationId, 'REQUEST_SKIPPED', actor, 'SUCCESS', {
        reason: 'Non-target request type',
        requestType: request.requestType
      });
      return;
    }

    validateTargetRequest_(request);

    var vendorContext = researchVendor(request, config);
    appendAuditLog(config, correlationId, 'VENDOR_RESEARCH_COMPLETED', actor, 'SUCCESS', {
      source: vendorContext.source,
      verified: vendorContext.verified
    });

    var prompt = buildEvaluationPrompt_(request, vendorContext);
    var llmResult = callLlmWithRetry(prompt, config);
    var evaluation = parseAndValidateEvaluation_(llmResult.text);

    evaluationRowNumber = writeEvaluationRecord_(config, correlationId, request, vendorContext, prompt, llmResult, evaluation, {
      slackStatus: 'PENDING',
      workflowStatus: llmResult.mock ? 'NEEDS_MANUAL_REVIEW' : 'COMPLETED',
      errorMessage: llmResult.mock ? 'MOCK LLM response used because API was unavailable or not configured.' : ''
    });

    appendAuditLog(config, correlationId, 'LLM_EVALUATION_COMPLETED', actor, 'SUCCESS', {
      modelProvider: llmResult.provider,
      modelName: llmResult.model,
      mock: llmResult.mock
    });

    var rowLink = getSheetRowLink_(config.evaluationSheetName, evaluationRowNumber);
    var slackResult = postSlackEvaluation({
      correlationId: correlationId,
      request: request,
      evaluation: evaluation,
      rowLink: rowLink
    }, config);

    updateEvaluationStatus_(config, evaluationRowNumber, {
      slackStatus: slackResult.status,
      workflowStatus: llmResult.mock ? 'NEEDS_MANUAL_REVIEW' : 'COMPLETED',
      errorMessage: slackResult.error || ''
    });

    appendAuditLog(config, correlationId, 'WORKFLOW_COMPLETED', actor, 'SUCCESS', {
      evaluationRowNumber: evaluationRowNumber,
      slackStatus: slackResult.status
    });
  } catch (error) {
    var safeMessage = getSafeErrorMessage_(error);

    if (evaluationRowNumber !== null) {
      updateEvaluationStatus_(config, evaluationRowNumber, {
        slackStatus: 'NOT_POSTED',
        workflowStatus: 'FAILED',
        errorMessage: safeMessage
      });
    }

    appendAuditLog(config, correlationId, 'WORKFLOW_FAILED', actor, 'FAILURE', {
      error: safeMessage
    });

    throw error;
  } finally {
    lock.releaseLock();
  }
}

function ensureWorkflowSheets_(config) {
  getOrCreateSheet_(config.evaluationSheetName, getEvaluationHeaders());
  getOrCreateSheet_(config.auditSheetName, getAuditHeaders());
}

function getOrCreateSheet_(sheetName, headers) {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
  }

  return sheet;
}

function extractRequestFromEvent_(event) {
  if (!event || !event.namedValues) {
    throw new Error('Form submit event did not include namedValues.');
  }

  var aliases = getHeaderAliases();
  var namedValues = event.namedValues;
  var request = {
    formRowNumber: event.range ? event.range.getRow() : '',
    rawNamedValues: namedValues
  };

  Object.keys(aliases).forEach(function (canonicalName) {
    request[canonicalName] = firstValueForAliases_(namedValues, aliases[canonicalName]);
  });

  request.submittedAt = firstValueForAliases_(namedValues, ['Timestamp']) || new Date().toISOString();
  request.vendorDomain = extractDomain_(request.vendorWebsite);
  request.estimatedAnnualCostNumber = parseCurrencyLikeNumber_(request.expectedAnnualCost);

  return request;
}

function firstValueForAliases_(namedValues, aliases) {
  for (var i = 0; i < aliases.length; i++) {
    var value = namedValues[aliases[i]];
    if (value && value.length > 0) {
      return String(value[0]).trim();
    }
  }
  return '';
}

function validateTargetRequest_(request) {
  var missingFields = [];
  var requiredFields = [
    ['toolName', 'Tool Name'],
    ['vendorWebsite', 'Vendor Website'],
    ['businessOwner', 'Business Owner'],
    ['businessProblem', 'Business Problem'],
    ['dataClassification', 'Data Classification']
  ];

  requiredFields.forEach(function (field) {
    if (!request[field[0]]) {
      missingFields.push(field[1]);
    }
  });

  if (missingFields.length > 0) {
    throw new Error('Missing required fields: ' + missingFields.join(', '));
  }

  if (request.vendorWebsite && !/^https:\/\//i.test(request.vendorWebsite)) {
    throw new Error('Vendor Website must use HTTPS.');
  }
}

function buildEvaluationPrompt_(request, vendorContext) {
  var requestPayload = {
    request_type: request.requestType,
    requester_email: request.requesterEmail,
    requester_department: request.requesterDepartment,
    requester_manager: request.requesterManager,
    business_owner: request.businessOwner,
    tool_name: request.toolName,
    vendor_website: request.vendorWebsite,
    requested_users_or_teams: request.requestedUsersOrTeams,
    estimated_number_of_users: request.estimatedNumberOfUsers,
    business_problem: request.businessProblem,
    desired_outcome: request.desiredOutcome,
    alternatives_considered: request.alternativesConsidered,
    usage_stage: request.usageStage,
    expected_annual_cost: request.expectedAnnualCost,
    contract_term: request.contractTerm,
    data_classification: request.dataClassification,
    customer_data: request.customerData,
    personal_data: request.personalData,
    source_code_or_credentials: request.sourceCodeOrCredentials,
    authentication_method: request.authenticationMethod,
    integrations: request.integrations,
    oauth_scopes: request.oauthScopes,
    soc2_available: request.soc2Available,
    dpa_available: request.dpaAvailable,
    ai_training_use: request.aiTrainingUse,
    proposed_data_owner: request.proposedDataOwner,
    proposed_technical_owner: request.proposedTechnicalOwner,
    additional_context: request.additionalContext
  };

  return [
    'You are an IT, Security, Vendor Risk, and SOC2 review assistant for Balto Software, a 75-person remote SaaS company.',
    'Return valid JSON only. Do not approve tools; recommend routing and conditions for human reviewers.',
    'Assume Okta RBAC is imperfect. Prefer least privilege, SSO, SCIM, named owners, and quarterly access review.',
    'Do not claim vendor facts unless present in vendor_context_json. Treat MOCK vendor context as unverified.',
    '',
    'request_json:',
    JSON.stringify(requestPayload, null, 2),
    '',
    'vendor_context_json:',
    JSON.stringify(vendorContext, null, 2),
    '',
    'Return JSON with exactly these top-level keys: risk_rating, recommendation, summary, approval_gates, key_risks, least_privilege_requirements, soc2_evidence_needed, data_use_restrictions, open_questions, reviewer_notes.'
  ].join('\n');
}

function parseAndValidateEvaluation_(responseText) {
  var cleaned = stripJsonCodeFence_(responseText);
  var parsed = JSON.parse(cleaned);

  var allowedRiskRatings = ['low', 'medium', 'high', 'critical'];
  var allowedRecommendations = ['approve_with_conditions', 'needs_manual_review', 'reject'];

  if (allowedRiskRatings.indexOf(parsed.risk_rating) === -1) {
    throw new Error('LLM response has invalid risk_rating.');
  }

  if (allowedRecommendations.indexOf(parsed.recommendation) === -1) {
    throw new Error('LLM response has invalid recommendation.');
  }

  if (!Array.isArray(parsed.approval_gates) || parsed.approval_gates.length === 0) {
    throw new Error('LLM response must include approval_gates.');
  }

  if (!Array.isArray(parsed.soc2_evidence_needed) || parsed.soc2_evidence_needed.length === 0) {
    throw new Error('LLM response must include soc2_evidence_needed.');
  }

  return parsed;
}

function stripJsonCodeFence_(text) {
  var trimmed = String(text || '').trim();
  if (trimmed.indexOf('```') === 0) {
    trimmed = trimmed.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```$/i, '').trim();
  }
  return trimmed;
}

function writeEvaluationRecord_(config, correlationId, request, vendorContext, prompt, llmResult, evaluation, status) {
  var sheet = getOrCreateSheet_(config.evaluationSheetName, getEvaluationHeaders());
  var now = new Date().toISOString();
  var row = [
    correlationId,
    request.formRowNumber,
    request.submittedAt,
    request.requesterEmail,
    request.toolName,
    request.vendorWebsite,
    request.vendorDomain,
    request.businessOwner,
    request.dataClassification,
    request.expectedAnnualCost,
    evaluation.risk_rating,
    evaluation.recommendation,
    JSON.stringify(evaluation.approval_gates || []),
    JSON.stringify(evaluation.key_risks || []),
    JSON.stringify(evaluation.least_privilege_requirements || []),
    JSON.stringify(vendorContext),
    prompt,
    llmResult.provider,
    llmResult.model,
    JSON.stringify(evaluation),
    llmResult.text,
    status.slackStatus,
    status.workflowStatus,
    status.errorMessage,
    now,
    now
  ];

  sheet.appendRow(row);
  return sheet.getLastRow();
}

function updateEvaluationStatus_(config, rowNumber, status) {
  var sheet = getOrCreateSheet_(config.evaluationSheetName, getEvaluationHeaders());
  var headers = getEvaluationHeaders();
  var now = new Date().toISOString();
  var updates = {
    'Slack Status': status.slackStatus,
    'Workflow Status': status.workflowStatus,
    'Error Message': status.errorMessage,
    'Updated At': now
  };

  Object.keys(updates).forEach(function (header) {
    var column = headers.indexOf(header) + 1;
    if (column > 0) {
      sheet.getRange(rowNumber, column).setValue(updates[header]);
    }
  });
}

function appendAuditLog(config, correlationId, eventType, actor, status, details) {
  var sheet = getOrCreateSheet_(config.auditSheetName, getAuditHeaders());
  sheet.appendRow([
    new Date().toISOString(),
    correlationId,
    eventType,
    actor || 'unknown',
    status,
    JSON.stringify(redactSensitiveDetails_(details || {}))
  ]);
}

function redactSensitiveDetails_(details) {
  var serialized = JSON.stringify(details);
  return JSON.parse(serialized.replace(/(api[_-]?key|token|secret|password|webhook)/ig, 'redacted'));
}

function getSheetRowLink_(sheetName, rowNumber) {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(sheetName);
  return spreadsheet.getUrl() + '#gid=' + sheet.getSheetId() + '&range=A' + rowNumber;
}

function createCorrelationId_() {
  return 'tool-eval-' + Utilities.getUuid();
}

function extractDomain_(url) {
  if (!url) {
    return '';
  }

  var match = String(url).match(/^https?:\/\/([^\/?#]+)/i);
  return match ? match[1].toLowerCase().replace(/^www\./, '') : '';
}

function parseCurrencyLikeNumber_(value) {
  if (!value) {
    return 0;
  }
  var parsed = parseFloat(String(value).replace(/[^0-9.]/g, ''));
  return isNaN(parsed) ? 0 : parsed;
}

function getSafeErrorMessage_(error) {
  var message = error && error.message ? error.message : String(error);
  return message.substring(0, 1000);
}
