// Kathaa Sangam - Supabase Auth UI. Bundled by esbuild; SUPABASE_URL / SUPABASE_ANON_KEY are inlined at build time.
// Only the PUBLIC anon key is used. Sessions are managed by supabase-js (PKCE flow, auto refresh).
import { createClient } from '@supabase/supabase-js';

const SB_URL = process.env.SUPABASE_URL;
const SB_KEY = process.env.SUPABASE_ANON_KEY;
const CONFIGURED = !!(SB_URL && SB_KEY);

const $ = (s, r = document) => r.querySelector(s);
const slot = $('#authSlot'), modal = $('#authModal'), card = modal && $('.au-card', modal);
const el = {
  tabs: $('#auTabs'), title: $('#authTitle'), sub: $('#auSub'), msg: $('#auMsg'), form: $('#auForm'),
  name: $('#auName'), email: $('#auEmail'), pass: $('#auPass'), pass2: $('#auPass2'), passL: $('#auPassL'), hint: $('#auHint'),
  fName: $('#fName'), fEmail: $('#fEmail'), fPass: $('#fPass'), fPass2: $('#fPass2'), eye: $('#auEye'),
  go: $('#auGo'), goT: $('#auGoT'), links: $('#auLinks'), close: $('#auClose'),
};

const sb = CONFIGURED ? createClient(SB_URL, SB_KEY, {
  auth: { flowType: 'pkce', persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
}) : null;

let session = null, ready = false, view = 'login', busy = false, lastFocus = null, afterLogin = null, pendingEmail = '', resendUntil = 0;
const readyCbs = [];
const whenReady = () => ready ? Promise.resolve() : new Promise(r => readyCbs.push(r));

const origin = () => location.origin;
const toast = m => { const t = $('#toast'); if (!t) return; t.textContent = m; t.classList.add('show'); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove('show'), 3800); };
const validEmail = v => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);

/* ---------- friendly error text (never leaks internals) ---------- */
function friendly(err) {
  const m = String((err && err.message) || ''), s = err && err.status, c = (err && (err.code || err.error_code)) || '';
  if (/invalid login credentials/i.test(m) || c === 'invalid_credentials') return 'That email and password do not match. Please check and try again.';
  if (/email not confirmed/i.test(m) || c === 'email_not_confirmed') return 'EMAIL_UNCONFIRMED';
  if (s === 429 || /rate limit|too many/i.test(m) || c === 'over_email_send_rate_limit' || c === 'over_request_rate_limit') return 'Too many attempts. Please wait a minute and try again.';
  if (/password.*(short|least|weak|characters)/i.test(m) || c === 'weak_password') return 'Please choose a stronger password (at least 8 characters).';
  if (/same password|different from the old/i.test(m) || c === 'same_password') return 'Your new password must be different from the old one.';
  if (/expired|invalid|otp/i.test(m) && /link|token|otp/i.test(m)) return 'This link has expired or was already used. Please request a new one.';
  if (/session.*(missing|not found)/i.test(m) || c === 'session_not_found') return 'Your session has ended. Please log in again.';
  if (/fetch|network|failed to/i.test(m) || err instanceof TypeError) return 'We could not reach the server. Check your connection and try again.';
  if (/signups? (not allowed|disabled)/i.test(m) || c === 'signup_disabled') return 'New sign-ups are currently turned off.';
  return 'Something went wrong. Please try again in a moment.';
}

/* ---------- message region ---------- */
function say(kind, text) { el.msg.hidden = !text; el.msg.className = 'au-msg ' + (kind || ''); el.msg.textContent = text || ''; }
function setBusy(b, label) { busy = b; el.go.disabled = b; if (label) el.goT.textContent = label; }
function invalid(input, on) { input.setAttribute('aria-invalid', on ? 'true' : 'false'); }

/* ---------- views inside the modal ---------- */
const VIEWS = {
  login:  { title: 'Welcome back', sub: 'Log in to keep your stories and progress with you.', go: 'Log in', fields: ['email', 'pass'], pw: 'current-password', tabs: true },
  signup: { title: 'Join Kathaa Sangam', sub: 'Create your free account. We will email you a link to confirm it.', go: 'Create account', fields: ['name', 'email', 'pass'], pw: 'new-password', tabs: true },
  forgot: { title: 'Forgot password?', sub: 'Enter your email and we will send you a link to choose a new password.', go: 'Send reset link', fields: ['email'], tabs: false },
  reset:  { title: 'Choose a new password', sub: 'Pick something at least 8 characters long.', go: 'Save new password', fields: ['pass', 'pass2'], pw: 'new-password', tabs: false },
  sent:   { title: 'Check your email', sub: '', go: '', fields: [], tabs: false },
};
function setView(v, opts = {}) {
  view = v; const d = VIEWS[v];
  el.title.textContent = d.title; el.sub.textContent = d.sub; el.sub.hidden = !d.sub;
  el.tabs.hidden = !d.tabs;
  $('#tabLogin').setAttribute('aria-selected', v === 'login'); $('#tabSignup').setAttribute('aria-selected', v === 'signup');
  $('#tabLogin').tabIndex = v === 'login' ? 0 : -1; $('#tabSignup').tabIndex = v === 'signup' ? 0 : -1;
  el.fName.hidden = !d.fields.includes('name'); el.fEmail.hidden = !d.fields.includes('email');
  el.fPass.hidden = !d.fields.includes('pass'); el.fPass2.hidden = !d.fields.includes('pass2');
  el.passL.textContent = v === 'reset' ? 'New password' : 'Password';
  el.hint.hidden = !(v === 'signup' || v === 'reset');
  if (d.pw) el.pass.setAttribute('autocomplete', d.pw);
  el.form.hidden = v === 'sent';
  el.go.hidden = v === 'sent'; el.goT.textContent = d.go;
  el.pass.type = 'password'; el.eye.setAttribute('aria-pressed', 'false'); el.eye.setAttribute('aria-label', 'Show password');
  [el.email, el.pass, el.pass2].forEach(i => invalid(i, false));
  if (!opts.keepMsg) say('', '');
  if (!opts.keepValues) { el.pass.value = ''; el.pass2.value = ''; }
  renderLinks();
  if (!opts.noFocus) setTimeout(() => { const f = v === 'sent' ? $('#auLinks button') : v === 'signup' ? el.name : v === 'reset' ? el.pass : el.email; f && f.focus(); }, 30);
}
function linkBtn(text, fn, dis) { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; if (dis) b.disabled = true; b.addEventListener('click', fn); return b; }
function renderLinks() {
  el.links.textContent = '';
  if (view === 'login') el.links.append(linkBtn('Forgot password?', () => setView('forgot', { keepValues: true })));
  if (view === 'forgot') el.links.append(linkBtn('← Back to log in', () => setView('login')));
  if (view === 'sent') {
    const wait = Math.max(0, Math.ceil((resendUntil - Date.now()) / 1000));
    el.links.append(linkBtn(wait ? `Resend email (${wait}s)` : 'Resend email', resend, wait > 0), linkBtn('Back to log in', () => setView('login')));
    if (wait) setTimeout(() => view === 'sent' && renderLinks(), 1000);
  }
}

/* ---------- modal open / close / focus trap ---------- */
function openModal(v = 'login', cb) {
  if (!modal) return;
  afterLogin = cb || null; lastFocus = document.activeElement;
  closeMenu(); setView(v);
  modal.classList.remove('hidden'); document.body.classList.add('au-open');
  if (!CONFIGURED) say('err', 'Sign-in is not configured on this site yet. The owner must add the Supabase settings (see README).');
}
function closeModal() {
  if (modal.classList.contains('hidden')) return;
  modal.classList.add('hidden'); document.body.classList.remove('au-open'); afterLogin = null;
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
modal && modal.addEventListener('mousedown', e => { if (e.target === modal) closeModal(); });
el.close && el.close.addEventListener('click', closeModal);
document.addEventListener('keydown', e => {
  if (modal && !modal.classList.contains('hidden')) {
    if (e.key === 'Escape') { e.preventDefault(); closeModal(); return; }
    if (e.key === 'Tab') {
      const f = [...modal.querySelectorAll('button,input,[href],[tabindex]:not([tabindex="-1"])')].filter(n => !n.disabled && !n.hidden && n.offsetParent !== null);
      if (!f.length) return; const a = f[0], z = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === a || document.activeElement === card)) { e.preventDefault(); z.focus(); }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
    }
  } else if (e.key === 'Escape') closeMenu();
});
el.tabs && el.tabs.addEventListener('click', e => { const b = e.target.closest('[data-view]'); if (b) setView(b.dataset.view, { keepValues: true }); });
el.tabs && el.tabs.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { setView(view === 'login' ? 'signup' : 'login', { keepValues: true, noFocus: true }); $('#' + (view === 'login' ? 'tabLogin' : 'tabSignup')).focus(); } });
el.eye && el.eye.addEventListener('click', () => {
  const show = el.pass.type === 'password'; el.pass.type = show ? 'text' : 'password'; el.pass2.type = el.pass.type;
  el.eye.setAttribute('aria-pressed', String(show)); el.eye.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
});

/* ---------- actions ---------- */
async function resend() {
  if (!sb || !pendingEmail || Date.now() < resendUntil) return;
  resendUntil = Date.now() + 60000; renderLinks();
  const { error } = await sb.auth.resend({ type: 'signup', email: pendingEmail, options: { emailRedirectTo: origin() + '/?auth=verified' } });
  say(error ? 'err' : 'ok', error ? friendly(error) : 'If that address has an unconfirmed account, a new link is on its way.');
}
async function submit(e) {
  e.preventDefault(); if (busy) return;
  if (!sb) { say('err', 'Sign-in is not configured on this site yet. The owner must add the Supabase settings (see README).'); return; }
  const email = el.email.value.trim(), pw = el.pass.value;
  say('', ''); [el.email, el.pass, el.pass2].forEach(i => invalid(i, false));
  try {
    if (view === 'login') {
      if (!validEmail(email)) { invalid(el.email, true); el.email.focus(); return say('err', 'Please enter a valid email address.'); }
      if (!pw) { invalid(el.pass, true); el.pass.focus(); return say('err', 'Please enter your password.'); }
      setBusy(true, 'Logging in…');
      const { error } = await sb.auth.signInWithPassword({ email, password: pw });
      if (error) {
        const f = friendly(error);
        if (f === 'EMAIL_UNCONFIRMED') { pendingEmail = email; setView('sent', { keepMsg: true }); el.sub.hidden = false; el.sub.textContent = ''; return sentText(email, 'Your email is not confirmed yet. Open the link we sent to ' + email + ', then log in.'); }
        invalid(el.pass, true); return say('err', f);
      }
      const cb = afterLogin; closeModal(); toast('Welcome back! 🌟'); cb && cb();
    } else if (view === 'signup') {
      if (!validEmail(email)) { invalid(el.email, true); el.email.focus(); return say('err', 'Please enter a valid email address.'); }
      if (pw.length < 8) { invalid(el.pass, true); el.pass.focus(); return say('err', 'Your password needs at least 8 characters.'); }
      setBusy(true, 'Creating account…');
      const name = el.name.value.trim().slice(0, 60);
      const { data, error } = await sb.auth.signUp({ email, password: pw, options: { emailRedirectTo: origin() + '/?auth=verified', data: name ? { full_name: name } : {} } });
      if (error) return say('err', friendly(error) === 'EMAIL_UNCONFIRMED' ? 'Please try logging in.' : friendly(error));
      if (data && data.session) { const cb = afterLogin; closeModal(); toast('Welcome to Kathaa Sangam! 🎉'); cb && cb(); return; }
      // Same message whether or not the address already existed (prevents account enumeration).
      pendingEmail = email; resendUntil = Date.now() + 60000; setView('sent');
      sentText(email, 'We sent a confirmation link to ' + email + '. Open it to activate your account, then log in. It can take a minute; check spam too.');
    } else if (view === 'forgot') {
      if (!validEmail(email)) { invalid(el.email, true); el.email.focus(); return say('err', 'Please enter a valid email address.'); }
      setBusy(true, 'Sending…');
      const { error } = await sb.auth.resetPasswordForEmail(email, { redirectTo: origin() + '/?auth=recovery' });
      if (error && (error.status === 429 || /rate/i.test(error.message || ''))) return say('err', friendly(error));
      pendingEmail = ''; setView('sent');
      el.links.textContent = ''; el.links.append(linkBtn('Back to log in', () => setView('login')));
      sentText(email, 'If an account exists for ' + email + ', a password reset link is on its way. The link works in this same browser.');
    } else if (view === 'reset') {
      if (pw.length < 8) { invalid(el.pass, true); el.pass.focus(); return say('err', 'Your password needs at least 8 characters.'); }
      if (pw !== el.pass2.value) { invalid(el.pass2, true); el.pass2.focus(); return say('err', 'The two passwords do not match.'); }
      setBusy(true, 'Saving…');
      const { error } = await sb.auth.updateUser({ password: pw });
      if (error) return say('err', friendly(error));
      closeModal(); toast('Password updated. You are logged in. ✅');
    }
  } catch (err) { say('err', friendly(err)); }
  finally { setBusy(false); const d = VIEWS[view]; el.goT.textContent = d.go; }
}
function sentText(email, text) { el.sub.hidden = false; el.sub.textContent = text; say('ok', 'Check your inbox ✉️'); }
el.form && el.form.addEventListener('submit', submit);

async function logout() {
  closeMenu();
  if (sb) { const { error } = await sb.auth.signOut(); if (error && !/session/i.test(error.message || '')) { await sb.auth.signOut({ scope: 'local' }); } }
  toast('You are logged out. See you soon! 👋');
}

/* ---------- header slot ---------- */
let menuEl = null;
function closeMenu() { if (!menuEl) return; menuEl.classList.add('hidden'); const b = $('.au-me', slot); b && b.setAttribute('aria-expanded', 'false'); }
function displayName(u) { return (u.user_metadata && u.user_metadata.full_name) || (u.email || '?').split('@')[0]; }
function renderSlot() {
  slot.textContent = ''; menuEl = null;
  slot.removeAttribute('aria-busy');
  if (!session) {
    const a = document.createElement('button'); a.className = 'btn-o'; a.id = 'btnLogin'; a.type = 'button'; a.textContent = 'Log In'; a.addEventListener('click', () => openModal('login'));
    const b = document.createElement('button'); b.className = 'btn-y'; b.id = 'btnSignup'; b.type = 'button'; b.textContent = 'Sign Up'; b.addEventListener('click', () => openModal('signup'));
    slot.append(a, b); return;
  }
  const u = session.user, name = displayName(u);
  const wrap = document.createElement('div'); wrap.className = 'au-meWrap';
  const btn = document.createElement('button'); btn.type = 'button'; btn.className = 'au-me'; btn.id = 'btnMe';
  btn.setAttribute('aria-haspopup', 'true'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-label', 'Account menu for ' + name);
  const av = document.createElement('span'); av.className = 'au-av'; av.textContent = name.trim().charAt(0) || '?';
  const nm = document.createElement('span'); nm.className = 'au-nm'; nm.textContent = name;
  btn.append(av, nm);
  const menu = document.createElement('div'); menu.className = 'au-menu hidden'; menu.id = 'auMenu';
  const who = document.createElement('div'); who.className = 'au-who'; const wb = document.createElement('b'); wb.textContent = name; const ws = document.createElement('small'); ws.textContent = u.email || ''; who.append(wb, ws);
  const acc = document.createElement('a'); acc.href = '#account'; acc.textContent = '👤 My account'; acc.addEventListener('click', closeMenu);
  const out = document.createElement('button'); out.type = 'button'; out.id = 'btnLogout'; out.textContent = '↩ Log out'; out.addEventListener('click', logout);
  menu.append(who, acc, out); wrap.append(btn, menu); slot.append(wrap); menuEl = menu;
  btn.addEventListener('click', e => { e.stopPropagation(); const open = menu.classList.contains('hidden'); menu.classList.toggle('hidden', !open); btn.setAttribute('aria-expanded', String(open)); if (open) acc.focus(); });
}
document.addEventListener('click', e => { if (menuEl && !e.target.closest('.au-meWrap')) closeMenu(); });

/* ---------- account page (user-only; server verifies the token via /api/me) ---------- */
function row(l, v) { const d = document.createElement('div'); const s = document.createElement('small'); s.textContent = l; const b = document.createElement('b'); b.textContent = v; d.append(s, b); return d; }
const fmt = s => s ? new Date(s).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '-';
async function showAccount() {
  const body = $('#acBody'); if (!body) return;
  body.textContent = ''; const ld = document.createElement('p'); ld.className = 'acv-load'; ld.innerHTML = '<span class="au-spin on" aria-hidden="true"></span> Checking your account…'; body.append(ld);
  await whenReady();
  if (!session) {
    body.textContent = ''; const p = document.createElement('p'); p.style.cssText = 'margin:0 0 12px;font-weight:800'; p.textContent = 'Please log in to see your account.';
    const b = document.createElement('button'); b.className = 'btn-y'; b.type = 'button'; b.textContent = 'Log in'; b.addEventListener('click', () => openModal('login', showAccount));
    body.append(p, b); openModal('login', showAccount); return;
  }
  let info = null, serverMsg = '';
  try {
    const r = await fetch('/api/me', { headers: { Authorization: 'Bearer ' + session.access_token }, cache: 'no-store' });
    if (r.status === 401) { await sb.auth.signOut({ scope: 'local' }); return; }
    if (!r.ok) throw new Error('status ' + r.status);
    info = await r.json();
  } catch (_) { serverMsg = 'We could not verify your session with the server just now, so some details are hidden. Please try again.'; }
  body.textContent = '';
  if (!info) {
    const p = document.createElement('p'); p.style.cssText = 'margin:0 0 12px;font-weight:800'; p.textContent = serverMsg;
    const r = document.createElement('button'); r.className = 'btn-y'; r.type = 'button'; r.textContent = 'Try again'; r.addEventListener('click', showAccount); body.append(p, r); return;
  }
  const name = info.name || (info.email || '').split('@')[0];
  const top = document.createElement('div'); top.className = 'acv-top';
  const av = document.createElement('span'); av.className = 'au-av'; av.textContent = name.charAt(0);
  const t = document.createElement('div'); const nb = document.createElement('b'); nb.textContent = name; const es = document.createElement('small'); es.textContent = info.email;
  const bd = document.createElement('span'); bd.className = 'acv-badge ' + (info.email_verified ? 'ok' : 'no'); bd.textContent = info.email_verified ? '✓ Email verified' : 'Email not verified';
  t.append(nb, es, document.createElement('br'), bd); top.append(av, t);
  const rows = document.createElement('div'); rows.className = 'acv-rows';
  rows.append(row('Member since', fmt(info.created_at)), row('Last sign-in', fmt(info.last_sign_in_at)), row('Account ID', info.id));
  const h = document.createElement('h3'); h.textContent = 'Change password';
  const f = document.createElement('form'); f.className = 'acv-form'; f.noValidate = true;
  f.innerHTML = '<label class="au-f"><span>New password</span><input id="acPw" type="password" autocomplete="new-password" minlength="8" required></label><label class="au-f"><span>Confirm new password</span><input id="acPw2" type="password" autocomplete="new-password" minlength="8" required></label><div class="au-msg" id="acMsg" role="alert" hidden></div><button class="btn-y au-go" type="submit" style="width:auto">Update password</button>';
  f.addEventListener('submit', async ev => {
    ev.preventDefault(); const m = $('#acMsg'), a = $('#acPw').value, b2 = $('#acPw2').value;
    const show = (k, x) => { m.hidden = false; m.className = 'au-msg ' + k; m.textContent = x; };
    if (a.length < 8) return show('err', 'Your password needs at least 8 characters.');
    if (a !== b2) return show('err', 'The two passwords do not match.');
    const { error } = await sb.auth.updateUser({ password: a });
    if (error) return show('err', friendly(error));
    f.reset(); show('ok', 'Password updated.');
  });
  const act = document.createElement('div'); act.className = 'acv-actions';
  const lo = document.createElement('button'); lo.type = 'button'; lo.className = 'btn-o'; lo.style.cssText = 'color:var(--jamun);border-color:var(--jamun);display:inline-block'; lo.textContent = 'Log out'; lo.addEventListener('click', logout);
  act.append(lo); body.append(top, rows, h, f, act);
}

/* ---------- boot ---------- */
function stripAuthParams() {
  const u = new URL(location.href); ['auth', 'code', 'error', 'error_code', 'error_description'].forEach(k => u.searchParams.delete(k));
  history.replaceState(null, '', u.pathname + (u.search || '') + (u.hash && !/error|access_token|type=/.test(u.hash) ? u.hash : ''));
}
async function boot() {
  if (!modal || !slot) return;
  const q = new URLSearchParams(location.search), hp = new URLSearchParams(location.hash.replace(/^#/, ''));
  const flag = q.get('auth'), linkErr = q.get('error_description') || hp.get('error_description');
  if (!sb) { renderSlot(); ready = true; readyCbs.splice(0).forEach(f => f()); return; }
  sb.auth.onAuthStateChange((evt, s) => {
    session = s;
    // Defer: never call supabase from inside this callback.
    setTimeout(() => {
      renderSlot(); window.dispatchEvent(new CustomEvent('ks:auth'));
      if (evt === 'PASSWORD_RECOVERY') { openModal('reset'); }
      if (evt === 'SIGNED_OUT' && location.hash === '#account') location.hash = '';
    }, 0);
  });
  const { data } = await sb.auth.getSession(); // waits for any ?code= exchange (email links)
  session = data.session; ready = true; renderSlot(); readyCbs.splice(0).forEach(f => f());
  if (linkErr) { openModal('login'); say('err', /expired|invalid/i.test(linkErr) ? 'That email link has expired or was already used. Please request a new one.' : 'That email link could not be used. Please request a new one.'); }
  else if (flag === 'verified') { session ? toast('Email verified. Welcome to Kathaa Sangam! 🎉') : openModal('login'); if (!session) say('ok', 'Email verified. You can log in now.'); }
  else if (flag === 'recovery' && session) openModal('reset');
  else if (flag === 'recovery' && !session) { openModal('forgot'); say('err', 'Open the reset link in the same browser where you requested it, or request a new link.'); }
  if (flag || linkErr || q.get('code')) stripAuthParams();
  if (location.hash === '#account') showAccount();
}

/* ---------- Artwork submissions (children) and review (administrators) ----------
   Files go to the PRIVATE storage bucket "child-art" (folder = the child's user id); a row in public.artwork_submissions records
   story, time, optional text and review status. Success is reported only after BOTH the file and the record are saved.
   Row-level security (supabase/artwork.sql) is what enforces who can see what; the checks here are for friendly messages. */
const ART = { max: 2 * 1024 * 1024, bucket: 'child-art', ext: { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp' } };
const isAdmin = () => !!(session && session.user && session.user.app_metadata && session.user.app_metadata.role === 'admin');
async function sniff(file) {
  const b = new Uint8Array(await file.slice(0, 12).arrayBuffer());
  if (b[0] === 0xFF && b[1] === 0xD8 && b[2] === 0xFF) return 'image/jpeg';
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4E && b[3] === 0x47 && b[4] === 0x0D && b[5] === 0x0A && b[6] === 0x1A && b[7] === 0x0A) return 'image/png';
  if (b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 && b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50) return 'image/webp';
  return null;
}
const FAIL = e => ({ ok: false, error: e });
async function submitArtwork({ storyId, file, title, description, consent }) {
  if (!sb) return FAIL('Artwork sharing is not switched on yet.');
  await whenReady();
  if (!session) return FAIL('Please log in first.');
  if (!/^[a-z0-9-]{1,60}$/.test(storyId || '')) return FAIL('We could not tell which story this is for.');
  if (!consent) return FAIL('Please tick the box to say a parent, guardian or teacher is happy for you to share this.');
  if (!file) return FAIL('Please choose a picture first.');
  if (file.size < 1 || file.size > ART.max) return FAIL('That picture is too big. Please choose one under 2 MB.');
  const type = await sniff(file);
  if (!type) return FAIL('Please choose a JPG, PNG or WebP picture.');
  title = (title || '').trim().slice(0, 80); description = (description || '').trim().slice(0, 300);
  const path = session.user.id + '/' + crypto.randomUUID() + '.' + ART.ext[type];
  const up = await sb.storage.from(ART.bucket).upload(path, file, { contentType: type, upsert: false, cacheControl: '3600' });
  if (up.error) return FAIL('We could not save the picture. Nothing was sent. Please try again.');
  const ins = await sb.from('artwork_submissions').insert({ story_id: storyId, storage_path: path, content_type: type, size_bytes: file.size,
    title: title || null, description: description || null, consent_confirmed: true }).select('id,created_at,status').single();
  if (ins.error || !ins.data) {
    await sb.storage.from(ART.bucket).remove([path]); // do not leave an orphan file behind
    return FAIL('We could not save your submission. Nothing was sent. Please try again.');
  }
  return { ok: true, id: ins.data.id, created_at: ins.data.created_at, status: ins.data.status };
}
const el_ = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
async function mountAdmin(root) {
  root.textContent = '';
  const note = t => { root.textContent = ''; root.append(el_('p', 'bk-small', t)); };
  if (!sb) return note('Review is not switched on because the site is not connected to its database yet.');
  await whenReady();
  if (!session) { note('Please log in with an administrator account.'); const b = el_('button', 'lbtn', 'Log in'); b.type = 'button'; b.onclick = () => openModal('login'); root.append(b); return; }
  if (!isAdmin()) return note('This page is for project administrators only.');
  const bar = el_('div', 'lis-bar'), sel = el_('select'); sel.setAttribute('aria-label', 'Show');
  [['pending', 'Waiting for review'], ['approved', 'Approved'], ['rejected', 'Rejected'], ['all', 'All']].forEach(([v, t]) => { const o = el_('option', '', t); o.value = v; sel.append(o); });
  const status = el_('p', 'lis-st'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const list = el_('div', 'ad-list'); bar.append(el_('label', 'lspd', 'Show '), sel); root.append(bar, status, list);
  bar.firstChild.append(sel);
  async function load() {
    list.textContent = ''; status.textContent = 'Loading…';
    let q = sb.from('artwork_submissions').select('*').order('created_at', { ascending: false }).limit(200);
    if (sel.value !== 'all') q = q.eq('status', sel.value);
    const { data, error } = await q;
    if (error) { status.className = 'lis-st err'; status.textContent = 'Could not load submissions.'; return; }
    status.className = 'lis-st'; status.textContent = data.length ? data.length + ' submission' + (data.length === 1 ? '' : 's') : 'Nothing here.';
    const urls = {};
    if (data.length) { const r = await sb.storage.from(ART.bucket).createSignedUrls(data.map(d => d.storage_path), 300); (r.data || []).forEach(x => { if (x.path && x.signedUrl) urls[x.path] = x.signedUrl; }); }
    data.forEach(d => {
      const card = el_('article', 'ad-card');
      const fig = el_('div', 'ad-img');
      if (urls[d.storage_path]) { const im = new Image(); im.src = urls[d.storage_path]; im.alt = 'Submitted artwork' + (d.title ? ': ' + d.title : ''); im.loading = 'lazy'; fig.append(im); } else fig.textContent = 'Preview unavailable';
      const story = (typeof REAL !== 'undefined' && REAL[d.story_id] && REAL[d.story_id].title) || d.story_id;
      const meta = el_('div', 'ad-meta');
      meta.append(el_('b', '', 'Inspired by: ' + story), el_('span', '', d.title || '(no title)'), el_('span', 'bk-small', d.description || ''),
        el_('span', 'bk-small', 'Sent ' + new Date(d.created_at).toLocaleString() + ' · ' + Math.round(d.size_bytes / 1024) + ' KB · ID ' + d.id.slice(0, 8)));
      const pill = el_('span', 'pill ' + (d.status === 'approved' ? 'ok' : d.status === 'rejected' ? 'todo' : 'check'), d.status); meta.prepend(pill);
      const acts = el_('div', 'lis-bar');
      const mk = (label, fn) => { const b = el_('button', 'lbtn', label); b.type = 'button'; b.onclick = async () => { b.disabled = true; await fn(); b.disabled = false; }; return b; };
      const setS = async st => {
        const r = await sb.from('artwork_submissions').update({ status: st, reviewed_at: new Date().toISOString(), reviewed_by: session.user.id }).eq('id', d.id).select('id,status').single();
        if (r.error || !r.data) { status.className = 'lis-st err'; status.textContent = 'That change was not saved.'; return; }
        load();
      };
      if (d.status !== 'approved') acts.append(mk('✅ Approve', () => setS('approved')));
      if (d.status !== 'rejected') acts.append(mk('⛔ Reject', () => setS('rejected')));
      acts.append(mk('🗑 Delete', async () => {
        if (!confirm('Delete this artwork and its record permanently?')) return;
        const rf = await sb.storage.from(ART.bucket).remove([d.storage_path]);
        if (rf.error) { status.className = 'lis-st err'; status.textContent = 'The file could not be deleted.'; return; }
        const rr = await sb.from('artwork_submissions').delete().eq('id', d.id).select('id');
        if (rr.error || !rr.data || !rr.data.length) { status.className = 'lis-st err'; status.textContent = 'The record could not be deleted.'; return; }
        load();
      }));
      card.append(fig, meta, acts); list.append(card);
    });
  }
  sel.onchange = load; load();
}
window.KathaaArt = { configured: CONFIGURED, ready: whenReady, signedIn: () => !!session, isAdmin, submit: submitArtwork, mountAdmin, login: () => openModal('login') };
window.KathaaAuth = { showAccount, open: openModal, logout, configured: CONFIGURED };
boot();
