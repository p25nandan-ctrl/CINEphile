# Kathaa Sangam: v3 update (Journey fixes, Stories nav, instant signup, Abol Tabol submissions, About, footer)

Status: code changed and tested **against a local mock backend only**. Nothing here has been run against the real Supabase project or the deployed Vercel site.

## 1. What was wrong, and what changed

| Item | Cause found in the code | Fix |
|---|---|---|
| **Stories tab broken** | The nav link scrolls to `#featured`, which is inside `#landing`. The old handler only handled the state shelf; on About, Abol Tabol, Account, a story, the map or the Hollow, `#landing` is hidden, so the scroll went nowhere. | New `goHomeTo()` (app.js): if home is not showing it routes home first, then scrolls. Also used by the "My Learning Journey" menu item. |
| **"Something went wrong" on My Learning Journey** | The dashboard ran four database reads together; any one failing (for example the optional artwork table, or a missing table) threw one generic error. Every non-network, non-permission error was shown as "Something went wrong". **I cannot see your live database, so I cannot tell you which request failed there.** The most likely causes are that `learning.sql` was never run, or stopped part-way (it is not safe to re-run). | Progress is the only strict read now; written answers, quiz results and artwork are optional and the dashboard still shows if they fail (it says what was left out). Errors are classified: missing table, expired session (one login refresh, then "Log in again"), permission, connection (one quiet retry). Technical detail goes to the browser console. New users get an empty state, not an error. |
| **Reading not reflected after returning from a story** | Dashboard state was loaded once at login. Progress was also only saved when a page was turned. | Opening a story now creates the "Currently Reading" record at the cover. The dashboard re-reads from the database whenever home is shown again, on tab focus and on back/forward. Pending saves are flushed when leaving the tab. |
| Signup | Frontend already creates a session when Supabase returns one. | Wording changed; a clear "already has an account" message. Needs the Supabase setting below. |
| Footer | Two placeholder lines. | Removed (nothing put in their place). |
| About "Who we are" | Generic text. | Your suggested text, plus one line saying the organisations have not endorsed or sponsored the site. **Please confirm that line and the named organisations are factually right.** |

## 2. Database steps (Supabase > SQL Editor), in this order
1. If not already run: `schema.sql`, `artwork.sql`, `learning.sql`, `community.sql`.
2. **`journey_repair.sql`** (new). Idempotent copy of `learning.sql`: safe to run even if `learning.sql` half-ran. First run the diagnostic queries at its top; a NULL result means that table was missing, which explains the Journey error.
3. **`abol_community.sql`** (new). Creates `abol_submissions`, two public views (published creatures/poems, no user id), the private `abol-art` bucket and its policies. Safe to re-run. Nothing existing is touched.
4. Make yourself an administrator (SQL editor only, never from the website):
   `update auth.users set raw_app_meta_data = coalesce(raw_app_meta_data,'{}'::jsonb) || '{"role":"admin"}' where email = 'you@example.org';` then log out and in. The review queue is at `#admin` ("Abol Tabol submissions").

## 3. Turn off mandatory email confirmation
Supabase dashboard > Authentication > Sign In / Providers (or "Providers" > Email) > turn **Confirm email** OFF > Save. With it off, `signUp` returns a session immediately and the site logs the person straight in. Leave it on and the old "check your inbox" screen still appears (the code handles both).

**Flag before production (children's site):**
- Anyone can register any address, including one they do not own, so an email address no longer proves who someone is. Impersonation of an existing account is still not possible (the address is taken), but a person can register someone else's address first and lock them out of it.
- With confirmation off, Supabase reports "User already registered" for an existing address. That reveals that an address has an account (the earlier setup hid this).
- Password reset still works, but is then the only proof of email ownership.
- DPDP Act: accounts are for adults who consent for each child; email confirmation was a weak but real check that the adult controls the address. Please take advice on whether verifiable parental consent can rest on an unverified email. Consider: a school- or teacher-managed account route, confirming email later (before the first story or artwork is submitted), CAPTCHA or rate limits on signup (Authentication > Rate limits), and a minimum password length of 8 or more (already enforced in the page; also set it in Supabase).

## 4. Abol Tabol submissions: how it works
- "Submit Your Creature" (name, drawing, optional description) and "Submit Your Crazy Poem" (title, poem text, optional picture and description). Login required. No real name asked for. Two ticks: an adult agrees to send it (required) and agrees it may be shown publicly (without which it can never be published).
- Stored in `abol_submissions` (id, user id, kind, title, description, poem text, image path, created time, status) and in the private `abol-art` bucket, 2 MB, JPG/PNG/WebP, file type checked by content, not only by name.
- Private until an administrator publishes. Public pages read only the views `published_abol_creatures` / `published_abol_poems`, which leave out user id and consent flags. Published pictures are served by signed URL from a copy under `published/`.
- Administrators can publish, reject, hide (take a published item off the site, which also removes the public picture copy) and delete. They cannot edit a child's words.
- Poems are labelled as reader poems, never as Sukumar Ray's. The old "invented characters from the book" line is gone; the four team drawings stay as "A few to get you started".
- Readers can see and withdraw their own pending submissions.
- Not built: edit-after-sending, per-item notes from the reviewer, e-mail notification, automated image or text moderation. Moderation is human only.

## 5. Tests actually run
Local mock backend (`dev/mock-gotrue.mjs`, `mock-community.mjs`, new `mock-abol.mjs`), Chrome via Playwright. Build with `SUPABASE_URL=http://localhost:54321 SUPABASE_ANON_KEY=x ALLOW_CUSTOM_SUPABASE_URL=1 node build.mjs`, run `node dev/serve.mjs`, then:
- `./dev/run_v3_test.sh`: 77 checks for this update (navigation from 9 views, instant signup, Journey progress and fresh data, error messages, footer, About, creature and poem submit, privacy, moderation, responsive overflow at 390 and 768 px).
- `./dev/run_learn_test.sh` and `./dev/run_community_test.sh`: earlier suites, re-run as regression checks.
The mock imitates the intended rules. **It does not prove the real SQL policies work.** Before launch: run the SQL on a staging Supabase project, then repeat the privacy checks with two real accounts and one admin.

## 6. Not tested
Real Supabase (SQL, RLS, Storage, signed URLs, Auth settings); real email; the Vercel deployment; Hindi wording; phones (only viewport widths were tested); screen readers; the 3D Hollow world beyond "Stories link works from it".
