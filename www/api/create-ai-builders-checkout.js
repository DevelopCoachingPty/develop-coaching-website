const EVENT = 'ai-for-builders-september-2026';
const STRIPE = 'https://api.stripe.com/v1';
module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed' }); }
  const key = process.env.STRIPE_SECRET_KEY, publishableKey = process.env.STRIPE_PUBLISHABLE_KEY, priceId = process.env.STRIPE_AI_BUILDERS_PRICE_ID;
  if (!key || !publishableKey || !priceId) return res.status(503).json({ error: 'Booking is temporarily unavailable. Please try again shortly.' });
  const host = String(req.headers['x-forwarded-host'] || req.headers.host || '').toLowerCase();
  if (!/^(develop-coaching\.com|www\.develop-coaching\.com|[a-z0-9-]+\.vercel\.app|localhost:\d+|127\.0\.0\.1:\d+)$/.test(host)) return res.status(400).json({ error: 'Invalid origin' });
  const origin = `${/^(localhost|127\.)/.test(host) ? 'http' : 'https'}://${host}`;
  if (req.headers.origin && req.headers.origin !== origin) return res.status(403).json({ error: 'Invalid origin' });
  let body;
  try { body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body || {}; } catch { return res.status(400).json({ error: 'Invalid request' }); }
  if (!/^[a-zA-Z0-9-]{16,80}$/.test(body.attemptId || '')) return res.status(400).json({ error: 'Please refresh and try again.' });
  try {
    const headers = { Authorization: `Bearer ${key}` };
    const priceResponse = await fetch(`${STRIPE}/prices/${encodeURIComponent(priceId)}`, { headers });
    const price = await priceResponse.json();
    if (!priceResponse.ok || !price.active || price.product !== 'prod_T9GTRdidVpjXVZ' || price.type !== 'one_time' || price.recurring || price.currency !== 'gbp' || price.unit_amount !== 4500) return res.status(503).json({ error: 'Booking is temporarily unavailable. Please contact hello@develop-coaching.com.' });
    const params = new URLSearchParams({ mode: 'payment', ui_mode: 'embedded', 'line_items[0][price]': priceId, 'line_items[0][quantity]': '1', 'payment_method_types[0]': 'card', return_url: `${origin}/${EVENT}/?checkout=complete&session_id={CHECKOUT_SESSION_ID}`, 'metadata[event]': EVENT, 'payment_intent_data[metadata][event]': EVENT, client_reference_id: EVENT });
    const response = await fetch(`${STRIPE}/checkout/sessions`, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded', 'Idempotency-Key': `${EVENT}-${body.attemptId}` }, body: params });
    const session = await response.json();
    if (!response.ok || !session.client_secret) return res.status(502).json({ error: 'Booking is temporarily unavailable. Please try again shortly.' });
    return res.status(200).json({ clientSecret: session.client_secret, publishableKey });
  } catch { return res.status(502).json({ error: 'Booking is temporarily unavailable. Please try again shortly.' }); }
};
