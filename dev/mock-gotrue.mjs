// DEV-ONLY stand-in for Supabase GoTrue so the UI wiring can be exercised offline. NOT deployed, NOT a security test.
import http from 'node:http';
import crypto from 'node:crypto';
const files = new Map(), rows = [], users = new Map(), codes = new Map(), mails = [], sessions = new Map();
const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
const jwt = u => `${b64({alg:'HS256',typ:'JWT'})}.${b64({sub:u.id,email:u.email,role:'authenticated',app_metadata:u.email.startsWith('admin@')?{role:'admin'}:{},exp:Math.floor(Date.now()/1000)+3600,aud:'authenticated'})}.sig`;
const pub = u => ({ id:u.id, aud:'authenticated', role:'authenticated', email:u.email, email_confirmed_at:u.confirmed?u.created:null, created_at:u.created, last_sign_in_at:u.last, app_metadata:u.email.startsWith('admin@')?{provider:'email',role:'admin'}:{provider:'email'}, user_metadata:u.meta||{}, identities:[{id:u.id}] });
const sess = u => { const rt = crypto.randomUUID(); u.last = new Date().toISOString(); const s = { access_token:jwt(u), token_type:'bearer', expires_in:3600, expires_at:Math.floor(Date.now()/1000)+3600, refresh_token:rt, user:pub(u) }; sessions.set(rt,u.email); return s; };
const send = (res, code, obj, hdr={}) => { res.writeHead(code, { 'content-type':'application/json', 'access-control-allow-origin':'*', 'access-control-allow-headers':'*', 'access-control-allow-methods':'*', ...hdr }); res.end(obj===undefined?'':JSON.stringify(obj)); };
const err = (res, code, msg, ec) => send(res, code, { code, error_code:ec, msg, message:msg });
http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x'); if (req.method === 'OPTIONS') return send(res, 204);
  let body = {}; if (['POST','PUT','PATCH','DELETE'].includes(req.method)) { let d=''; for await (const c of req) d+=c; try{ body = JSON.parse(d||'{}'); }catch{} }
  const bearer = (req.headers.authorization||'').replace(/^Bearer /,''); const byTok = () => { try { const p = JSON.parse(Buffer.from(bearer.split('.')[1],'base64url')); return [...users.values()].find(x=>x.id===p.sub); } catch { return null; } };
  const p = u.pathname;
  if (p === '/__mail') return send(res, 200, mails);
  if (p === '/auth/v1/signup') {
    const email = (body.email||'').toLowerCase(); if ((body.password||'').length < 8) return err(res,422,'Password should be at least 8 characters.','weak_password');
    let x = users.get(email);
    if (!x) { x = { id:crypto.randomUUID(), email, pw:body.password, created:new Date().toISOString(), confirmed:false, meta:body.data }; users.set(email,x); const c = crypto.randomUUID(); codes.set(c,{email,kind:'signup'}); mails.push({to:email,kind:'signup',link:`http://localhost:54321/auth/v1/verify?c=${c}&redirect_to=${encodeURIComponent(u.searchParams.get('redirect_to')||'')}`}); return send(res,200,pub(x)); }
    return send(res,200,{ ...pub(x), identities:[] }); // obfuscated for existing email
  }
  if (p === '/auth/v1/verify') { const c = codes.get(u.searchParams.get('c')); if (!c) return send(res,302,{}, {location:(u.searchParams.get('redirect_to')||'/')+'#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired'}); const x = users.get(c.email); if (c.kind==='signup') x.confirmed = true; const ac = crypto.randomUUID(); codes.set(ac,{email:c.email,kind:'pkce',type:c.kind}); const r = new URL(u.searchParams.get('redirect_to')); r.searchParams.set('code', ac); res.writeHead(302,{location:r.toString()}); return res.end(); }
  if (p === '/auth/v1/token') {
    const g = u.searchParams.get('grant_type');
    if (g === 'password') { const x = users.get((body.email||'').toLowerCase()); if (!x || x.pw !== body.password) return err(res,400,'Invalid login credentials','invalid_credentials'); if (!x.confirmed) return err(res,400,'Email not confirmed','email_not_confirmed'); return send(res,200,sess(x)); }
    if (g === 'refresh_token') { const e = sessions.get(body.refresh_token); if (!e) return err(res,400,'Invalid Refresh Token: Refresh Token Not Found','refresh_token_not_found'); return send(res,200,sess(users.get(e))); }
    if (g === 'pkce') { const c = codes.get(body.auth_code); if (!c) return err(res,400,'invalid flow state, no valid flow state found','flow_state_not_found'); const x = users.get(c.email); return send(res,200,sess(x)); }
  }
  if (p === '/auth/v1/user' && req.method === 'GET') { const x = byTok(); return x ? send(res,200,pub(x)) : err(res,401,'invalid JWT','bad_jwt'); }
  if (p === '/auth/v1/user' && req.method === 'PUT') { const x = byTok(); if (!x) return err(res,401,'invalid JWT','bad_jwt'); if (body.password) { if (body.password.length<8) return err(res,422,'Password should be at least 8 characters.','weak_password'); if (body.password===x.pw) return err(res,422,'New password should be different from the old password.','same_password'); x.pw = body.password; } return send(res,200,pub(x)); }
  if (p === '/auth/v1/logout') { return send(res,204); }
  if (p === '/auth/v1/recover') { const email=(body.email||'').toLowerCase(); if (users.has(email)) { const c = crypto.randomUUID(); codes.set(c,{email,kind:'recovery'}); mails.push({to:email,kind:'recovery',link:`http://localhost:54321/auth/v1/verify?c=${c}&redirect_to=${encodeURIComponent(u.searchParams.get('redirect_to')||'')}`}); } return send(res,200,{}); }
  if (p === '/auth/v1/resend') { const email=(body.email||'').toLowerCase(); if (users.has(email) && !users.get(email).confirmed) { const c = crypto.randomUUID(); codes.set(c,{email,kind:'signup'}); mails.push({to:email,kind:'resend',link:`http://localhost:54321/auth/v1/verify?c=${c}&redirect_to=${encodeURIComponent(u.searchParams.get('redirect_to')||'')}`}); } return send(res,200,{}); }

  /* ---- DEV-ONLY approximation of Supabase Storage + PostgREST for the artwork flow. Mimics the intended RLS rules; it is NOT a test of the real policies. ---- */
  const who = byTok(); const isAdm = !!(who && who.email.startsWith('admin@'));
  if (p.startsWith('/storage/v1/')) {
    if (p.startsWith('/storage/v1/object/sign/child-art/') && req.method==='GET') { const key = decodeURIComponent(p.slice('/storage/v1/object/sign/child-art/'.length)); const f = files.get(key); if(!f) return err(res,404,'nf'); res.writeHead(200,{'content-type':f.type,'access-control-allow-origin':'*'}); return res.end(f.buf); }
    if (!who) return err(res,401,'invalid JWT');
    if (p.startsWith('/storage/v1/object/child-art/') && req.method==='POST') {
      const key = decodeURIComponent(p.slice('/storage/v1/object/child-art/'.length)); const buf=Buffer.alloc(0); buf.size=Number(req.headers['content-length']||0);
      if (key.split('/')[0] !== who.id) return err(res,403,'new row violates row-level security policy');
      if (buf.size > 2*1024*1024+4096) return err(res,413,'The object exceeded the maximum allowed size');
      if (files.has(key)) return err(res,409,'The resource already exists');
      if (globalThis.__failUpload) return err(res,500,'boom');
      files.set(key,{buf,type:'image/png',owner:who.id}); return send(res,200,{Key:'child-art/'+key,Id:crypto.randomUUID()});
    }
    if (p==='/storage/v1/object/sign/child-art' && req.method==='POST') { const out=(body.paths||[]).map(pa=>{const f=files.get(pa); return f&&(isAdm||f.owner===who.id)?{path:pa,signedURL:'/object/sign/child-art/'+encodeURIComponent(pa)+'?token=t',error:null}:{path:pa,signedURL:null,error:'not found'}}); return send(res,200,out); }
    if (p==='/storage/v1/object/child-art' && req.method==='DELETE') { const del=(body.prefixes||[]).filter(k=>isAdm||(k.split('/')[0]===who.id&&!rows.some(r=>r.storage_path===k))); del.forEach(k=>files.delete(k)); return send(res,200,del.map(name=>({name}))); }
    return err(res,404,'nf '+p);
  }
  if (p === '/__state') return send(res,200,{files:[...files.keys()],rows});
  if (p === '/__failinsert') { globalThis.__failInsert = u.searchParams.get('on')==='1'; return send(res,200,{}); }
  if (p === '/__failupload') { globalThis.__failUpload = u.searchParams.get('on')==='1'; return send(res,200,{}); }
  if (p.startsWith('/rest/v1/artwork_submissions')) {
    if (!who) return err(res,401,'JWT required');
    const single = /pgrst\.object/.test(req.headers.accept||''); const ret = x => single ? send(res,200,x[0]) : send(res,200,x);
    const q = k => { const v=u.searchParams.get(k); return v&&v.startsWith('eq.')?v.slice(3):null };
    if (req.method==='POST') { if(globalThis.__failInsert) return err(res,500,'boom');
      const r=Array.isArray(body)?body[0]:body; const bad = r.user_id&&r.user_id!==who.id; const folder=(r.storage_path||'').split('/')[0];
      if (bad || folder!==who.id || !r.consent_confirmed || !files.has(r.storage_path)) return send(res,403,{code:'42501',message:'new row violates row-level security policy for table "artwork_submissions"'});
      const row={id:crypto.randomUUID(),user_id:who.id,status:'pending',created_at:new Date().toISOString(),reviewed_at:null,reviewed_by:null,...r}; rows.push(row); return res.writeHead(201,{'content-type':'application/json','access-control-allow-origin':'*'}),res.end(JSON.stringify(single?row:[row])); }
    const vis = rows.filter(r=>isAdm||r.user_id===who.id);
    if (req.method==='GET') { let out=vis; const st=q('status'); if(st) out=out.filter(r=>r.status===st); out=[...out].sort((a,b)=>b.created_at.localeCompare(a.created_at)); return send(res,200,out); }
    if (req.method==='PATCH' || req.method==='DELETE') { if(!isAdm) return ret(single?[]:[]) ; const id=q('id'); const m=rows.filter(r=>r.id===id);
      if (req.method==='PATCH') { m.forEach(r=>Object.assign(r,body)); if(single&&!m.length) return err(res,406,'The result contains 0 rows'); return ret(m); }
      m.forEach(r=>rows.splice(rows.indexOf(r),1)); return send(res,200,m); }
  }
  err(res,404,'not found '+p);
}).listen(54321, () => console.log('mock gotrue on 54321'));
