/**
 * Slack notification helpers.
 *
 * Slack is a reviewer notification channel, not the authoritative approval
 * record. The evaluation Sheet remains the SOC2 evidence source.
 */

function postSlackEvaluation(messageContext, config) {
  if (!config.slackWebhookUrl) {
    return {
      status: 'SKIPPED_NO_WEBHOOK',
      error: ''
    };
  }

  var payload = {
    text: buildSlackText_(messageContext)
  };

  var lastError = null;

  for (var attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      var response = UrlFetchApp.fetch(config.slackWebhookUrl, {
        method: 'post',
        muteHttpExceptions: true,
        contentType: 'application/json',
        payload: JSON.stringify(payload)
      });

      var statusCode = response.getResponseCode();
      if (statusCode >= 200 && statusCode < 300) {
        return {
          status: 'POSTED',
          error: ''
        };
      }

      lastError = new Error('Slack webhook returned HTTP ' + statusCode + ': ' + response.getContentText().substring(0, 500));
    } catch (error) {
      lastError = error;
    }

    if (attempt < config.maxRetries) {
      Utilities.sleep(config.retryBaseMs * Math.pow(2, attempt - 1));
    }
  }

  return {
    status: 'FAILED',
    error: getSafeErrorMessage_(lastError)
  };
}

function buildSlackText_(context) {
  var request = context.request;
  var evaluation = context.evaluation;
  var gates = (evaluation.approval_gates || []).map(function (gate) {
    return gate.gate + ': ' + gate.reason;
  }).join('\n');

  var risks = (evaluation.key_risks || []).slice(0, 5).map(function (risk) {
    return '- ' + risk.severity + ': ' + risk.risk + ' - ' + risk.mitigation;
  }).join('\n');

  return [
    '*New Software Tool Evaluation*',
    '*Tool:* ' + request.toolName,
    '*Requester:* ' + (request.requesterEmail || 'unknown'),
    '*Business owner:* ' + (request.businessOwner || 'unknown'),
    '*Risk rating:* ' + evaluation.risk_rating,
    '*Recommendation:* ' + evaluation.recommendation,
    '*Summary:* ' + evaluation.summary,
    '',
    '*Approval gates:*',
    gates || 'No gates returned by model. Manual review required.',
    '',
    '*Top risks:*',
    risks || 'No risks returned by model. Manual review required.',
    '',
    '*Evaluation record:* ' + context.rowLink,
    '_The Sheet is the source of truth. This Slack post is a notification only._'
  ].join('\n');
}
