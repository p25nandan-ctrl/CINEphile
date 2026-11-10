# Kathaa Sangam: story content spec (read fully before writing)

You write ONE JSON file per assigned story into /home/claude/content/stories/<id>.json (create the folder if missing).
Do NOT edit any other file. Do not touch the website. Validate with:  python3 /home/claude/content/validate.py /home/claude/content/stories/<id>.json  and fix every error before you finish.

## Source
/home/claude/content/src/repo_clean.txt is the project team's story repository (a cleaned text export of a PDF). Your story's line range is given in your task. Also read the state's introduction lines (just before the first story of that state) for context and source notes. The text may still contain small PDF artefacts (stray "Centre for Contemporary Folklore (CCF)+1" chips, "Read the source story." fragments, photo-caption lines, "Moral:", "Source:" lines). Story text = the lines under "The story" / "English", up to the "Moral:" or "Source" line. Everything else is source/context material.

## The reference level (the supplied story)
- The supplied English text is the REFERENCE version. Decide which of the 3 levels it most closely matches (1 Little Seedling, grades 4-5; 2 Growing Sapling, 6-7; 3 Mighty Tree, 8-10) from vocabulary, sentence length and structure, and say why in "levelReason". Do not assume level 2.
- Keep the supplied text as that level's English, WORD FOR WORD. You may only: repair PDF artefacts (broken dropped capitals, stray spaces, odd quote marks), and join or split lines into paragraphs. Never reword it, never "improve" it.
- If the story ends with a "Moral:" line, keep it as the last paragraph of the story at every level (rewritten for each level). Interpretive/editorial notes go in about/sources, not in the story.
- Then write the OTHER TWO levels from it. Same characters, setting, order of events, conflict, cultural details, ending and message. No new characters, subplots or endings. Change only the language: vocabulary, sentence length/structure, descriptive depth, emotional depth. Do not just shorten/lengthen. Do not change culturally significant details to make things easier.
- Level targets: L1 = very simple words, short sentences (about 6-8 words average), short paragraphs. L2 = varied sentences, connectors, moderate vocabulary (about 9-12 words average). L3 = richer vocabulary, complex sentences, atmosphere, emotional depth (about 12-16 words average), opportunities for interpretation.
- ALL THREE LEVELS MUST HAVE EXACTLY THE SAME NUMBER OF PARAGRAPHS, paragraph i telling the same moment at every level, so pictures and pages line up. Merge several very short supplied lines into one paragraph if needed (a story of 25-45 paragraphs is typical; keep each paragraph under ~70 words at level 3).
- Hindi: for EVERY level write the Hindi (Devanagari only, no Roman letters at all, no transliteration) as the same number of paragraphs, natural child-friendly Hindi at that level's difficulty, same events and ending as the English at that level. Keep names of people/places/gods as natural Devanagari spellings. No word-for-word translation.

## Pages and pictures
- "pages": list of spreads; each spread = a list of paragraph indices (0-based, consecutive, covering every paragraph exactly once, in order). Choose breaks at natural narrative moments. Keep each spread to at most ~120 English words at level 3 (so most stories need 5-12 spreads; 2-4 paragraphs per spread).
- "scenes": exactly one per spread: {"t": short English caption (3-8 words), "th": the same caption in Hindi, "p": a detailed illustration prompt for that exact narrative moment}. Prompts: describe characters, setting, action, mood, with the SAME consistent character look across all scenes. Child-appropriate; no gore. No generic "Indian" clichés; no invented art-tradition claims.
- "artStyle": {"region": "...", "verified": true|false, "tradition": "name of a traditional visual art associated with this state/community, ONLY if you verified it with a reliable source (use WebSearch/WebFetch); otherwise null", "note": "one or two sentences on the visual style to use (palette, shapes, clothing/architecture details you verified); say plainly if no specific tradition could be verified and a neutral storybook style is proposed", "characters": [{"name": "...", "look": "consistent description"}], "sources": [["title","url"]]}. We cannot generate images here, so these prompts will be used later; do not claim any image exists.

## Vocabulary (per level)
8-12 entries per level: {"w": word exactly as it appears in that level's English text (one word, same spelling), "en": simple English meaning (a child at that level can read it), "hi": Hindi meaning in Devanagari}. Choose genuinely useful/challenging words for that level; each must appear in that level's English paragraphs (word-boundary match). No proper nouns unless truly needed.

## Questions (per level): exactly 5: {"k": short label, "q": the question}
- L1: basic comprehension, characters and events, feelings, a personal connection.
- L2: character motivation, cause and effect, decisions and consequences, interpretation.
- L3: an ethical question, another point of view, cultural understanding, interpretation of theme, connection to contemporary life.
Story-specific. Different questions at every level. Child-safe wording; do not ask children to disclose private/family details.

## Other fields
- "imagine" and "create": one imagine prompt and one create prompt (draw/write) specific to the story.
- "summary": if an existing summary is given in your task, use it EXACTLY and set "summarySource":"existing". Otherwise write 1-2 plain sentences (max 40 words) from the repository's blurb/story and set "summarySource":"written for this site".
- "titleHi": Hindi (Devanagari) title.  "from": short provenance label like "Tamil folktale, Tamil Nadu" (only what the sources support).  "genre": e.g. "Folktale", "Origin myth", "Animal fable", "Ballad/legend".
- "about": {"where": ..., "community": ..., "tradition": ..., "shared": ..., "matters": ..., "links": [["title","url"], ...]}. Child-readable, warm, factual. Use reliable sources (WebSearch/WebFetch). Say only what sources support; if the community is not named in the sources, say "The sources we have do not say which community first told this version, so we are not guessing." Never stereotype. Mention that this is one version from one source, not the only one. 2-4 sentences per field.
- "sources": list of {"l": label, "v": value, "s": "ok"|"check", "url": optional, "n": optional note}. Include: the repository's original source (author/collector, book, publisher, year, URL where given), the repository itself ("English text supplied by the project team in the CINE Story repository (G1)"), adaptation credit ("Levels X and Y written for this website by Claude (an AI assistant) from the supplied version; not yet reviewed by an educator"), translation credit ("Hindi translations by Claude (an AI assistant); not yet reviewed by a fluent Hindi reader"), and copyright/licence status as far as you can verify ("Licence not confirmed: permission from the rights holder should be checked before public launch" if unknown; never claim a licence you did not see). Mark unknown things "check".
- "reviewFlags": list of short strings for anything a human must verify (uncertain facts, sensitive content, unclear source, mixed attributions, translation worries).
- Sensitivity: handle caste, religion, violence, death, childhood loss, and tribal/community material respectfully and accurately; keep the supplied events; do not add stereotypes.

## JSON shape (exact keys)
{
 "id": "kebab-case-id (given)", "state": "code (given)", "title": "exact supplied title", "titleHi": "...",
 "summary": "...", "summarySource": "existing|written for this site", "genre": "...", "from": "...",
 "origLevel": 1|2|3, "levelReason": "...",
 "levels": {"1": {"texts": {"en": [..], "hi": [..]}, "vocab": [..], "questions": [..]}, "2": {...}, "3": {...}},
 "pages": [[0,1],[2,3,4],...], "scenes": [{"t","th","p"},...],
 "artStyle": {...}, "imagine": "...", "create": "...",
 "about": {...}, "sources": [...], "reviewFlags": [...]
}
Use straight JSON (UTF-8, no comments). Use curly quotes “ ” ’ inside text for dialogue/apostrophes to avoid escaping trouble.
