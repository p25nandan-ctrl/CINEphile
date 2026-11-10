# Kathaa Sangam: My Learning Journey (setup, safeguards, tests)

This update adds consent + child profiles, reading progress, recommendations, saved written answers, quizzes, an English learning score, artwork linked to a child, and an admin review panel. It extends the existing project; nothing is a new deployment.

## 1. What must be done before it works on the live site
1. Run, in the Supabase SQL editor and in this order: `supabase/schema.sql` and `supabase/artwork.sql` (if not already run), then **`supabase/learning.sql`** (new). It only adds tables/policies and one nullable column (`artwork_submissions.child_id`); it does not overwrite existing data.
2. Environment variables are unchanged: `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Vercel. Never add the service-role key (the build refuses it).
3. Auth redirect URLs and email templates: unchanged from `README.md` (the site URL and `/?auth=verified`).
4. Admin: an admin is a user whose `app_metadata.role` is `admin` (set in the Supabase dashboard, as for artwork review). Admins now also see a "Written answers to review" panel on `#admin`.
5. Copy `src/index.html` and `assets/` changes into the GitHub repo and push; Vercel redeploys the existing project.

## 2. How it works
- **Accounts are for adults** (parent, guardian or teacher). After verifying their email they accept a consent notice (stored in `consent_records`, versioned), then add child profiles: nickname (max 24), optional grade, reading level. No child email, full name, school or photo. Max 8 profiles per account. Deleting a profile removes its progress, answers and quiz results (cascade). Artwork already sent stays until a reviewer removes it (stated in the UI).
- Visitors can still browse and read everything. Login is needed to save progress, answers, quizzes, artwork and to see the dashboard.
- Grade suggests a level (4-5 Seedling, 6-7 Sapling, 8-10 Tree); the adult can change it at any time, and any level can always be read.
- **Progress** (`story_progress`): written when a signed-in child turns pages, per story and level, with page and timestamp. Opening the cover alone is not "reading". Completion is a button at the end ("I finished this story"). "Stories completed" counts distinct stories across levels.
- **Recommendations** are rules only: continue started stories, then unread stories in a region already read, then unread stories at the child's level, then a completed story at another level. Only stories that exist on the site. No AI.
- **Score (0-100)** only from evidence. Comprehension and Vocabulary come from auto-checked quiz questions (first try per question counts; at least 6 answers per dimension). Written expression and Critical thinking come only from an administrator's 0-4 rubric review of saved answers (at least 2 reviewed). Otherwise they show "awaiting review". Overall = average of the dimensions that have enough evidence. Bands: under 50 Developing, 50-74 Progressing, 75+ Confident, none = Not Yet Assessed. Level advice appears only after 8+ first-try answers across 2+ stories, and is a suggestion, never forced.
- No AI scoring was added. No child data goes to any AI service.

## 3. Honest limitations
- **Quiz answer keys ship in the page**, so a determined child could read them. Scores are formative guidance, not secure exams. The database prevents editing or deleting attempts and forging reviews, but cannot prove an answer was honestly chosen.
- **Quiz content is thin.** Vocabulary questions are auto-built from existing word lists; comprehension questions were authored (draft, needs teacher review) for only 4 new stories (Precious Present, Shabrang, Monkey and the Fox, Owl Princess). Other stories have fewer or no quiz items, so a score will take time to appear. Many stories have no "Think" questions yet, so there is nothing for an admin to review there.
- The consent text is a draft and **needs legal review** for the target jurisdictions (e.g. India's DPDP Act requirements on verifiable parental consent for under-18s) before real children use it.
- Supabase project settings still need a human check: email confirmation on, password rules, rate limits, backups.
- The Claude artifact preview has no database, so these features are hidden there; they work on the Vercel deployment.

## 4. Testing
Run `SUPABASE_URL=http://localhost:54321 SUPABASE_ANON_KEY=x ALLOW_CUSTOM_SUPABASE_URL=1 node build.mjs`, then `node dev/serve.mjs`, then `./dev/run_learn_test.sh` (restarts the mock backend, runs `dev/learn_test.py` with Playwright).

**What was actually executed:** 45 browser checks against `dev/mock-gotrue.mjs`, a local stand-in that imitates the intended RLS rules: the 17-step journey in the brief (signup/verify, consent, profile, dashboard, progress, resume, completion, answers, quiz, score, recommendations, artwork, shelf indicators, admin review, second child, logout/login) and unauthorised-access checks (another user cannot read or write a child's progress, answers, quizzes or artwork link; users cannot create or read reviews; quiz attempts are append-only; invalid values rejected; non-admin blocked from `#admin`). Result: 45 passed, 0 failed.

**What was NOT tested:** the real Supabase policies in `supabase/learning.sql`, real email delivery, real Storage, and the Vercel deployment. The mock reimplements the rules, so passing it does not prove the SQL is right. Before launch, run `learning.sql` on a staging Supabase project and repeat the unauthorised-access checks with two real accounts (use the same steps in `dev/learn_test.py`). Hindi text and the Hindi quiz/consent wording were not reviewed by a native speaker (the consent and dashboard are English only).
