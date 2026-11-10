# Kathaa Sangam: AI feasibility, admin workflow and functionality audit
Written 9 Nov 2026. Prices and free tiers change often and several figures below come from third-party summaries of vendor pricing pages. **Re-check the vendor page before committing.**

## 1. Done this round
- **Quests and Games removed.** Nav links "Games" and "Quests" are gone, as is the "Play Quests" tile and the "Create" nav link (it only showed a "coming soon" message). The India map section stays because it is not a quest. Homepage tiles are now Read Stories, Listen to Stories, Story World, Explore India. No game-specific components or state existed beyond these, so there was nothing further to delete.
- **Listen to the story is real.** It uses the browser's built-in speech (no paid API). See section 3.
- **Hollow buttons removed** from the story popup: "Read side by side", "Think about it" and "Draw it" only displayed "coming next", so they were taken out until built.

## 2. AI illustration generation: options
Recommended workflow (matches your 8 steps): admin pastes story, picks art style and scenes, prompts are prepared and **stored with the story**, images are generated **once**, an admin approves each image, then approved files are stored and shown to children. Nothing is generated when a child opens a story.

| Option | Cost / free limit | API | Commercial / public site | GPU or server | Quality and cultural fit | Student-project reliability |
|---|---|---|---|---|---|---|
| **Cloudflare Workers AI, FLUX.1 [schnell]** | 10,000 "neurons"/day free, shared across the account; above that $0.011 per 1,000 neurons. A 512x512, 4-step image is about 43 neurons per Cloudflare's published rates, so dozens to hundreds of images/day are possible within the allowance depending on size and steps. Free-plan requests fail once the daily limit is hit. | Yes (REST / Workers) | FLUX.1 schnell weights are Apache 2.0. Also read Cloudflare's own service terms. | None (hosted) | Good general quality, fast. Weak on specific folk-art idioms and on text in images. Needs careful prompts and human review. | Good for a prep-time, admin-only tool. Do not call it from the public page. |
| **Google Gemini API image models** | No free API tier for the image models on Google's pricing page as reported in 2026; paid about $0.04 per image for the 2.5 Flash Image model (reported Feb 2026). AI Studio can be used manually for testing. | Yes (paid) | Check Google's terms | None | Strong quality and prompt following | Reliable but not free |
| **Hugging Face Inference Providers** | Free accounts get about $0.10/month of credit (subject to change): only a handful of images | Yes | Depends on model licence. FLUX.1 [dev] is non-commercial; [schnell] is Apache 2.0 | None | Same models as above | Credits run out fast |
| **Open-source locally (FLUX.1 schnell, SDXL)** | Free software. FLUX.1 schnell is Apache 2.0; SDXL uses the OpenRAIL++ licence with use restrictions. FLUX.1 [dev] is non-commercial, so avoid it | Self-run (ComfyUI / diffusers) | Yes for schnell | A recent GPU (roughly 12 GB+ VRAM, or quantised models on less) or a rented/free notebook GPU with its own usage limits | Can add a style LoRA, but only train on art you have permission to use | Fully under your control, but needs someone technical |
| **Manual: generate in any tool, admin uploads** | Whatever that tool costs | No | Check that tool's terms for public/commercial use | None | Same as the tool | Most reliable. This is the fallback and is built into the plan below |

**Cultural accuracy.** No general model reliably reproduces a specific regional tradition (for example Warli, Madhubani, Pattachitra, Gond or Kalamkari). Each story needs a verified community context first, then a named art style chosen with a regional or art-history reviewer, then human approval of every image. Do not train or prompt on a living artist's work without their permission. Every AI image carries an "AI-assisted" credit on the Sources page.

**Recommendation.** Build the admin tool with a pluggable generator: (a) Cloudflare FLUX.1 schnell if you create a free Cloudflare account, (b) paste-in / upload of images made elsewhere. Both store prompt, style, generator and reviewer. Do not promise unlimited free generation.

## 3. Listen to Story
**Built (Option 1, browser text-to-speech):** English, Hindi and Gujarati chips appear only when the story has text in that language, and Play is enabled only when the device actually has a matching voice; otherwise it explains what is missing. Play, Pause/Resume, Restart, speed 0.75x/1x/1.25x, tap a sentence to jump, highlighted sentence, loading and error messages. It reads sentence by sentence to avoid the roughly 15-second cut-off some Chrome voices have.

**Known limits.** Voices differ by device: Chrome on Android lists voices unreliably, Edge on Android exposes none, Firefox for Android has no speech synthesis, and iOS needs a tap to start (we start on a button press). Hindi and especially Gujarati voices may be missing or poor on some phones. This cannot be fixed in code, which is why Option 2 exists.

**Option 2, pre-generated audio.** Cloud TTS services (for example Google Cloud Text-to-Speech) charge per character with a monthly free allowance (reported as 4M characters for Standard voices and 1M for WaveNet/Neural2/Chirp voices; about $4 to $30 per million characters after that). Rough size: 56 stories x 3 levels x 3 languages is about 500 files; at about 3,000 characters each that is roughly 1.5M characters (so about one free month for Standard voices, or a few dollars on premium voices). At 48 to 64 kbps mono the files total around 1 GB, so store only approved audio and consider fewer levels. Check that the chosen service has a Gujarati voice and that its terms allow publishing the audio. Human recording is the highest quality and the highest effort.

**Plan.** The player already accepts `b.audio = {en:"url.mp3"}` in the story data model (hook reserved). Pre-recorded files can be added later without redesigning the pages.

## 4. Admin content management (proposal)
Goal: add 56 stories without exposing admin tools to children.
- **Stage A (usable immediately, no custom UI):** the Supabase table editor plus `supabase/schema.sql` (proposed, not yet run). Tables: stories, story_texts (language x level), vocab, questions, sources, illustrations, audio. Admin = a user whose `app_metadata.role` is `admin`, which only you can set in the Supabase dashboard. Row-level security shows the public only stories with `published = true` and illustrations with `status = approved`.
- **Stage B (small custom page, after Stage A is verified):** an `/admin` page that checks the role on the server (like `/api/me`), with forms for each section, a preview, a checklist (state, three levels, English and Hindi, vocab, questions, sources, storytellers, approved illustrations) and a Publish toggle that is blocked until the checklist is complete.
- Not exposed to ordinary users: the admin page and write policies require the admin role on the server; hiding a button is not relied on.

## 5. Functionality audit
Legend: **F** fully functional, **C** functional but needs external configuration, **P** prototype/placeholder, **X** not built, **R** removed.

| Element | Status | Notes / what is needed |
|---|---|---|
| Nav: Stories, Story Map, About, search, menu | F | |
| Login / Sign Up / Logout / Forgot / Reset / Account page | C | Works on the Vercel project once Supabase is configured. On the published artifact the buttons only show a message. Tested only against a local fake auth server, not real Supabase |
| Homepage tiles, Grow With Stories | F | |
| Story selection: map pins, state list, atlas, Story World (3D), state shelves | F | 3D world is heavy for low-end phones |
| Story search | F | Searches title, subtitle, state, description. It searches sample descriptions, not full story text |
| State filter chips (homepage rail) | F | |
| Reading-level filter (state shelves) | F | Filters the sample listings. No story has three level versions yet |
| **Reading-level switching inside a story** | X | Needs three texts per story (schema ready) |
| **Language switching for reading** | X | Only the Listen player has language chips. Needs per-language texts |
| **Vocabulary tooltips** | X | Phase 2: curated entries per story |
| **Listen to Story** | F (device-dependent) | Reads the sample summary today. Reads full text once added. Needs a device voice per language |
| Story popup: About the Storytellers, Sources & Acknowledgements | P | Fields say "To be verified / To be added". Need verified research |
| Sources & Acknowledgements page | P | Structure real; no sources recorded yet |
| Footer attribution | P | Needs exact CINE wording |
| **AI illustration generation** | X | Story covers are generic SVG artwork, not story-specific. Needs admin tool + generator (section 2) |
| **Written responses, artwork upload, "my submissions"** | X | Needs Supabase tables/storage with RLS (schema proposed), file limits, moderation and parental/school consent |
| **Saving reading progress** | X | Needs a progress table tied to the logged-in user |
| Games, Quests, Create nav, "Read side by side", "Think about it", "Draw it" | R | Removed because they only displayed messages |

**Biggest gap:** all ~120 stories are sample listings with no story text. Until real, verified stories are added, reading levels, translations, vocabulary, listening to the full story, questions and illustrations have nothing to work on.
