const EVENT = 'ai-for-builders-september-2026';
module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') { res.setHeader('Allow', 'GET'); return res.status(405).json({ error: 'Method not allowed' }); }
  const id = req.query && req.query.session_id;
  if (typeof id !== 'string' || !/^cs_(test_|live_)[a-zA-Z0-9]+$/.test(id)) return res.status(400).json({ error: 'Invalid confirmation reference' });
  if (!process.env.STRIPE_SECRET_KEY || !process.env.STRIPE_AI_BUILDERS_PRICE_ID) return res.status(503).json({ error: 'Confirmation temporarily unavailable' });
  try {
    const response = await fetch(`https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(id)}?expand[]=line_items`, { headers: { Authorization: `Bearer ${process.env.STRIPE_SECRET_KEY}` } });
    const session = await response.json();
    const items = session.line_items && session.line_items.data;
    if (!response.ok || session.mode !== 'payment' || session.metadata?.event !== EVENT || session.amount_total !== 4500 || session.currency !== 'gbp' || !items || items.length !== 1 || items[0].quantity !== 1 || items[0].price?.id !== process.env.STRIPE_AI_BUILDERS_PRICE_ID) return res.status(400).json({ error: 'We could not verify this workshop payment.' });
    return res.status(200).json({ status: session.status === 'complete' && session.payment_status === 'paid' ? 'paid' : 'pending', event: EVENT, amount: 4500, currency: 'gbp' });
  } catch { return res.status(502).json({ error: 'Confirmation temporarily unavailable' }); }
};
