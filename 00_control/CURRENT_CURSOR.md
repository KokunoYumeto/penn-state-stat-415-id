# Production cursor

Updated: 2026-08-26

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, id-ID.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation and reader complete: landing/index plus Lessons 00–12, all 14
  documents and all 4,932 segments.
- Complete structure: 6,510 normalized source units / 6,498 derivative units /
  3,156 protected source-mathematics surfaces. Every target removal or repair
  is registered and all other topology is preserved.
- Corrections: 242 target-only records, exactly ordered
  `O006-PSU-ADV-0001` through `O006-PSU-ADV-0242`; cumulative backend SHA-256
  `2b709bfe05dce6aa84c67513f1679faac0d1c38da987509a558b1dbba1cb0837`.
  Authority bytes remain unchanged.
- Lesson 12: 580 segments / 846 units / 352 protected math surfaces / nine
  frozen image files in ten occurrences / six captioned scoped tables / three
  expanded offline video equivalents / 24 correction records. Target SHA-256
  `6cd3218f6d1a613f1ea9d1459c5506ea8b24f37340a3ee26f17bc18504dd5965`;
  translation receipt SHA-256
  `5514555698cd07737d12e3b91e440af9f9302dc32de5df49716c8b532f248364`.
- Complete reader: 106 files / 17,614,553 bytes; manifest SHA-256
  `697c9ee8e23cc10469fea4d1894e16471ffb4276edd1f0d25bebfb5be0dbe79e`.
- Build receipt SHA-256
  `d7bae677a7d93023322773806a96418b3d96af19bae39bfd5fe967c327d01954`;
  deterministic QA receipt SHA-256
  `44a0fd8e432f81da65776b45f33cccda0e462db32bb04bf8ecdb6d11eeca5560`.
  All write/check-only replays pass.
- Cross-platform repair: `working/lesson12_source_findings.md` is canonically
  LF at 8,203 bytes / SHA-256
  `8b087fb8e545f14ba323afd1caa5672117d60878c3c5924a0b0455136078109c`;
  scripts and downstream receipts no longer bind the obsolete 8,209-byte CRLF
  identity. The complete CI command chain passes locally and the reader bytes
  and manifest are unchanged.
- Visual QA passes fifteen routes at 1,280 × 720 and 390 × 844: 86/86 local
  resources, 3,156 protected MathJax containers, 67 images, 14 tables, zero
  `merror`, broken images, iframes, console warnings/errors, or page/navigation
  overflow. Visual receipt SHA-256
  `2fe1f40b8748b0dcc67e08e6a87e6ba402b5323b581744f73e35c787ae583d5f`.
- Complete translation ledger: fourteen data rows / 5,821 bytes / SHA-256
  `c5ba07e250360af2a97957aa957278f43348c05bb44a208a2a2898fc6b034660`.
- Complete terminology glossary: 192 data rows / 20,340 bytes / SHA-256
  `554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Current public archive: Zenodo record `22105226`, DOI
  `10.5281/zenodo.22105226`, in concept record `22077422` / concept DOI
  `10.5281/zenodo.22077422`. All nine files / 55,308,347 bytes matched by
  anonymous readback; the final concept audit found one submitted matching
  version and zero drafts. One corrected source-reproducibility version must
  supersede it in the same concept after the repaired GitHub gate because the
  immutable package predates the six-byte LF binding repair.
- Current GitHub/Pages boundary: commit
  `8222b6a84cc7592ddfce16dabcbc392533fa50eb`, tree
  `03887f51eaba4357bf997b1db2691f46f6c47105`, successful run `32923342205`,
  tag/release `v2026.08.26.13of14`. Anonymous readback matched 668 commit-tree
  blobs / 150,369,151 bytes, 96 Pages files / 17,232,761 bytes, and nine
  release assets / 51,832,274 bytes.
- Public checkpoint receipt SHA-256 values: GitHub commit/Pages
  `d6e1918a8f3b888ec3eecfa27d0d876a2541792aa1fddfbe0dd57e82b2970d26`;
  GitHub release
  `cd61daa5633890738efed0a57773c4fe385aba87df4a66b59ed7273ee01a12f7`;
  Zenodo 14-of-14 publication
  `e7b96fa525e416cf49d332eafb701b9f91797e298654c768bec09f02891d9b1e`;
  anonymous Zenodo readback
  `b2db8839ca366d03bef9387b2266bd57d5cc4288c94835ec6ca8ebb020299db0`;
  final lineage audit
  `c5b88758ca760e778fd90e7c8196821a454a5dc9ecc7ca3cc43dfbe7af09b826`.
- No upstream message has been sent.

## Next executable action

Commit and push the repaired deterministic 14-of-14 boundary, wait for the
exact GitHub/Pages workflow to pass, publish tag/release
`v2026.08.26.14of14`, and anonymously verify commit, Pages, release, and every
public byte. Rebuild the same reader-first package with the repaired source
identities, publish one corrected version in existing Zenodo concept
`22077422`, and anonymously verify it. Then produce and validate the
consolidated PDF/EPUB surfaces before beginning the distinct exact Random
completeness donor and original C140 companion.

## Recovery

Read `00_control/WORKFLOW.md`, this file, `CURRENT_STATE.md`,
`CHECKPOINT_2026-08-26_THROUGH_LESSON12_LF_REPAIR.md`,
`COMPONENT_BOUNDARY.md`, the fourteen-document authority manifest/freeze
receipt, `TRANSLATION_LEDGER.csv`, `ADVERSE_LEDGER.jsonl`, the final glossary,
`build/LESSON12_MATERIALIZATION_RECEIPT.json`,
`build/THROUGH_LESSON12_BUILD_RECEIPT.json`,
`build/THROUGH_LESSON12_QA_RECEIPT.json`, and
`build/THROUGH_LESSON12_VISUAL_QA_RECEIPT.json`, and the three through-Lesson12
Zenodo receipts. Until the repaired 14-of-14 GitHub and corrected Zenodo
transactions are complete, preserve the through-Lesson11 GitHub receipts and
record `22105226` as the last independently verified public states.
Conversation summaries are not state. Do not broaden the filesystem or Git
scope.
