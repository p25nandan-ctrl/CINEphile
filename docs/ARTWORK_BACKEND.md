# Share Your Artwork: how it works, and what is NOT yet proven

## What was built
- **Form** (end of every full story): picture (JPG/PNG/WebP, max 2 MB, type checked by file signature, not only the name), optional title (80 chars) and description (300 chars), and a required tick: "a parent, guardian or teacher says it is OK".
- **Storage**: private bucket `child-art`, path `{user id}/{random id}.{ext}`. No public URL. Reviewers get 5-minute signed links.
- **Database**: `public.artwork_submissions` (internal id, story id, storage path, type, size, optional text, consent flag, status pending/approved/rejected, created_at, reviewed_at, reviewed_by).
- **Rules** (`supabase/artwork.sql`, row-level security): a signed-in child can add one pending record for a file in their own folder and see only their own records; only an admin (`app_metadata.role = 'admin'`, set from the Supabase dashboard, never by the website) can read everything, approve/reject and delete. Anonymous users can do nothing. Nothing is ever public automatically, approved or not.
- **Review page**: `#admin` on the site. Shows a non-admin "administrators only". Lists submissions, shows the story that inspired each, a preview, and Approve / Reject / Delete buttons that report failure if a change was not saved.
- **No false success**: the thank-you message appears only after the file upload AND the record insert both succeeded. If the record fails, the uploaded file is deleted again (storage policy lets a child delete only an orphan file with no record).

## Authentication and protection (required before production uploads)
Uploads need a signed-in account (the Supabase email login already in the project). The account is the only identity kept; no name, school or address field exists. Before switching this on for real children you still need to decide, with the project's legal/school contacts:
1. Parental/school consent: the tick-box is a prompt, not verified consent. Under-13 accounts may need verifiable parental consent (India's DPDP Act 2023 requires verifiable parental consent for under-18s' personal data; confirm with counsel).
2. Who may be an administrator and how their accounts are protected (use MFA on the Supabase dashboard).
3. A retention and deletion policy, and a way for parents to ask for removal.
4. Moderation: reviewers should check pictures for personal information before approving anything for any future public use.

## Test status
- Tested with a local stand-in server (`dev/mock-gotrue.mjs`, `dev/art_test.py`): the upload/insert/rollback/approve flow and the UI messages. **The stand-in only imitates the rules.** The real Postgres policies in `artwork.sql`, real Storage limits and real signed URLs have NOT been tested. Run `schema.sql`, then `artwork.sql`, create a test child and a test admin, and repeat the flow before launch.
- Setup: Supabase > SQL Editor: run `schema.sql` (for `is_admin()`), then `artwork.sql`. Make an admin: `update auth.users set raw_app_meta_data = coalesce(raw_app_meta_data,'{}'::jsonb) || '{"role":"admin"}' where email='reviewer@example.org';` then have them log out and in.
- The Claude artifact preview has no database, so there the section honestly says sharing is not switched on.
