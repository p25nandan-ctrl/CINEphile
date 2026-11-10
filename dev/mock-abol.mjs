// DEV-ONLY approximation of supabase/abol_community.sql (abol_submissions, public views, trigger rules, RLS, bucket abol-art).
// It mimics the INTENDED rules for offline UI tests; it is NOT a test of the real Postgres policies. Never deployed.
import crypto from 'node:crypto';
const PNG1 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
export const ADB = { abol_submissions: [] };
export function resetAbol() { ADB.abol_submissions.length = 0; }
const len = s => (s || '').trim().length;
const pub = r => r.status === 'published' && r.publish_consent;
const pick = (r, ks) => Object.fromEntries(ks.map(k => [k, r[k] ?? null]));
export async function abol(ctx) {
  const { req, res, u, body, who, isAdm, send, err, files } = ctx, p = u.pathname, m = req.method, T = ADB.abol_submissions;
  const single = /pgrst\.object/.test(req.headers.accept || '');
  const eq = k => { const v = u.searchParams.get(k); return v && v.startsWith('eq.') ? v.slice(3) : null; };
  const raw = (c, o) => { res.writeHead(c, { 'content-type': 'application/json', 'access-control-allow-origin': '*' }); res.end(JSON.stringify(o)); return true; };
  const out = a => single ? (a.length === 1 ? raw(200, a[0]) : (err(res, 406, 'rows ' + a.length), true)) : raw(200, a);
  const rls = () => (send(res, 403, { code: '42501', message: 'new row violates row-level security policy for table "abol_submissions"' }), true);
  const lim = a => { const n = +u.searchParams.get('limit'); return n > 0 ? a.slice(0, n) : a; };
  const ord = a => { const o = u.searchParams.get('order'); if (!o) return a; const [k, d] = o.split('.'); return [...a].sort((x, y) => (d === 'desc' ? -1 : 1) * String(x[k] ?? '').localeCompare(String(y[k] ?? ''))); };
  const filt = (a, cols) => a.filter(r => cols.every(c => { const v = eq(c); return v == null || String(r[c]) === v; }));
  const SB = '/storage/v1/object/';
  if (p.startsWith(SB + 'sign/abol-art/') && m === 'GET') { const f = files.get(decodeURIComponent(decodeURIComponent(p.slice((SB + 'sign/abol-art/').length)))); if (!f) { err(res, 404, 'nf'); return true; } res.writeHead(200, { 'content-type': 'image/png', 'access-control-allow-origin': '*' }); res.end(f.buf); return true; }
  if (p === SB + 'sign/abol-art' && m === 'POST') {
    send(res, 200, (body.paths || []).map(pa => { const f = files.get(pa); const row = T.find(r => r.art_public_path === pa && pub(r)); const ok = f && (row || (who && (isAdm || pa.split('/')[0] === who.id)));
      return ok ? { path: pa, signedURL: '/object/sign/abol-art/' + encodeURIComponent(pa) + '?token=t', error: null } : { path: pa, signedURL: null, error: 'not found' }; })); return true; }
  if (p.startsWith(SB + 'abol-art/') && m === 'POST') {
    if (!who) { err(res, 401, 'invalid JWT'); return true; }
    const key = decodeURIComponent(p.slice((SB + 'abol-art/').length)), folder = key.split('/')[0];
    if (!(folder === who.id || (folder === 'published' && isAdm))) { err(res, 403, 'new row violates row-level security policy'); return true; }
    if (Number(req.headers['content-length'] || 0) > 2 * 1024 * 1024 + 4096) { err(res, 413, 'exceeded'); return true; }
    if (files.has(key)) { err(res, 409, 'exists'); return true; }
    files.set(key, { buf: PNG1, type: 'image/png', owner: who.id, bucket: 'abol-art' }); send(res, 200, { Key: 'abol-art/' + key }); return true; }
  if (p === SB + 'copy' && m === 'POST' && /^published\//.test(body.destinationKey || '') && files.get(body.sourceKey)?.bucket === 'abol-art') {
    if (!who || !isAdm) { err(res, 403, 'rls'); return true; } files.set(body.destinationKey, { ...files.get(body.sourceKey), bucket: 'abol-art' }); send(res, 200, { Key: 'abol-art/' + body.destinationKey }); return true; }
  if (p === SB + 'abol-art' && m === 'DELETE') {
    if (!who) { err(res, 401, 'invalid JWT'); return true; }
    const del = (body.prefixes || []).filter(k => isAdm || (k.split('/')[0] === who.id && !T.some(r => r.art_path === k))); del.forEach(k => files.delete(k)); send(res, 200, del.map(name => ({ name }))); return true; }
  if (p === '/rest/v1/published_abol_creatures' && m === 'GET') return out(lim(ord(T.filter(r => r.kind === 'creature' && pub(r)).map(r => pick(r, ['id', 'title', 'description', 'art_public_path', 'published_at'])))));
  if (p === '/rest/v1/published_abol_poems' && m === 'GET') return out(lim(ord(T.filter(r => r.kind === 'poem' && pub(r)).map(r => pick(r, ['id', 'title', 'description', 'body', 'art_public_path', 'published_at'])))));
  if (p !== '/rest/v1/abol_submissions') return false;
  if (!who) return rls();
  const vis = r => isAdm || r.user_id === who.id;
  const validate = r => {
    if (!['creature', 'poem'].includes(r.kind)) return 'kind'; if (len(r.title) < 1 || len(r.title) > 80) return 'title';
    if (r.description != null && r.description.length > 300) return 'description';
    if (r.kind === 'creature' && !r.art_path) return 'creature_needs_image';
    if (r.kind === 'poem' && (len(r.body) < 20 || len(r.body) > 3000)) return 'poem_needs_text';
    if (r.art_path != null && !/^[0-9a-f-]{36}\/[0-9a-f-]{36}\.(jpg|png|webp)$/.test(r.art_path)) return 'art_path';
    if (r.consent_confirmed !== true) return 'consent_confirmed'; if (r.status === 'published' && !r.publish_consent) return 'published_needs_consent'; return null; };
  if (m === 'GET') return out(lim(ord(filt(T.filter(vis), ['id', 'kind', 'status', 'user_id']))).map(r => ({ ...r })));
  if (m === 'POST') {
    const r0 = Array.isArray(body) ? body[0] : body;
    if ((r0.user_id && r0.user_id !== who.id) || (r0.status && r0.status !== 'pending') || r0.reviewed_at || r0.published_at || r0.art_public_path) return rls();
    if (r0.art_path && (r0.art_path.split('/')[0] !== who.id || !files.has(r0.art_path))) return rls();
    const r = { id: crypto.randomUUID(), user_id: who.id, status: 'pending', publish_consent: false, description: null, body: null, art_path: null, art_public_path: null, art_content_type: null, reviewed_at: null, reviewed_by: null, published_at: null, created_at: new Date().toISOString(), ...r0, user_id: who.id };
    const v = validate(r); if (v) { send(res, 400, { code: '23514', message: 'check constraint: ' + v }); return true; }
    if (T.filter(x => x.user_id === who.id && x.status === 'pending').length >= 6) { send(res, 400, { code: 'P0001', message: 'too_many_waiting' }); return true; }
    T.push(r); return raw(201, single ? r : [r]); }
  if (m === 'PATCH') {
    if (!isAdm) return out([]); /* readers have no update policy: 0 rows */
    const hit = T.filter(r => eq('id') == null || r.id === eq('id'));
    for (const r of hit) { const nv = { ...r, ...body }; ['user_id', 'kind', 'title', 'description', 'body', 'art_path', 'art_content_type', 'consent_confirmed', 'publish_consent', 'created_at'].forEach(k => nv[k] = r[k]);
      nv.reviewed_at = new Date().toISOString(); nv.reviewed_by = who.id; if (nv.status === 'published') nv.published_at = r.published_at || new Date().toISOString(); else { nv.published_at = null; nv.art_public_path = null; }
      const v = validate(nv); if (v) { send(res, 400, { code: '23514', message: 'check constraint: ' + v }); return true; } Object.assign(r, nv); }
    return out(hit.map(r => ({ ...r }))); }
  if (m === 'DELETE') { const hit = T.filter(r => (eq('id') == null || r.id === eq('id')) && (isAdm || (r.user_id === who.id && r.status !== 'published'))); hit.forEach(r => T.splice(T.indexOf(r), 1)); return raw(200, hit); }
  return false;
}
