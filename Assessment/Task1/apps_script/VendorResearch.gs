/**
 * Vendor research integration.
 *
 * The v1 workflow supports a configured endpoint and a clearly labeled MOCK
 * fallback. Mock data is useful for deterministic tests and demos, but it is
 * not acceptable final vendor evidence for sensitive production use.
 */

function researchVendor(request, config) {
  if (config.vendorResearchEndpoint) {
    try {
      return lookupVendorWithConfiguredEndpoint_(request, config);
    } catch (error) {
      if (!config.enableMockVendorResearch) {
        throw error;
      }
      return buildMockVendorContext_(request, 'Configured vendor research failed: ' + getSafeErrorMessage_(error));
    }
  }

  if (config.enableMockVendorResearch) {
    return buildMockVendorContext_(request, 'No approved vendor research endpoint configured.');
  }

  throw new Error('Vendor research endpoint is not configured and mock vendor research is disabled.');
}

function lookupVendorWithConfiguredEndpoint_(request, config) {
  var response = UrlFetchApp.fetch(config.vendorResearchEndpoint, {
    method: 'post',
    muteHttpExceptions: true,
    contentType: 'application/json',
    payload: JSON.stringify({
      tool_name: request.toolName,
      vendor_website: request.vendorWebsite,
      vendor_domain: request.vendorDomain
    })
  });

  var statusCode = response.getResponseCode();
  var body = response.getContentText();

  if (statusCode < 200 || statusCode >= 300) {
    throw new Error('Vendor research endpoint returned HTTP ' + statusCode + ': ' + body.substring(0, 500));
  }

  var parsed = JSON.parse(body);
  parsed.source = parsed.source || 'configured_endpoint';
  parsed.verified = parsed.verified === true;
  return parsed;
}

function buildMockVendorContext_(request, reason) {
  return {
    source: 'MOCK_VENDOR_RESEARCH',
    verified: false,
    reason: reason,
    vendor_name: request.toolName,
    vendor_domain: request.vendorDomain,
    vendor_website: request.vendorWebsite,
    trust_center_url: request.vendorSecurityUrl || '',
    soc2_status: request.soc2Available || 'Unknown',
    dpa_status: request.dpaAvailable || 'Unknown',
    sso_status: request.authenticationMethod || 'Unknown',
    scim_status: 'Unknown',
    ai_training_status: request.aiTrainingUse || 'Unknown',
    notes: [
      'This is MOCK context. A human reviewer must verify vendor facts before approval.',
      'Use this only to exercise workflow routing and evidence generation.'
    ]
  };
}
