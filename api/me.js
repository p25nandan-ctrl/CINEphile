// Server-side authorization: verifies the caller's Supabase access token with Supabase Auth
// (auth.getUser asks the Auth server, so revoked/expired tokens are rejected) and only then
// returns data. Uses the public anon key + the user's own JWT; the service-role key is NOT needed.
const { createClient } = require('@supabase/supabase-js');

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') { res.setHeader('Allow', 'GET'); return res.status(405).json({ error: 'method_not_allowed' }); }
  const m = /^Bearer\s+(.+)$/i.exec(req.headers.authorization || '');
  if (!m) return res.status(401).json({ error: 'unauthorized' });
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_ANON_KEY;
  if (!url || !key) return res.status(500).json({ error: 'server_not_configured' });
  try {
    const sb = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } });
    const { data, error } = await sb.auth.getUser(m[1]);
    if (error || !data || !data.user) return res.status(401).json({ error: 'unauthorized' });
    const u = data.user;
    return res.status(200).json({
      id: u.id,
      email: u.email,
      name: (u.user_metadata && u.user_metadata.full_name) || null,
      email_verified: !!u.email_confirmed_at,
      created_at: u.created_at,
      last_sign_in_at: u.last_sign_in_at || null,
    });
  } catch (e) {
    return res.status(502).json({ error: 'auth_server_unreachable' });
  }
};
