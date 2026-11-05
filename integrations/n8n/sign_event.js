// Reference for a SEPARATE test sidecar Code node. Never paste into a live baseline blindly.
// Requires an IT-approved crypto signing capability and secret binding in the n8n instance.
// Input must already be normalized to the documented evaluation contract.
const crypto = require('crypto');
const secret = $env.N8N_WEBHOOK_SECRET;
if (!secret || secret.length < 32) throw new Error('Signing is not configured');
return $input.all().map(item => {
  const evaluation = item.json;
  const envelope = { event_id: crypto.randomUUID(), issued_at: Math.floor(Date.now() / 1000), evaluation };
  const rawBody = JSON.stringify(envelope);
  const signature = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  return { json: { rawBody, signature } };
});
