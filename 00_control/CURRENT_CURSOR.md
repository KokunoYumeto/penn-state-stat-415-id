# Production cursor

Updated: 2026-08-25

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, `id-ID`.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete locally: landing/index plus Lessons 00–03, 5 of 14
  documents and 1,599 admitted segments.
- Structure and mathematics: 1,399 normalized source units, 1,397 derivative
  units, and 1,149 protected mathematics surfaces. The two removed Lesson 00
  units are registered source defects; all other topology is preserved.
- Corrections: 46 target-only proved repairs—14 first unit, 6 Lesson 01, 9
  Lesson 02, and 17 Lesson 03. Authority bytes remain unchanged.
- Lesson 03 authority: 118,925 bytes; SHA-256
  `26dd4efe75abc879a5316c215eaedbfe713c77e742898eb86e7f3d88cb0c04c9`.
  Deterministic normalization emits 531 segments, 421 units, 440 mathematics
  nodes, zero assets, and 1,393 catalogue records; receipt SHA-256
  `693b5fbb2b410567e0c81e2232e46ad159a9958605b691b2badbd2f4b08d5fc6`.
- Lesson 03 translation: 531/531 audited segments; receipt SHA-256
  `d120e1d1b8248070450a4e3d314a890e4b38b199faab364ce525638038676bc6`.
  An independent computed-output replay found zero blanks, English leakage,
  terminology violations, ordering failures, or formula/text boundary defects.
- Lesson 03 target HTML: 102,473 bytes; SHA-256
  `85e9f7356c756435a251a54094f1c723bfb9efc0aae6eb3cec904b3f0654b9de`.
- Cumulative offline reader: 32 files / 2,804,159 bytes; manifest SHA-256
  `15e979bbd3b791b0a7d2a25873e9450030c5a1b7019455982b84e0dac6287831`.
- Deterministic build receipt SHA-256:
  `4ffb6a9963cc7581139a8f5123225b5fd3c6dc7fc8792f60dc0414bf1b371246`.
- Deterministic QA receipt SHA-256:
  `262b4143aecc4f4c546adcb5aaf7fec13832f071a2d5a5e43009a8a3204f7eda`.
- Responsive visual-QA receipt: 6,042 bytes; SHA-256
  `f80ba6dc59e3ce4e869950b3b6175b75af5affb4a445a3f1881a129fba3f34f7`.
  At 1280×720 and 390×844, all six routes use `reader-5of14.css`, have
  no page/navigation overflow, render exactly 1,149 mathematics surfaces, load
  all twenty images, and emit zero fresh warning/error logs. Lesson 03 units
  U0127 and U0140 were visually inspected and are centered, legible, and
  unclipped.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Last public checkpoint remains 3 of 14 at commit
  `4a1182fc9bd5a86942da5f7be6539f4dbf048921`, GitHub tag
  `v2026.08.24.3of14`, and Zenodo version DOI `10.5281/zenodo.22083156`
  inside concept DOI `10.5281/zenodo.22077422`. The 5-of-14 local boundary is
  release-ready but not yet publicly claimed.
- No upstream message has been sent.

## Next executable action

Commit and push the exact release-ready 5-of-14 boundary, verify GitHub commit
bytes, Pages routes, and all 32 manifest files anonymously, then publish the
same substantial checkpoint in the existing GitHub/Zenodo lineages and verify
the public bytes. Continue with Lesson 04 in source order without reopening
completed documents.

## Recovery

Read `WORKFLOW.md`, this file, `CURRENT_STATE.md`, `COMPONENT_BOUNDARY.md`,
`CHECKPOINT_2026-08-25_THROUGH_LESSON03.md`, `TRANSLATION_LEDGER.csv`, and the
Lesson 03 normalization/translation/build/QA/visual receipts. Conversation
summaries are not state. Do not broaden the filesystem or Git scope.
