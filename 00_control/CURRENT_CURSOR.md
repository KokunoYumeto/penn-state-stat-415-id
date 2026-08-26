# Production cursor

Updated: 2026-08-26

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, id-ID.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete locally: landing/index plus Lessons 00–11, 13 of 14
  documents and 4,352 admitted segments. Lesson 12 is the only pending source
  document.
- Structure and mathematics: 5,664 normalized source units, 5,652 derivative
  units, and 2,804 protected mathematics surfaces. Every intentional target
  removal is registered; all other topology is preserved.
- Corrections: 218 target-only proved repairs, ordered
  `O006-PSU-ADV-0001` through `O006-PSU-ADV-0218`. Lesson 11 contributes the
  contiguous suffix `O006-PSU-ADV-0199` through `O006-PSU-ADV-0218`.
  Authority bytes remain unchanged.
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
- Cumulative reader through Lesson 11: 96 files / 17,232,761 bytes; manifest
  SHA-256 `026ac69ce34ceb77d3174ff167621043bd9ff5d2e5ce82124b8bec3faf365173`.
- Deterministic build-receipt SHA-256:
  `421d60b88849d9f800d4dc1691d28e59f01c86ac4d892c01f797d7114ee4b98d`.
- Deterministic QA-receipt SHA-256:
  `d715c53a6bd48992a1bca49937adfbdf917f38c7ac1c864b76d52c0e9e104f39`.
  Asset-freeze, normalization, merge, build, and QA check-only replays pass.
- The currently public nine-file reader-first 12-of-14 release package passes
  write/check-only replay: 49,769,118 bytes, 94 reader files, and 432 bounded
  source entries. Exact identities are in
  `build/THROUGH_LESSON10_PACKAGE_RECEIPT.json`; its self-hash is deliberately
  excluded from the source closure to keep the package non-circular.
- Desktop/mobile visual QA passes index, Lessons 00–11, and licenses at
  1,280 × 720 and 390 × 844. Fourteen routes and all 77 referenced local
  resources return HTTP 200; all 2,804 math surfaces render; all 57
  substantive images load; all eight tables remain inside the reader; the
  Lesson 11 portrait is centered/full-width; and console warning/error logs
  are empty. Visual-QA receipt SHA-256:
  `4b7644108b5423c83ec049c6710622c1605dc4b46901c9fae9c579a1a4a1e5bc`.
- The 5,417-byte, thirteen-row translation-ledger prefix through Lesson 11 has
  SHA-256
  `d674909cce4e6ed9a144eda1808fff6634f1b0d91748df94241dfedd6a278a2f`;
  merged Lesson 11 translation SHA-256 is
  `1b54aa89f765f3befbd9464d4382aa68551f7278947a06d01621fd26b632c20c`.
  Cumulative correction backend SHA-256 is
  `699377a938dcd9a2336d3d69b2d4258b3358db3f8f3beabb24f666c396c1b53a`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Current public archive: Zenodo DOI `10.5281/zenodo.22104074`, concept DOI
  `10.5281/zenodo.22077422`; all nine files / 49,769,118 bytes matched by
  anonymous readback and the final concept audit found one submitted matching
  version and zero drafts.
- Current GitHub/Pages boundary: commit
  `a342a4cf4de7464f42d6a3f2aa97bfcdf66293a1`, tree
  `0f399d4efef53c29f5e0123a7febf8eb2305f869`, run `32917215255`, tag
  `v2026.08.26.12of14`. Anonymous readback matched 611 commit files, 94 Pages
  files, and nine release assets.
- Lesson 11 normalization passes: 354 segments / 264 units / 264 math / one
  table / one asset; normalization-receipt SHA-256
  `448773792cfad18d52fb883d3dba4a298d5271948fdbedd2d9e01d7d2a70cdd4`.
- Lesson 11 asset: one 142,195-byte PNG preserved byte-for-byte, SHA-256
  `2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22`;
  asset-freeze-receipt SHA-256
  `2d128b3d4b4635aa45855b8d5ba82cbec408f139a1ac51bcddcbd7682221f3e2`.
- Lesson 11 complete: three canonical batches S0001–S0354 merged, corrected,
  built, and QA-verified. The target is 69,861 bytes, SHA-256
  `70a954496254cf26abd8d28317d45ac1bc945ed2551dd4a6b0eb902ae78e8002`;
  translation-receipt SHA-256
  `fc920cee18729d0e775e7e8cad922163af9a4d50f2ef4826a4c79395a615a374`.
- The admitted Lesson 11 glossary prefix contains 168 decisions through
  `O006-TERM-0168`; its first 17,727 bytes have SHA-256
  `1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65`.
- No upstream message has been sent.

## Next executable action

Package and publish the validated local 13-of-14 reader in the existing GitHub
and Zenodo lineages, then anonymously verify the public commit, Pages reader,
release assets, Zenodo files, and concept lineage. Continue immediately with
Lesson 12—the only pending source document—preserving all structure,
mathematics, assets, attribution, stable IDs, and proved target-only correction
records. Do not replace or discard the public 12-of-14 evidence.

## Recovery

Read `00_control/WORKFLOW.md`, this file, `CURRENT_STATE.md`,
`CHECKPOINT_2026-08-26_THROUGH_LESSON11_LOCAL_COMPLETE.md`,
`COMPONENT_BOUNDARY.md`, the fourteen-document authority manifest/freeze
receipt, `TRANSLATION_LEDGER.csv`, `ADVERSE_LEDGER.jsonl`, the final glossary
rows, `authority/LESSON11_ASSET_FREEZE_RECEIPT.json`,
`build/LESSON11_NORMALIZATION_RECEIPT.json`,
`build/LESSON11_TRANSLATION_RECEIPT.json`,
`build/THROUGH_LESSON11_BUILD_RECEIPT.json`,
`build/THROUGH_LESSON11_QA_RECEIPT.json`, and
`build/THROUGH_LESSON11_VISUAL_QA_RECEIPT.json`. For public state, read the
latest package/public verification receipts. Conversation summaries are not
state. Do not broaden the filesystem or Git scope.
