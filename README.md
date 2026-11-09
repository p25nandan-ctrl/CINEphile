# Kathaa Sangam - Supabase Authentication + Vercel deployment

The site is plain HTML/CSS/JS (no framework). Auth is added without changing the design:
Log In / Sign Up open a modal in the existing style; when logged in the header shows an account chip
(My account, Log out). `#account` is a user-only page whose data comes from `/api/me`, a Vercel
function that verifies the access token with Supabase on the server.

```
src/index.html      the whole site (unchanged except the auth hooks)
src/auth/auth.js    Supabase client + login/signup/forgot/reset UI (bundled to dist/auth.js)
api/me.js           server-side authorization (Bearer token -> Supabase auth.getUser)
build.mjs           injects SUPABASE_URL / SUPABASE_ANON_KEY at build time, fails the Vercel build if missing
vercel.json         build config + security headers
dev/                OFFLINE test helpers only (mock server). Not deployed (.vercelignore).
```

## Environment variables (names)
| Name | Where | Value |
|---|---|---|
| `SUPABASE_URL` | Vercel (Production + Preview) | Supabase > Project Settings > API > Project URL |
| `SUPABASE_ANON_KEY` | Vercel (Production + Preview) | the **anon / publishable** key |

The anon key is public by design. **Never** add the `service_role` / secret key: this project does not
need it and the build refuses it. Do not commit `.env`.

## 1. Supabase setup (you must do this)
1. Create a project at supabase.com.
2. **Authentication > Providers > Email**: enabled, **Confirm email = ON**, minimum password length 8
   (Authentication > Sign In / Providers > Password settings).
3. **Authentication > URL Configuration**
   - **Site URL**: your production URL, e.g. `https://kathaa-sangam.vercel.app`
   - **Redirect URLs** (add all):
     - `https://kathaa-sangam.vercel.app/**`
     - `https://*-<your-vercel-team>.vercel.app/**` (preview deployments, optional)
     - `http://localhost:3000/**` (local testing)
4. **Email delivery**: Supabase's built-in sender is heavily rate-limited (a few emails/hour) and for testing only.
   For real use configure **Authentication > Emails > SMTP Settings** with your own provider (Resend, Postmark, SES...).
5. Optional: Authentication > Emails > templates; keep the default `{{ .ConfirmationURL }}` links (the app uses the PKCE flow, so links arrive as `/?code=...`).
6. Optional hardening: enable CAPTCHA (Authentication > Attack Protection) and leaked-password protection.

## 2. Deploy to Vercel
1. Push this folder to a GitHub repo.
2. Vercel > Add New Project > import it. Framework preset: **Other**. Build/Output are read from `vercel.json` (`npm run build`, `dist`).
3. Project Settings > Environment Variables: add `SUPABASE_URL` and `SUPABASE_ANON_KEY` for Production and Preview.
4. Deploy. If a variable is missing the build fails with a clear message (by design).
5. Copy the final production URL into Supabase's Site URL / Redirect URLs (step 1.3) and redeploy if you changed anything.

CLI alternative: `npm i -g vercel && vercel` then `vercel env add SUPABASE_URL`, `vercel env add SUPABASE_ANON_KEY`, `vercel --prod`.

Local run: copy `.env.example` to `.env`, fill it, `npm install && npm run build`, then `vercel dev` (serves `/api/me` too).

## 3. Test after deployment (checklist)
- [ ] Sign up with a real inbox: you see "Check your email". Existing address shows the same message.
- [ ] Open the confirmation email link: you land on the site, logged in, with "Email verified".
- [ ] Log out (menu > Log out); header returns to Log In / Sign Up.
- [ ] Log in; refresh the page and open a new tab: still logged in.
- [ ] Wrong password: friendly error, no account hint. Unconfirmed email: offers resend.
- [ ] Forgot password: generic message; open the email link **in the same browser**; set a new password; log in with it.
- [ ] Expired/used link: shows "link has expired" and offers a new one.
- [ ] Visit `/#account` logged out: login modal opens. Logged in: shows details.
- [ ] `curl https://YOUR-DOMAIN/api/me` -> 401; with a valid Bearer token -> 200 JSON.
- [ ] Mobile width: Log In / Sign Up visible in the header and the modal fits.

## Notes
- Sessions live in the browser (supabase-js default storage, auto-refresh). The password is never stored by this app.
- The old standalone artifact page cannot hold Supabase settings; deploy this project for working auth.
