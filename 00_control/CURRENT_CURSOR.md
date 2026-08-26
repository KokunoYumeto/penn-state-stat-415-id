# Production cursor

Updated: 2026-08-26

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, id-ID.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete locally: landing/index plus Lessons 00–10, 12 of 14
  documents and 3,998 admitted segments.
- Structure and mathematics: 5,400 normalized source units, 5,388 derivative
  units, and 2,540 protected mathematics surfaces. Every intentional target
  removal is registered; all other topology is preserved.
- Corrections: 198 target-only proved repairs, ordered
  `O006-PSU-ADV-0001` through `O006-PSU-ADV-0198`. Authority bytes remain
  unchanged.
- Lesson 07: 237 segments / 399 units / 148 math / two assets / twelve
  corrections; target 74,079 bytes, SHA-256
  `d5714697191c3530be7183ee15a8ae3dffda87596338eadb293ac58c0d1cb440`.
- Lesson 08: 291 segments / 604 source units / 594 derivative units / 156 math
  / four assets / 28 code surfaces / seventeen corrections; target 113,208
  bytes, SHA-256
  `d902c11f06ed884d3124596c9c178e87dbd993063b65c454176e73c96b4d3daf`.
- Lesson 09: 443 segments / 414 units / 219 math / ten assets / three semantic
  tables / nineteen corrections; target 95,275 bytes, SHA-256
  `539cf8f248e654ccb70bf12c98318ece8ac9de7281ae1f1ea5bb3d364d134f64`.
- Cumulative reader through Lesson 10: 94 files / 17,020,141 bytes; manifest
  SHA-256 `08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663`.
- Deterministic build-receipt SHA-256:
  `0f440e56bf71e172815ac0933e752e3f3f12383573e4c501db8fe5aa1922a520`.
- Deterministic QA-receipt SHA-256:
  `6bc589012a12e93d9418fe9f26029ca8b58b6de61235a4d6181114afa2300180`.
  Write and check-only replays pass.
- Deterministic nine-file reader-first 12-of-14 release package passes
  write/check-only replay: 49,769,118 bytes, 94 reader files, and 432 bounded
  source entries. Exact identities are in
  `build/THROUGH_LESSON10_PACKAGE_RECEIPT.json`; its self-hash is deliberately
  excluded from the source closure to keep the package non-circular.
- Desktop/mobile visual QA passes index, Lessons 00–10, and licenses at
  1,280 × 720 and 390 × 844. All 2,540 math surfaces render, all 56
  substantive figures are centered and full-width, mobile code/table reflow is
  internal, and console warning/error logs are empty. Visual-QA receipt
  SHA-256: `7c1377982b1cadbd7dbd69de84a63d8bbeb6df0961758c5c8e52f25cc1fc75a5`.
- Twelve-row translation ledger now resolves Lesson 10; merged Lesson 10
  translation SHA-256 is
  `27305c36d540f63db6dbf925de6caa93dc544fbc0268a863979ac410edad0b51`.
  Cumulative correction backend SHA-256 is
  `2450673f606d7a308dd7490cd811f81dcd3c42cc382b1eefe2b21d3dbb2f2032`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Current public archive: Zenodo DOI `10.5281/zenodo.22103203`, concept DOI
  `10.5281/zenodo.22077422`; all nine files / 30,362,116 bytes matched by
  anonymous readback and the final concept audit found one submitted matching
  version and zero drafts.
- Current GitHub/Pages boundary: commit
  `57170f9f7d914f3d13c716d19818ec64c3896df5`, tree
  `d94da2ca46268c1d93201e036d91d38132228669`, run `32906124668`, tag
  `v2026.08.26.11of14`. Anonymous readback matched 526 commit files, 71 Pages
  files, and nine release assets.
- Lesson 10 normalization passes: 540 segments / 625 units / 369 math / 22
  assets; normalization-receipt SHA-256
  `aa2dc59fb4720458742986fa71ab15ba95cba30424fb176052c3e562c6bd38e0`.
- Lesson 10 complete: four canonical batches S0001–S0540 merged, corrected,
  built, and QA-verified. The target is 153,768 bytes, SHA-256
  `8fb91a9fc5ef0b5a163767aec5e760d19c3e56f6c3dee35ee58323d6c45359c5`.
- No upstream message has been sent.

## Next executable action

Package the verified 12-of-14 reader and compact source/backend evidence, push
the dedicated GitHub repository and Pages, publish the next version in the
existing Zenodo concept, and anonymously verify every public byte. Do not ask
for another authorization. Then translate Lessons 11 and 12 contiguously,
reusing the same stable-ID/backend/build/QA workflow and preserving the public
12-of-14 boundary unless a proved defect requires a correction.

## Recovery

Read `00_control/WORKFLOW.md`, this file, `CURRENT_STATE.md`,
`COMPONENT_BOUNDARY.md`, the fourteen-document authority manifest/freeze
receipt, `TRANSLATION_LEDGER.csv`, `ADVERSE_LEDGER.jsonl`, the final glossary
rows, `build/THROUGH_LESSON10_BUILD_RECEIPT.json`,
`build/THROUGH_LESSON10_QA_RECEIPT.json`,
`build/THROUGH_LESSON10_VISUAL_QA_RECEIPT.json`,
`build/THROUGH_LESSON10_PACKAGE_RECEIPT.json`, and the latest package/public
verification receipts. Conversation summaries are not state. Do not broaden
the filesystem or Git scope.
