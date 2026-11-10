// DEV-ONLY stand-in for Supabase GoTrue so the UI wiring can be exercised offline. NOT deployed, NOT a security test.
import http from 'node:http';
import crypto from 'node:crypto';
import { community, CDB, resetCommunity } from './mock-community.mjs';
const files = new Map(), rows = [], users = new Map(), codes = new Map(), mails = [], sessions = new Map();
const DB = { consent_records:[], child_profiles:[], story_progress:[], child_responses:[], quiz_attempts:[], response_reviews:[] };
const owns = (who, cid) => !!(who && cid && DB.child_profiles.some(c => c.id===cid && c.guardian_id===who.id));
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
  if (p === '/__resetcommunity') { resetCommunity(); return send(res,200,{}); }
  if (p === '/__community') return send(res,200,CDB);
  if (await community({ req, res, u, body, who, isAdm, send, err, files })) return;
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
  if (p === '/__state') return send(res,200,{files:[...files.keys()],rows,db:DB});
  if (p === '/__failinsert') { globalThis.__failInsert = u.searchParams.get('on')==='1'; return send(res,200,{}); }
  if (p === '/__failupload') { globalThis.__failUpload = u.searchParams.get('on')==='1'; return send(res,200,{}); }
  if (p.startsWith('/rest/v1/artwork_submissions')) {
    if (!who) return err(res,401,'JWT required');
    const single = /pgrst\.object/.test(req.headers.accept||''); const ret = x => single ? send(res,200,x[0]) : send(res,200,x);
    const q = k => { const v=u.searchParams.get(k); return v&&v.startsWith('eq.')?v.slice(3):null };
    if (req.method==='POST') { if(globalThis.__failInsert) return err(res,500,'boom');
      const r=Array.isArray(body)?body[0]:body; const bad = r.user_id&&r.user_id!==who.id; const folder=(r.storage_path||'').split('/')[0];
      if (bad || folder!==who.id || !r.consent_confirmed || !files.has(r.storage_path) || (r.child_id && !owns(who,r.child_id))) return send(res,403,{code:'42501',message:'new row violates row-level security policy for table "artwork_submissions"'});
      const row={id:crypto.randomUUID(),user_id:who.id,status:'pending',created_at:new Date().toISOString(),reviewed_at:null,reviewed_by:null,...r}; rows.push(row); return res.writeHead(201,{'content-type':'application/json','access-control-allow-origin':'*'}),res.end(JSON.stringify(single?row:[row])); }
    const vis = rows.filter(r=>isAdm||r.user_id===who.id);
    if (req.method==='GET') { let out=vis; const st=q('status'); if(st) out=out.filter(r=>r.status===st); const ci=q('child_id'); if(ci) out=out.filter(r=>r.child_id===ci); out=[...out].sort((a,b)=>b.created_at.localeCompare(a.created_at)); return send(res,200,out); }
    if (req.method==='PATCH' || req.method==='DELETE') { if(!isAdm) return ret(single?[]:[]) ; const id=q('id'); const m=rows.filter(r=>r.id===id);
      if (req.method==='PATCH') { m.forEach(r=>Object.assign(r,body)); if(single&&!m.length) return err(res,406,'The result contains 0 rows'); return ret(m); }
      m.forEach(r=>rows.splice(rows.indexOf(r),1)); return send(res,200,m); }
  }

  /* ---- DEV-ONLY approximation of supabase/learning.sql tables + RLS. NOT a test of the real policies. ---- */
  const T = req.method==='GET'||req.method==='POST'||req.method==='PATCH'||req.method==='DELETE'?(p.match(/^\/rest\/v1\/(consent_records|child_profiles|story_progress|child_responses|quiz_attempts|response_reviews)$/)||[])[1]:null;
  if (T) {
    if (!who) return err(res,401,'JWT required');
    const single = /pgrst\.object/.test(req.headers.accept||''), db = DB[T];
    const rls = () => send(res,403,{code:'42501',message:`new row violates row-level security policy for table "${T}"`});
    const bad = m => send(res,400,{code:'23514',message:m});
    const out = a => single ? (a.length===1?send(res,200,a[0]):err(res,406,'The result contains '+a.length+' rows')) : send(res,200,a);
    const visible = r => { if (T==='consent_records') return r.guardian_id===who.id; if (T==='child_profiles') return r.guardian_id===who.id||isAdm;
      if (T==='response_reviews') return isAdm || owns(who,(DB.child_responses.find(x=>x.id===r.response_id)||{}).child_id); return owns(who,r.child_id)||(isAdm&&T==='child_responses'); };
    const match = r => { for (const [k,v] of u.searchParams) { if (['select','order','limit','on_conflict'].includes(k)) continue;
      if (v.startsWith('eq.')) { if (String(r[k])!==v.slice(3)) return false; } else if (v.startsWith('in.(')) { if (!v.slice(4,-1).split(',').includes(String(r[k]))) return false; } } return true; };
    const KEYS = { story_progress:['child_id','story_id','level'], child_responses:['child_id','story_id','level','question_id'], consent_records:['guardian_id','version'], response_reviews:['response_id'] };
    const validate = r => {
      if (T==='child_profiles'){ if(typeof r.nickname!=='string'||r.nickname.length<1||r.nickname.length>24) return 'nickname length'; if(![1,2,3].includes(r.level)) return 'level'; if(r.grade!=null&&!(r.grade>=1&&r.grade<=12)) return 'grade'; }
      if (T==='story_progress'){ if(!['reading','completed'].includes(r.status)) return 'status'; if(!(r.page>=-1&&r.page<=60)) return 'page'; if(![1,2,3].includes(r.level)) return 'level'; }
      if (T==='child_responses'){ if(!/^[0-9IC]{1,3}$/.test(r.question_id||'')) return 'question_id'; if(!r.body||r.body.length>3000) return 'body'; }
      if (T==='quiz_attempts'){ if(!['comprehension','vocabulary'].includes(r.dimension)) return 'dimension'; if(typeof r.correct!=='boolean') return 'correct'; }
      if (T==='response_reviews'){ if(![r.written,r.critical].every(v=>Number.isInteger(v)&&v>=0&&v<=4)) return 'score'; }
      if (T==='consent_records'){ if(!['parent','guardian','teacher'].includes(r.role)) return 'role'; }
      return null; };
    if (req.method==='GET') return out(db.filter(r=>visible(r)&&match(r)).map(r=>({...r})));
    if (req.method==='POST') {
      const list = Array.isArray(body)?body:[body], upsert=/merge-duplicates/.test(req.headers.prefer||''), res_=[];
      for (const r0 of list) {
        const r={...r0};
        if (T==='consent_records'||T==='child_profiles') r.guardian_id=who.id;
        if (T==='response_reviews'){ if(!isAdm) return rls(); r.reviewer=who.id; r.reviewed_at=new Date().toISOString(); }
        else if (T!=='consent_records'&&T!=='child_profiles'&&!owns(who,r.child_id)) return rls();
        const v=validate(r); if (v) return bad('check constraint: '+v);
        if (T==='child_profiles'){ if(DB.child_profiles.filter(c=>c.guardian_id===who.id).length>=8) return bad('too many child profiles'); r.id=crypto.randomUUID(); r.created_at=new Date().toISOString(); }
        if (T==='quiz_attempts'||T==='child_responses'&&!r.id) { r.id=r.id||crypto.randomUUID(); r.created_at=new Date().toISOString(); }
        const keys=KEYS[T], dup=keys&&db.find(x=>keys.every(k=>x[k]===r[k]));
        if (dup) { if(!upsert) return send(res,409,{code:'23505',message:'duplicate key value violates unique constraint'}); Object.assign(dup,r,{id:dup.id,created_at:dup.created_at}); res_.push({...dup}); continue; }
        if (T==='response_reviews'&&!DB.child_responses.some(x=>x.id===r.response_id)) return bad('fk');
        db.push(r); res_.push({...r});
      }
      if (/return=minimal/.test(req.headers.prefer||'')) { res.writeHead(201,{'access-control-allow-origin':'*'}); return res.end(); }
      return res.writeHead(201,{'content-type':'application/json','access-control-allow-origin':'*'}),res.end(JSON.stringify(single?res_[0]:res_));
    }
    if (req.method==='PATCH') { if (T==='quiz_attempts'||T==='consent_records') return out([]); const m=db.filter(r=>visible(r)&&match(r)&&(T!=='response_reviews'||isAdm)); for (const r of m){ const nv={...r,...body}; const v=validate(nv); if(v) return bad('check constraint: '+v); if(body.guardian_id||body.child_id) return rls(); Object.assign(r,body);} return out(m.map(r=>({...r}))); }
    if (req.method==='DELETE') { if (T==='quiz_attempts'||T==='consent_records'||T==='response_reviews') return out([]); const m=db.filter(r=>visible(r)&&match(r)); m.forEach(r=>{db.splice(db.indexOf(r),1); if(T==='child_profiles') ['story_progress','child_responses','quiz_attempts'].forEach(t=>{DB[t]=DB[t].filter(x=>x.child_id!==r.id)}); if(T==='child_responses') DB.response_reviews=DB.response_reviews.filter(x=>x.response_id!==r.id);}); return out(m); }
  }
  err(res,404,'not found '+p);
}).listen(54321, () => console.log('mock gotrue on 54321'));
