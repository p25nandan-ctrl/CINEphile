// DEV-ONLY approximation of supabase/community.sql (tables, views, trigger rules, RLS and the story-art bucket) for offline
// UI tests. It mimics the INTENDED rules; it is NOT a test of the real Postgres policies. Never deployed.
import crypto from 'node:crypto';
const PNG1 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64'); // 1x1 PNG so previews can really render
export const CDB = { user_stories: [], testimonials: [] };
const STATES28 = new Set('as kl mh gj ap ar br ct ga hr hp jh ka mp mn ml mz nl or pb rj sk tn tg tr up ut wb'.split(' '));
const PUBLIC_STORY = ['id','title','body','language','state_id','inspiration','art_public_path','published_at'];
const PUBLIC_TESTI = ['id','quote','role','display_name','sort_order'];
const pick = (r, keys) => Object.fromEntries(keys.map(k => [k, r[k] ?? null]));
const len = s => (s || '').trim().length;
const isPublished = r => r.status === 'published' && r.publish_consent;

export function resetCommunity() { CDB.user_stories.length = 0; CDB.testimonials.length = 0; }

export async function community(ctx) {
  const { req, res, u, body, who, isAdm, send, err, files } = ctx, p = u.pathname, m = req.method;
  const single = /pgrst\.object/.test(req.headers.accept || '');
  const eq = k => { const v = u.searchParams.get(k); return v && v.startsWith('eq.') ? v.slice(3) : null; };
  const raw = (code, o) => { res.writeHead(code, { 'content-type': 'application/json', 'access-control-allow-origin': '*' }); res.end(JSON.stringify(o)); return true; };
  const out = a => { if (single) return a.length === 1 ? raw(200, a[0]) : (err(res, 406, 'The result contains ' + a.length + ' rows'), true); return raw(200, a); };
  const rls = t => (send(res, 403, { code: '42501', message: `new row violates row-level security policy for table "${t}"` }), true);
  const bad = msg => (send(res, 400, { code: '23514', message: msg }), true);
  const order = a => { const o = u.searchParams.get('order'); if (!o) return a; const [k, d] = o.split('.'); return [...a].sort((x, y) => (d === 'desc' ? -1 : 1) * String(x[k] ?? '').localeCompare(String(y[k] ?? ''))); };
  const lim = a => { const n = +u.searchParams.get('limit'); return n > 0 ? a.slice(0, n) : a; };
  const filt = (a, cols) => a.filter(r => cols.every(c => { const v = eq(c); return v == null || String(r[c]) === v; }));

  /* ---------- storage: bucket story-art ---------- */
  const SB = '/storage/v1/object/';
  if (p.startsWith(SB + 'sign/story-art/') && m === 'GET') {
    const key = decodeURIComponent(decodeURIComponent(p.slice((SB + 'sign/story-art/').length))); const f = files.get(key); if (!f) { err(res, 404, 'nf'); return true; }
    res.writeHead(200, { 'content-type': f.type || 'image/png', 'access-control-allow-origin': '*' }); res.end(f.buf); return true;
  }
  if (p === SB + 'sign/story-art' && m === 'POST') {
    const outp = (body.paths || []).map(pa => {
      const f = files.get(pa); const row = CDB.user_stories.find(r => r.art_public_path === pa && isPublished(r));
      const ok = f && (row || (who && (isAdm || pa.split('/')[0] === who.id)));
      return ok ? { path: pa, signedURL: '/object/sign/story-art/' + encodeURIComponent(pa) + '?token=t', error: null } : { path: pa, signedURL: null, error: 'not found' };
    });
    send(res, 200, outp); return true;
  }
  if (p.startsWith(SB + 'story-art/') && m === 'POST') {
    if (!who) { err(res, 401, 'invalid JWT'); return true; }
    const key = decodeURIComponent(p.slice((SB + 'story-art/').length)); const folder = key.split('/')[0];
    if (!(folder === who.id || (folder === 'published' && isAdm))) { err(res, 403, 'new row violates row-level security policy'); return true; }
    const size = Number(req.headers['content-length'] || 0); if (size > 2 * 1024 * 1024 + 4096) { err(res, 413, 'The object exceeded the maximum allowed size'); return true; }
    if (files.has(key)) { err(res, 409, 'The resource already exists'); return true; }
    if (globalThis.__failUpload) { err(res, 500, 'boom'); return true; }
    const buf = PNG1; files.set(key, { buf, type: 'image/png', owner: who.id, bucket: 'story-art' }); send(res, 200, { Key: 'story-art/' + key, Id: crypto.randomUUID() }); return true;
  }
  if (p === SB + 'copy' && m === 'POST') {
    if (!who || !isAdm) { err(res, 403, 'new row violates row-level security policy'); return true; }
    const f = files.get(body.sourceKey); if (!f || !/^published\//.test(body.destinationKey || '')) { err(res, 404, 'not found'); return true; }
    files.set(body.destinationKey, { ...f, bucket: 'story-art' }); send(res, 200, { Key: 'story-art/' + body.destinationKey }); return true;
  }
  if (p === SB + 'story-art' && m === 'DELETE') {
    if (!who) { err(res, 401, 'invalid JWT'); return true; }
    const del = (body.prefixes || []).filter(k => isAdm || (k.split('/')[0] === who.id && !CDB.user_stories.some(r => r.art_path === k)));
    del.forEach(k => files.delete(k)); send(res, 200, del.map(name => ({ name }))); return true;
  }

  /* ---------- views (public) ---------- */
  if (p === '/rest/v1/published_user_stories' && m === 'GET') {
    let a = CDB.user_stories.filter(isPublished).map(r => pick(r, PUBLIC_STORY)); a = lim(order(filt(a, ['id', 'language', 'state_id']))); return out(a);
  }
  if (p === '/rest/v1/published_testimonials' && m === 'GET') {
    return out(lim(order(CDB.testimonials.filter(r => r.status === 'approved').map(r => pick(r, PUBLIC_TESTI)))));
  }

  /* ---------- user_stories ---------- */
  if (p === '/rest/v1/user_stories') {
    if (!who) return rls('user_stories');
    const vis = r => isAdm || r.user_id === who.id;
    const validate = r => {
      if (len(r.title) < 1 || len(r.title) > 100) return 'title length';
      if (len(r.body) < 20 || len(r.body) > 8000) return 'body length';
      if (!['en', 'hi'].includes(r.language)) return 'language';
      if (r.state_id != null && !STATES28.has(r.state_id)) return 'state_id';
      if (r.inspiration != null && r.inspiration.length > 300) return 'inspiration length';
      if (r.art_path != null && !/^[0-9a-f-]{36}\/[0-9a-f-]{36}\.(jpg|png|webp)$/.test(r.art_path)) return 'art_path';
      if (r.consent_confirmed !== true) return 'consent_confirmed';
      if (r.status === 'published' && !r.publish_consent) return 'published_needs_consent';
      return null;
    };
    if (m === 'GET') return out(lim(order(filt(CDB.user_stories.filter(vis), ['id', 'status', 'user_id']))).map(r => ({ ...r })));
    if (m === 'POST') {
      const r0 = Array.isArray(body) ? body[0] : body;
      if (globalThis.__failInsert) { send(res, 500, { message: 'boom' }); return true; }
      if ((r0.user_id && r0.user_id !== who.id) || (r0.status && r0.status !== 'pending') || r0.reviewed_at || r0.reviewed_by || r0.published_at || r0.admin_note || r0.art_public_path) return rls('user_stories');
      if (r0.art_path && (r0.art_path.split('/')[0] !== who.id || !files.has(r0.art_path))) return rls('user_stories');
      const r = { id: crypto.randomUUID(), user_id: who.id, status: 'pending', publish_consent: false, admin_note: null, art_public_path: null, art_content_type: null, art_path: null, state_id: null, inspiration: null,
        reviewed_at: null, reviewed_by: null, published_at: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...r0, user_id: who.id };
      const v = validate(r); if (v) return bad('check constraint: ' + v);
      if (CDB.user_stories.filter(x => x.user_id === who.id && ['pending', 'revision_requested'].includes(x.status)).length >= 5) { send(res, 400, { code: 'P0001', message: 'too_many_waiting' }); return true; }
      CDB.user_stories.push(r); return raw(201, single ? r : [r]);
    }
    if (m === 'PATCH') {
      const hit = CDB.user_stories.filter(r => vis(r) && (eq('id') == null || r.id === eq('id')));
      for (const r of hit) {
        const nv = { ...r, ...body };
        if (isAdm) { // admin: moderation columns only
          ['user_id', 'title', 'body', 'language', 'state_id', 'inspiration', 'art_path', 'art_content_type', 'consent_confirmed', 'publish_consent', 'created_at'].forEach(k => nv[k] = r[k]);
          nv.reviewed_at = new Date().toISOString(); nv.reviewed_by = who.id;
          if (nv.status === 'published') nv.published_at = r.published_at || new Date().toISOString(); else { nv.published_at = null; nv.art_public_path = null; }
        } else {
          if (!['pending', 'revision_requested'].includes(r.status)) { send(res, 400, { code: 'P0001', message: 'locked' }); return true; }
          Object.assign(nv, { user_id: r.user_id, status: 'pending', admin_note: r.admin_note, reviewed_at: r.reviewed_at, reviewed_by: r.reviewed_by, published_at: null, art_public_path: null, created_at: r.created_at });
        }
        const v = validate(nv); if (v) return bad('check constraint: ' + v);
        nv.updated_at = new Date().toISOString(); Object.assign(r, nv);
      }
      return out(hit.map(r => ({ ...r })));
    }
    if (m === 'DELETE') {
      const hit = CDB.user_stories.filter(r => (eq('id') == null || r.id === eq('id')) && (isAdm || (r.user_id === who.id && r.status !== 'published')));
      hit.forEach(r => CDB.user_stories.splice(CDB.user_stories.indexOf(r), 1)); return raw(200, hit);
    }
  }

  /* ---------- testimonials (admin only) ---------- */
  if (p === '/rest/v1/testimonials') {
    if (!who || !isAdm) return rls('testimonials');
    const validate = r => {
      if (len(r.quote) < 10 || len(r.quote) > 400) return 'quote length';
      if (!['student', 'teacher', 'parent', 'educator', 'other'].includes(r.role)) return 'role';
      if (r.display_name != null && r.display_name.length > 60) return 'display_name';
      if (!['draft', 'approved', 'hidden'].includes(r.status)) return 'status';
      if (r.status === 'approved' && r.is_child && !r.permission_confirmed) return 'child_needs_permission';
      if (r.status === 'approved' && len(r.source_note) === 0) return 'approved_needs_source';
      return null;
    };
    if (m === 'GET') return out(lim(order(filt(CDB.testimonials, ['id', 'status']))).map(r => ({ ...r })));
    if (m === 'POST') {
      const r = { id: crypto.randomUUID(), display_name: null, is_child: false, permission_confirmed: false, source_note: null, status: 'draft', sort_order: 0, created_by: who.id, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...(Array.isArray(body) ? body[0] : body) };
      const v = validate(r); if (v) return bad('check constraint: ' + v); CDB.testimonials.push(r); return raw(201, single ? r : [r]);
    }
    if (m === 'PATCH') {
      const hit = CDB.testimonials.filter(r => eq('id') == null || r.id === eq('id'));
      for (const r of hit) { const nv = { ...r, ...body, id: r.id }; const v = validate(nv); if (v) return bad('check constraint: ' + v); nv.updated_at = new Date().toISOString(); Object.assign(r, nv); }
      return out(hit.map(r => ({ ...r })));
    }
    if (m === 'DELETE') { const hit = CDB.testimonials.filter(r => eq('id') == null || r.id === eq('id')); hit.forEach(r => CDB.testimonials.splice(CDB.testimonials.indexOf(r), 1)); return raw(200, hit); }
  }
  return false;
}
