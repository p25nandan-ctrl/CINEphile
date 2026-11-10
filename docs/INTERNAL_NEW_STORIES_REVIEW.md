# INTERNAL — new-story integration review (not shown on the site)

Covers the 32 stories added from the story repository (28 in CINE_Story_repository__G2.pdf, 2 Kashmir, 2 Assam). Nothing here is displayed publicly.

## What was done
- 32 stories placed on their state shelves (see STORY_INVENTORY.md). Four existing placeholders were updated in place, not duplicated: Puran Bhagat (Punjab), Dhola and Maru (Rajasthan, now "Dhola–Maru"), Panna Dhai (Rajasthan), Sammakka and Saralamma (Telangana). No new states.
- Every story has three reading levels, English left and Hindi right, synchronised pagination, vocabulary hook, audiobook, Sources and About the Storytellers.
- Illustrations stored under `assets/stories/<story-id>/` as WebP. Descriptive file names and alt text. The same pictures are reused at all three levels.

## Content NOT supplied, left empty (not invented)
- **Vocabulary tooltips: none supplied for any of the 32 stories.** Tooltips are therefore absent. The Kashmir and Assam files contain glossary notes in prose only, with no Hindi meanings in the tooltip format.
- **Critical-thinking questions, Imagine and Create prompts: none supplied.** The Think, Imagine and Create section and the end-of-book button are hidden for these stories.
- **About the Storytellers:** only the facts in the repository are shown (where, community, tradition). "How stories were shared" and "Why it matters" are not shown.
- Per-story summaries on the shelf use the repository's one-line description.

## Source and rights items to resolve (internal only)
- Rights/permissions for the supplied illustrations and for the reading-level text are not confirmed. Public credit is the neutral line "Illustrations supplied with the story repository."
- Published retellings (e.g. E-Pao for the Manipur elephant story) are retellings, not primary oral sources.
- **Nwai, Chethuang, The Race between Teesta and Rangeet** are creative adaptations of a documented premise or title, not retellings of an original text. Sources lines say so.
- Folk Tales of Assam: the repository's own notes say the specific tale-to-community mapping is a reading, not a confirmed attribution; ikashmir.net page names S. L. Sadhu but gives no publisher or year.
- Ka Pah Syntiew and Mount Sophet Bneng come from a 1920 colonial-era English retelling.
- Dharmapada and Sivai Santara: legends, not established history (stated in Sources).
- Possible overlap to check: "Sammakka" and "Sammakka and Saralamma" (two shelf books); "The Tiger and the Man" (Nagaland, new) versus the existing placeholder "Tiger, Spirit and Man" (not merged because the titles differ and no mapping was supplied).
- **Sensitive themes for a child audience:** Chethuang (supplied heading "A Story of Forbidden Love", kinship boundaries) and Puran Bhagat. Reviewer decision needed on age placement; the supplied text was not altered.

## Hindi
- Hindi text was extracted from PDFs whose Hindi glyph order was unreliable; it was reconstructed programmatically and has **not been reviewed by a native reader.** A native-speaker proof is still required.
- Repairs made to extraction damage (displaced anusvara/chandrabindu/virama and broken words) in: bonobibi-and-shah-jangali, chawngtinleri, shabrang, the-clever-hare, the-egotistical-elephant-and-the-praying-pebet, the-magic-ring, the-monkey-and-the-fox, the-precious-present. The Chawngtinleri king's name was normalised to "लालचुंगनुंगा" to match the English "Lalchungnunga".
- The supplied Hindi for the Manipur pebet story contained stray virama marks ("पे ्बेट"); these were removed.
- Hindi level titles differ between levels in the repository for 21 stories; the site shows the level's own title (English and Hindi pair) when the level changes.

## Pagination
- Paragraph counts differ between English and Hindi in these levels (paged by proportion, so spreads still match in number):   - chawngtinleri level 2: 19 English vs 18 Hindi paragraphs
  - dharmapada level 2: 10 English vs 11 Hindi paragraphs
  - licha-ba level 3: 30 English vs 29 Hindi paragraphs
  - shabrang level 3: 14 English vs 15 Hindi paragraphs
  - the-clever-hare level 1: 25 English vs 26 Hindi paragraphs
  - the-clever-hare level 3: 26 English vs 27 Hindi paragraphs
  - the-clever-jackal-up level 1: 13 English vs 14 Hindi paragraphs
  - the-clever-jackal-up level 3: 12 English vs 25 Hindi paragraphs
  - the-crow-and-the-sparrow level 1: 31 English vs 30 Hindi paragraphs
  - the-crow-and-the-sparrow level 3: 38 English vs 37 Hindi paragraphs
  - the-four-fairies level 1: 11 English vs 12 Hindi paragraphs
  - the-legend-of-mount-sophet-bneng level 3: 9 English vs 8 Hindi paragraphs
  - the-magic-ring level 3: 39 English vs 41 Hindi paragraphs
  - the-match-making-jackal level 2: 14 English vs 13 Hindi paragraphs

## Illustrations
- 28 stories have **one** composite illustration each. It appears on the first spread (both pages) only; later spreads are text-only. If you want one picture per spread, more artwork is needed.
- Four images were cropped to remove book mock-up edges and an empty caption box: Tiger and the Man (g-077), Licha Ba (g-085), Fyoli (g-187), Ghughutiya (g-194). The Dhola–Maru image has two empty banners left in the artwork; Ghughutiya's original had red label strips in its side panels.
- Kashmir and Assam: 7 panels each, cropped from the storyboard sheets so the printed English captions are not shown; alt text uses the sheet's captions.
- Not used: a third storyboard sheet in the Kashmir file ("The Burglar's Gift", held in reserve in the repository) and two wide strips at the end of the G2 file ("The Tale of the Cat's Daughter", etc.) that match no story in the list.

## Database
- No Supabase change is needed: stories are static content in the page. No migration was written and no database was touched.
