# Community features: setup, rules and tests

Covers: Abol Tabol collection, Share Your Story, Stories From Our Readers, Voices From Our Readers (testimonials), and the removal of Union Territories from public browsing.

## 1. What was built

| Feature | Where | Status |
|---|---|---|
| Abol Tabol collection | `#abol`, nav link, home section | Built. **0 poems published** (see section 3). |
| Share Your Story | `#share`, nav link, home section | Built; needs `supabase/community.sql` run once. |
| Stories From Our Readers | `#readers`, `#readers/<id>` | Built; empty until an admin publishes a story. |
| Voices From Our Readers | home section `#voices` | Built; **hidden until an admin approves a real testimonial. 0 testimonials exist.** |
| Admin review | `#admin` (existing page, two new panels) | Built: stories and testimonials. |
| Union Territories | map, lists, search, counts | Removed from public browsing; records kept. |

## 2. Deploy steps

1. Existing environment variables stay as they are (`SUPABASE_URL`, `SUPABASE_ANON_KEY`). No new keys. Never add the service-role key.
2. In Supabase > SQL Editor run, in this order: `schema.sql` (already done), `artwork.sql` (already done), `learning.sql` (already done), then **`community.sql`**. It only adds: tables `user_stories`, `testimonials`; views `published_user_stories`, `published_testimonials`; bucket `story-art`; a trigger and storage policies. It changes nothing that exists.
3. Administrators are the same as for artwork review (`app_metadata.role = 'admin'`, set only in the Supabase dashboard).
4. Deploy as before (`npm run build`). New files: `assets/abol/*.svg`.

**`community.sql` has NOT been run against a real Supabase project.** Please run it in a test project first, then repeat the checklist in section 5.

## 3. Abol Tabol: content and copyright

What the page says (all checked against sources on 10 Nov 2026): Abol Tabol is Sukumar Ray's Bengali nonsense-verse collection, first published 19 September 1923 by U. Ray and Sons; Ray died 10 September 1923; he wrote and drew for *Sandesh*, started by his father Upendrakishore Ray Chowdhury; his son was the filmmaker Satyajit Ray; the book has stayed in print.

**Poems published: 0.** Reasons:
- The site is English and Hindi only. No verified English or Hindi version of any poem has been supplied, and the brief forbids inventing translations.
- Original Bengali text: under the Indian Copyright Act 1957 a literary work lasts for the author's life plus 60 years (a posthumous first publication is 60 years from publication), so the 1923 originals are out of copyright in India. This is a summary, not legal advice, and other countries differ. Please have your legal adviser confirm before relying on it.
- Modern translations are **protected and must not be copied** without permission: e.g. Satyajit Ray (1970), Sukanta Chaudhuri (OUP, 1987), Sampurna Chattarji (Puffin, 2004), Niladri Roy (*Rhymes of Whimsy*, 2017/2020). Ray's own illustrations and the illustrations in modern editions are checked separately and are **not used**.
- The collection cover and four creatures are **original drawings made for this site**. They are labelled on the page as not being Sukumar Ray's drawings or characters.

### Adding an Abol Tabol poem
Edit `abol_poems.js` (the header explains the record). A poem is shown only if `verified: true` and every field in `source` is filled in (work, author, first published, text checked against, who made this version, why we may use it, who verified it, when). Incomplete records are ignored, not shown. Line breaks and stanza breaks are kept exactly as typed (one array per stanza, one string per line); indentation is preserved. Hindi is optional; "Side by side" appears only when English and Hindi have the same number of stanzas. Then rebuild (`bash build_k.sh`, copy to `src/index.html`, `npm run build`).

Audio: the Listen button uses the browser's built-in voices (English or Hindi) and is disabled when the device has no voice for that language. No recorded audio exists.

## 4. Safety rules built into Share Your Story

- Login required. Form: title, story (20 to 8000 letters), English or Hindi, optional state (28 states only, or none), optional inspiration, optional picture (JPG/PNG/WebP, 2 MB, type checked by file signature).
- Two **separate** consent ticks: (1) a parent/guardian/teacher agrees the story may be sent to the team (required); (2) they also agree it may be shown publicly if chosen (optional). An admin cannot publish without tick 2 (database constraint and disabled button).
- No name, school or community is asked for. The public page shows no author identity, no user ID and no state unless the child chose one. Published stories are labelled "by a reader", never "folktale".
- Confirmation is shown only after the row is saved. If saving fails, the uploaded picture is removed and no success message appears.
- Statuses: `pending`, `revision_requested`, `approved`, `published`, `rejected`. Only an admin can set `approved`, `published` or `rejected`; a reader editing their own story always sends it back to `pending`. Admins cannot rewrite a child's words (trigger).
- Anti-spam: at most 5 stories waiting per reader. No comments, no messaging.
- Readers see only their own stories, with status and the admin's note. They can edit (while pending or changes requested) or withdraw (unless published).
- Publishing copies the picture to a `published/` folder in the private bucket; unpublishing deletes that copy.

## 5. Real-Supabase checklist (not done yet)
- Run `community.sql`; confirm no error.
- Sign in as a reader: submit a story with and without a picture; confirm the row appears as `pending`.
- Confirm a second reader cannot see it; confirm an anonymous `select` on `user_stories` returns nothing.
- As admin: request changes, approve, publish (with consent), then open `#readers` while logged out and confirm only the published story (and its picture) shows; unpublish and confirm it disappears.
- Confirm `published_user_stories` returns no `user_id`.
- Testimonials: add one as admin, approve it, confirm it shows on the home page while logged out; confirm a child's testimonial cannot be approved without permission.

## 6. Union Territories
Removed from every public browsing surface: home map (selection, tooltip, pins), state list, "All 28 states" tile, featured-story filter chips and search index, story-map page (selectable regions, chips, random pick, search), the 3D world (no UT trees, no UT jump-list entries), the sources list, homepage copy.
The UT outlines stay on the maps as plain, non-clickable geography (map files unchanged).
Preserved, not deleted: records are moved into `UT_ARCHIVE` (`ut.js`).

**Flagged for your decision.** Eight UT shelf records were hidden: Andaman and Nicobar Islands, Chandigarh, Dadra and Nagar Haveli, Daman and Diu, Delhi, Jammu and Kashmir, Lakshadweep, Puducherry (Ladakh had no record). All were short placeholder listings, but **two have real story text and quizzes that are now not reachable by readers**: *Shabrang* and *The Precious Present* (Jammu and Kashmir). Their data is intact in `UT_ARCHIVE.stories`. Old links to them now open the home page. Reader progress already saved for these two stories is kept in the database but is not shown. Decide whether to keep them hidden, or to re-home them (for example as a separate "Stories from Kashmir" note) if you want.

The 28 states: Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal.

The Hollow (3D world) library was rebuilt with `esbuild` to skip trees for UT outlines (`w3/hollow.js`, backups `hollow.bak9.js`, `hollow.bundle.bak9.js`). The 3D scene itself was not rendered in the automated test (no GPU); only its data and list were checked. Please look at it once in a real browser.

## 7. Tests run (local mock only)
Start: `SUPABASE_URL=http://localhost:54321 SUPABASE_ANON_KEY=x ALLOW_CUSTOM_SUPABASE_URL=1 node build.mjs`, `node dev/serve.mjs`, then `sh dev/run_community_test.sh` (104 checks: states, Abol Tabol, submissions, moderation, testimonials, responsive widths 390/768, JavaScript errors) and `sh dev/run_learn_test.sh` (45 checks).
The mock (`dev/mock-gotrue.mjs`, `dev/mock-community.mjs`) imitates the intended rules. **It is not a test of the real database policies.**
`dev/learn_test.py` was pointed at two visible stories (it used the two hidden Kashmir stories); the old `dev/art_test.py` predates the consent dialog and is superseded by step 11 of the learning test.
The Abol Tabol reader was tested with a clearly fake fixture inserted by the test only (not shipped), to prove line and stanza structure is kept.

## 8. Still needed
- Genuine testimonials with permission (none exist, so the section is hidden).
- Verified English/Hindi versions of Abol Tabol poems, with the source record; legal confirmation of the copyright position; any permission for modern translations or illustrations.
- A parent/guardian consent wording review by your legal adviser (same as the earlier consent text).
- The new pages (Abol Tabol, Share Your Story, Readers) are written in English only; readers can submit stories in Hindi. A Hindi version of this page text would need a native-speaker review.
- Running `community.sql` and the checklist in section 5 on a real project.
