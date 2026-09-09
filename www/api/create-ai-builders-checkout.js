const STRIPE_API = 'https://api.stripe.com/v1/checkout/sessions';

function clean(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 50);
}

module.exports = async function handler(request, response) {
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ error: 'Method not allowed' });
  }

  const secretKey = process.env.STRIPE_SECRET_KEY;
  const publishableKey = process.env.STRIPE_PUBLISHABLE_KEY;
  const priceId = process.env.STRIPE_AI_BUILDERS_PRICE_ID;

  if (!secretKey || !publishableKey || !priceId) {
    return response.status(503).json({ error: 'Checkout is not configured' });
  }

  const forwardedHost = request.headers['x-forwarded-host'];
  const host = String(forwardedHost || request.headers.host || '').toLowerCase();
  const allowedHost = host === 'develop-coaching.com'
    || host === 'www.develop-coaching.com'
    || /^[a-z0-9-]+\.vercel\.app$/.test(host)
    || /^localhost:\d+$/.test(host)
    || /^127\.0\.0\.1:\d+$/.test(host);

  if (!allowedHost) {
    return response.status(400).json({ error: 'Invalid checkout origin' });
  }

  const protocol = request.headers['x-forwarded-proto'] || 'https';
  const origin = `${protocol}://${host}`;
  let body = request.body || {};
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body || '{}');
    } catch (error) {
      return response.status(400).json({ error: 'Invalid request body' });
    }
  }
  const reference = [
    `s-${clean(body.source) || 'direct'}`,
    clean(body.campaign) ? `c-${clean(body.campaign)}` : '',
    clean(body.content) ? `a-${clean(body.content)}` : '',
  ].filter(Boolean).join('__').slice(0, 200);

  const parameters = new URLSearchParams();
  parameters.set('mode', 'payment');
  parameters.set('ui_mode', 'embedded');
  parameters.set('line_items[0][price]', priceId);
  parameters.set('line_items[0][quantity]', '1');
  parameters.set('return_url', `${origin}/ai-for-builders-september-2026/?checkout=complete&session_id={CHECKOUT_SESSION_ID}`);
  parameters.set('client_reference_id', reference);
  parameters.set('metadata[event]', 'ai-for-builders-september-2026');

  try {
    const stripeResponse = await fetch(STRIPE_API, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${secretKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: parameters,
    });
    const session = await stripeResponse.json();

    if (!stripeResponse.ok || !session.client_secret) {
      return response.status(502).json({ error: 'Stripe could not create the checkout session' });
    }

    response.setHeader('Cache-Control', 'no-store');
    return response.status(200).json({
      clientSecret: session.client_secret,
      publishableKey,
    });
  } catch (error) {
    return response.status(502).json({ error: 'Stripe is temporarily unavailable' });
  }
}
