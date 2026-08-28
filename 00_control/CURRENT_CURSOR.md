# Production cursor

Updated: 2026-08-28

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
  `b08693e28595bf51814c3cbd6654223f024cb22512b07e849a557e73a27dd328`;
  deterministic QA receipt SHA-256
  `d12c9dcb4293de0ec929cc2d2c330e197d936a86e17e27adc20dede10bef15db`.
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
  `02583cecceba1db5f8a9f7561f567ebd98585c441a6e4cae5ba1ef92f8710d6e`.
- Complete translation ledger: fourteen data rows / 5,821 bytes / SHA-256
  `c5ba07e250360af2a97957aa957278f43348c05bb44a208a2a2898fc6b034660`.
- Complete terminology glossary: 192 data rows / 20,340 bytes / SHA-256
  `554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Current public archive: corrected Zenodo record `22105616`, DOI
  `10.5281/zenodo.22105616`, version `2026.08.26.14of14-r1`, in concept record
  `22077422` / concept DOI `10.5281/zenodo.22077422`. All nine files /
  55,312,500 bytes matched by anonymous readback; the final concept audit found
  one submitted matching version and zero drafts. The source package binds the
  canonical 8,203-byte LF findings file.
- Current GitHub/Pages boundary: content commit
  `13767f55f739ad7dd058fc1dcb55cf5334ab097c`, tree
  `dbf8abf4f729ddca46f69547bcf38d0b71f27f07`, successful run `32930770236`,
  tag/release `v2026.08.26.14of14`. Anonymous readback matched 746 commit-tree
  blobs / 154,064,493 bytes, 106 Pages files / 17,614,553 bytes, and nine
  release assets / 55,312,500 bytes.
- Public checkpoint receipt SHA-256 values: GitHub commit/Pages
  `de0a44ae013f72198b32948a3c5b7f245cdefd2cdeffd902dba615cfb770f752`;
  GitHub release
  `e3b620272dff1b40f5d2ae8d3707e5e8a57940771f93c22ccd87c7a153052e17`;
  corrected Zenodo publication
  `11a047fc561e1e27f31b3bc800d9de1cf5e78b2e63001ec18563efb7c5ad5cf1`;
  anonymous Zenodo readback
  `a386fa3539d0366d8890669ddfeaff1853fab10f90c2f24533c0242887897c41`;
  final lineage audit
  `e476b7bb1b447478db30cb6954b6c6cda179cc255923d0bffb7a08eab39f3f92`;
  lineage pointer
  `80689f675838b69be6636680eb0fef1c3ff8b01fb07386b752c3b4a4620cfe90`.
- No upstream message has been sent.

## Next executable action

Commit and push the release-ready consolidated-reader source and receipts,
then publish the 17-file union under GitHub tag
`v2026.08.28.14of14-pdf-epub` and Zenodo version
`2026.08.28.14of14-pdf-epub` in the existing concept. The primary PDF is 219
pages / 20,170,549 bytes / SHA-256
`f39c1c438cc3e793fe9522eb11f5b02704d89fcdc7aecb2207a599087d458964`;
the EPUB is 12,301,415 bytes / SHA-256
`e122d65348971b91a5ac0c7a8219e0fa3e0eabedb92d130c661648e399e3c574`.
The ordered union is 17 files / 87,848,426 bytes and its package-receipt
SHA-256 is
`934f9484dd7fd25a2436c80914c68d9627ba4009da07900a975e168d91d01694`.
After anonymous byte-and-hash readback and sanitized receipt persistence,
begin the distinct exact Random completeness donor and then the original C140
companion. Do not launch any browser process and do not send an upstream
message.

## Recovery

Read `00_control/WORKFLOW.md`, this file, `CURRENT_STATE.md`,
`CHECKPOINT_2026-08-26_THROUGH_LESSON12_LF_REPAIR.md`,
`COMPONENT_BOUNDARY.md`, the fourteen-document authority manifest/freeze
receipt, `TRANSLATION_LEDGER.csv`, `ADVERSE_LEDGER.jsonl`, the final glossary,
`build/LESSON12_MATERIALIZATION_RECEIPT.json`,
`build/THROUGH_LESSON12_BUILD_RECEIPT.json`,
`build/THROUGH_LESSON12_QA_RECEIPT.json`, and
`build/THROUGH_LESSON12_VISUAL_QA_RECEIPT.json`,
`build/CONSOLIDATED_PDF_QA_RECEIPT.json`,
`build/CONSOLIDATED_PDF_VISUAL_QA_RECEIPT.json`,
`build/CONSOLIDATED_EPUB_BUILD_RECEIPT.json`,
`build/CONSOLIDATED_EPUB_QA_RECEIPT.json`,
`build/CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json`,
`build/CONSOLIDATED_READERS_PACKAGE_RECEIPT.json`,
`CHECKPOINT_2026-08-26_THROUGH_LESSON12_PUBLICATION_COMPLETE.md`, the complete
GitHub checkpoint/release receipts, the three LF-repair Zenodo receipts, and
`ZENODO_LINEAGE.json`. Conversation summaries are not state. Do not broaden
the filesystem or Git scope.
