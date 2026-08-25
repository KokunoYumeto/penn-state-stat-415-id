# Production cursor

Updated: 2026-08-26

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, id-ID.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete locally: landing/index plus Lessons 00–09, 11 of 14
  documents and 3,458 admitted segments.
- Structure and mathematics: 4,775 normalized source units, 4,763 derivative
  units, and 2,171 protected mathematics surfaces. Every intentional target
  removal is registered; all other topology is preserved.
- Corrections: 170 target-only proved repairs, ordered
  `O006-PSU-ADV-0001` through `O006-PSU-ADV-0170`. Authority bytes remain
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
- Cumulative reader: 71 files / 8,551,979 bytes; manifest SHA-256
  `fa29f2df5f34e441d976280696ef2433845a65fe4ec478674346e56e2f50ffc8`.
- Deterministic build-receipt SHA-256:
  `00199cebee641d78b09e8aab1b1c7ac8c687fdad93dca848444d698bc20443a1`.
- Deterministic QA-receipt SHA-256:
  `431f74cc685b73220ae7559d0299bec5e08b1637d239c901dd31280503878db3`.
  Write and check-only replays pass.
- Deterministic nine-file reader-first release package passes write/check-only
  replay. Exact non-self-referential identities are in
  `build/THROUGH_LESSON09_PACKAGE_RECEIPT.json` and the release root receipt.
- Desktop/mobile visual QA passes all twelve routes at 1,280 × 720 and
  390 × 844. All 2,171 math surfaces render, all 34 substantive figures are
  centered and full-width, mobile code/table reflow is internal, and console
  warning/error logs are empty. Visual-QA receipt SHA-256:
  `fa3ffb355a15dbeb50da1651037c1a66e85eba87617864427981ed4c9338006d`.
- Eleven-row translation ledger SHA-256:
  `b951e2260b5b0ba2100e8ffab7fd2a8a96674f2e18481a71bb233104563900b2`.
  Adverse-ledger SHA-256:
  `d45a8f458d64e1c64c185b8f27beb7dafdef6e7d0abb8286d1729a5da398090b`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Last public archive: Zenodo DOI `10.5281/zenodo.22097348`, concept DOI
  `10.5281/zenodo.22077422`. Last compact GitHub/Pages checkpoint: commit
  `abbadb33755be935e0b5753313f3c2967b0994e0`, run `32866078986`.
- No upstream message has been sent.

## Next executable action

Commit and push the exact cumulative source/backend/reader boundary, wait for
the Pages workflow, then anonymously verify the commit tree, all 71 Pages
files, the release tag and every release asset. Publish the same nine release
files as a new version of the existing Zenodo concept and anonymously read back
the public inventory and bytes. Do not create another concept.

Immediately after the public boundary is closed, continue contiguously with
Lesson 10: normalize and audit its exact frozen authority, then translate its
complete segment ledger in source order. Do not reopen Lessons 00–09 except to
repair a proved release or deterministic-replay defect.

## Recovery

Read `00_control/WORKFLOW.md`, this file, `CURRENT_STATE.md`,
`COMPONENT_BOUNDARY.md`, the fourteen-document authority manifest/freeze
receipt, `TRANSLATION_LEDGER.csv`, `ADVERSE_LEDGER.jsonl`, the final glossary
rows, `build/THROUGH_LESSON09_BUILD_RECEIPT.json`,
`build/THROUGH_LESSON09_QA_RECEIPT.json`,
`build/THROUGH_LESSON09_VISUAL_QA_RECEIPT.json`, and the latest package/public
verification receipts. Conversation summaries are not state. Do not broaden
the filesystem or Git scope.
