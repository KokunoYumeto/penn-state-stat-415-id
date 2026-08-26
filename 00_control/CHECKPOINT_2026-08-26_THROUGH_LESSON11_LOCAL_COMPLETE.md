# Local production checkpoint — cumulative edition through Lesson 11

Date: 2026-08-26
Status: deterministic build, QA, and browser QA complete; 13-of-14 public release next

## Frozen authority, asset, and translation

- Official boundary: landing/index plus Lessons 00–12, fourteen documents,
  1,604,869 frozen authority bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Lesson 11 authority: 99,359 bytes, SHA-256
  `4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32`.
- Lesson 11 normalization: 354 translation segments / 264 stable units / 264
  math surfaces / seven examples / one table / four code nodes / one asset.
  Receipt: 8,194 bytes, SHA-256
  `448773792cfad18d52fb883d3dba4a298d5271948fdbedd2d9e01d7d2a70cdd4`.
- Lesson 11 asset: one 142,195-byte PNG, frozen and copied byte-for-byte at
  SHA-256
  `2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22`.
  Asset-freeze receipt: 1,062 bytes, SHA-256
  `2d128b3d4b4635aa45855b8d5ba82cbec408f139a1ac51bcddcbd7682221f3e2`.
- All 354 translation segments are complete. Merged translation CSV: 86,242
  bytes, SHA-256
  `1b54aa89f765f3befbd9464d4382aa68551f7278947a06d01621fd26b632c20c`.
  Translation receipt: 3,264 bytes, SHA-256
  `fc920cee18729d0e775e7e8cad922163af9a4d50f2ef4826a4c79395a615a374`.
- Lesson 11 target: 69,861 bytes, SHA-256
  `70a954496254cf26abd8d28317d45ac1bc945ed2551dd4a6b0eb902ae78e8002`.
- Translation provenance: `OpenAI Codex gpt-5.6-sol, Ultra`.

## Corrections, build, and QA

- Twenty proved Lesson 11 target-only repairs are registered contiguously as
  `O006-PSU-ADV-0199` through `O006-PSU-ADV-0218`; authority bytes remain
  unchanged. The cumulative correction count is 218.
- Cumulative coverage: 13 of 14 documents; 4,352 segments; 5,664 normalized
  units; 5,652 derivative units; 2,804 math nodes.
- Offline reader: 96 files / 17,232,761 bytes.
- Manifest: 10,290 bytes, SHA-256
  `026ac69ce34ceb77d3174ff167621043bd9ff5d2e5ce82124b8bec3faf365173`.
- Build receipt: 8,116 bytes, SHA-256
  `421d60b88849d9f800d4dc1691d28e59f01c86ac4d892c01f797d7114ee4b98d`.
- QA receipt: 7,503 bytes, SHA-256
  `d715c53a6bd48992a1bca49937adfbdf917f38c7ac1c864b76d52c0e9e104f39`.
- Visual receipt: 17,818 bytes, SHA-256
  `4b7644108b5423c83ec049c6710622c1605dc4b46901c9fae9c579a1a4a1e5bc`.
- Asset freeze, normalization, translation merge, cumulative build, and QA
  check-only replays pass. Deterministic QA covers all 354 Lesson 11 source ↔
  target bindings, the exact stable-unit/math order, only five registered math
  changes, all 20 new correction records, the byte-preserved portrait, table
  semantics, code/runtime disclosure, locale/provenance/navigation metadata,
  privacy, offline closure, and the exact 96-file inventory.
- Browser QA covers the landing page, Lessons 00–11, and licenses at 1,280 ×
  720 and 390 × 844. Fourteen routes and 77 referenced local resources return
  HTTP 200; all 2,804 math surfaces render; all 57 substantive images load;
  all eight tables remain within the reader; no page/navigation overflow or
  fresh console warning/error is present.
- Cumulative correction backend: 313,335 bytes, SHA-256
  `699377a938dcd9a2336d3d69b2d4258b3358db3f8f3beabb24f666c396c1b53a`.
- Translation-ledger prefix through Lesson 11: thirteen rows / 5,417 bytes,
  SHA-256
  `d674909cce4e6ed9a144eda1808fff6634f1b0d91748df94241dfedd6a278a2f`.
- Glossary prefix through `O006-TERM-0168`: 168 rows / 17,727 bytes, SHA-256
  `1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65`.

## Release boundary and next cursor

The validated 13-of-14 boundary is locally complete. The next authorized
operation is one reader-first release in the existing GitHub repository and
Zenodo concept, followed by anonymous commit, Pages, release-asset, Zenodo-file,
and concept-lineage verification. The currently public 12-of-14 release remains
valid evidence until that transaction completes. No upstream contact has
occurred. After publication, continue immediately with Lesson 12, the only
pending document. The independent Random edition remains a separate component
and is not copied here.
