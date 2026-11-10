# Kerala stories added (9 Nov 2026): what was checked, what needs a decision

## Stories
1. The Clever Jackal and the Foolish Leopard (ബുദ്ധിമാനായ കുറുക്കനും മണ്ടനായ പുലിയും)
2. A Friend in Need (ആപത്തിൽ സഹായിച്ച സുഹൃത്ത്)
Text (English, Malayalam, Romanized) is exactly as supplied. Hindi and Gujarati do not exist yet and are shown as "not yet available". Both are provisionally "Growing Sapling" (set by me from sentence length and vocabulary; please confirm). There is one level per story; no Seedling/Tree versions were invented.

## Web check of the sources (needs your follow-up)
- **Story 1, archive:** the Centre for Contemporary Folklore's Indian Folklore Archive does list "The Clever Jackal and the Foolish Leopard" under Kerala. The page carries "All Rights Reserved" and links Terms of Service I could not read. **Permission to adapt/publish is needed** (contact address is on the CCF page).
- **Story 1, book:** a book "Folk Tales of Kerala" by I. K. K. Menon (Publications Division, Ministry of I&B) is listed by a bookseller; another with the same title is by K. Jacob (Sterling, 1972). Your brief says "K. K. Menon". I could not confirm that this story is in either book. Check the physical book.
- **Story 2:** "A Friend in Need" (Malayalam) is in A. K. Ramanujan, *Folktales from India: A Selection of Oral Tales from Twenty-Two Languages* (Pantheon, 1991), p. 148 per the table of contents. **The CCF archive page does not list it**, so the attribution to CCF in your brief is not confirmed. A blog credits the storyteller as M. G. Shashibhooshan (unchecked). The anthology is a copyrighted book; check permission and how closely the retelling follows the published text.
- Malayalam and Romanized text: have a fluent reader check it. The Hindi word meanings in the vocabulary tooltips were written by me and need a fluent reader too (the page says so).
- I did not use search results about "kampikathakal" for the storytellers section; those pages are unreliable.

## Illustration briefs (nothing has been generated)
Proposed style, **awaiting editor confirmation**: inspired by Kerala mural painting, which traditionally uses five colours (red, yellow, green, black, white) from natural pigments, bold flowing outlines, and decorative borders. Murals traditionally depict mythological scenes, so applying the style to animal folktales is an adaptation: have a Kerala mural artist or art historian review the results, and do not imitate a named living artist. Label every AI-assisted image.
Prompt template: "Children's book illustration in the style of Kerala temple mural painting: flat bold colours in red ochre, yellow, green, black and white; strong flowing outlines; ornamental leaf border; [SCENE]. Warm, friendly, not scary. No text."
Scenes are stored in `stories_real.js` (`scenes[]`): Story 1: leopard frightening the forest; jackal finds the drum; BOOM; leopard runs away. Story 2: friends by the pond; leopard appears; fox has an idea; splash.

## What works on the story page (tested in a browser)
Reading-level indicator (other levels shown as unavailable), English/Malayalam/Romanized switching, Hindi/Gujarati shown as unavailable, curated vocabulary tooltips (hover, tap, keyboard, Esc), read-aloud for English and Malayalam when the device has a voice (Romanized is read-along only), Think/Imagine/Create questions, answers saved on this device only, picture preview with type/size checks (not uploaded), About the Storytellers, Sources & Acknowledgements with status labels, links to other stories. Not tested: real Malayalam voices on a phone.


## Storybook reader and illustrations (update)

- Full stories now open as a **storybook**: a cover that opens, then spreads with the picture on the left and the story on the right, turning like pages (single stacked page on phones; no 3D turn when the device asks for reduced motion). Next/Back, arrow keys, swipe and page dots all work.
- Reading level, language (English, Malayalam, Romanized), word help, Listen, Think/Imagine/Create, About the Storytellers and Sources are all kept.
- **Pictures** (`art.js`): original vector art drawn in code with AI assistance (Claude), 4 animated scenes per story. They use the five-colour palette associated with Kerala mural painting but are NOT traditional murals. Disclosed in the book credit line and in each story's Sources list ("Needs checking"). To do: review by a Kerala artist, or replace with commissioned art.
- Page splits per language are in `pages` in `stories_real.js`; they are editorial choices and can be changed.
- Tested in a desktop browser and at phone width, with a stand-in voice for Listen. Not tested with a real Malayalam voice on a real device.


## Bilingual storybook (update 2)

- Clicking a full-story book on the shelf flies the book to the centre, then the cover opens into a two-page spread: **English on the left, a second language on the right**. The right-page language chips list only languages that have a real translation (Malayalam, Romanized). A phone shows one page with an English / translation switch.
- Each spread is one story moment in both languages (`pages` in `stories_real.js`). Pages grow to fit their text. Pictures sit between paragraphs (left page full size, right page a smaller copy).
- **The Clever Jackal and the Foolish Leopard** uses the painting supplied by the project team (`site/img/cj1-4.jpg`, four crops, slow zoom only). Creator, tool and usage rights still need to be recorded in Sources. **A Friend in Need** still uses the vector art in `art.js`.
- Listen: choose English or the second language; the book turns the page and highlights the sentence being read. Close book returns to the shelf.

## Update 3 (English + Hindi only)
- The site now supports only English (left page) and Hindi / हिंदी in Devanagari (right page). Romanized text is removed everywhere; Malayalam is no longer shown. The original Malayalam text is archived in `docs/malayalam_original_archive.json`.
- Hindi for the two existing stories was translated from the English by Claude, paragraph for paragraph, and is **not yet reviewed by a fluent Hindi reader** (stated in each story's Sources). Hindi captions and titles are included.
- Removed from the website: the source rows "Permission to publish", "Illustrations", "Hindi and Gujarati versions" and the "Permissions" lines on sample listings. **These open questions still exist and are kept here:** (1) CCF archive page for "The Clever Jackal..." carries "All Rights Reserved"; permission to adapt/publish not obtained. (2) "A Friend in Need" comes from a copyrighted anthology; permission and closeness of the retelling unchecked. (3) The Clever Jackal pictures are a painting supplied by the project team; creator, tool and usage rights not recorded. (4) A Friend in Need pictures are vector art drawn in code with AI assistance, not reviewed by a Kerala artist. The book's credit line under each book still states how the pictures were made.

## Update 4: three reading levels for the two existing Kerala stories
- Stories: The Clever Jackal and the Foolish Leopard (`clever-jackal`) and A Friend in Need (`a-friend-in-need`). No other story was changed.
- Data: `REAL[id].levels = {1,2,3}` in `stories_real.js` (texts en/hi, vocab, questions). Level 2 (Growing Sapling) is the text the project team supplied, unchanged. Levels 1 and 3 were written by Claude from that same text. Every level has the same paragraphs in the same order, so pictures, page breaks and English/Hindi pairing are shared.
- Status: levels 1 and 3, and all new Hindi, are AI-written and NOT yet reviewed by an educator or fluent Hindi reader. Source permissions for the two original texts are still open (see earlier notes).
- UI: reading-level chips on the story page; switching keeps the book position and answers typed so far.
- Not done: the shelf and grove still list each story under Growing Sapling only.
