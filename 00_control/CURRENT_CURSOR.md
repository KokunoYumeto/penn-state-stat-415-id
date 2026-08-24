# Production cursor

Updated: 2026-08-24

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, `id-ID`.
- Frozen corpus: landing/index plus Lesson 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete: landing/index plus complete Lesson 00 and Lesson 01,
  3 of 14 documents and 744 of 744 admitted segments at this boundary.
- Structure and mathematics: 750 normalized source units, 748 derivative units,
  and 500 math surfaces. The two removed Lesson 00 units are registered source
  defects; all other topology is preserved.
- Lesson 01 translation CSV: 54,021 bytes; SHA-256
  `f7c6cc3c2089f1e3f0fb500dddd93b803cb2c63007b30349a41e88c9d52e9eeb`.
- Lesson 01 target HTML: 47,205 bytes; SHA-256
  `0766b844ddbe2733e82a466fc05ffc69a9f9b4b6ff6d3b98581ad29bab3e24d1`.
- Cumulative offline reader: 28 files / 2,598,449 bytes; manifest SHA-256
  `6a047b981eeb71e740450678b4f802fb7ec3eb954cf92ffc3cebbaf8a050b5a7`.
- Deterministic build receipt SHA-256:
  `ae926ca4f9a3d0d1723b059fbc578365bfd5fc704521a7a990b98bdd4bc4a1c2`.
- Deterministic QA receipt SHA-256:
  `3143ff7a9f8127d76370c52e93567e74b1fa328c52f0916d31eb59a9f3a4548f`.
- Desktop/mobile visual QA receipt SHA-256:
  `74fc753f0191adfcc6545c3bf728c7feaba0f67ad2b5cf76b213fd871521401a`.
  All three routes fill the available content width, have no page-level
  horizontal overflow, and render all 500 mathematics surfaces without fresh
  console errors or warnings.
- Hardened reader-first release: 9 files / 7,150,601 bytes; package-receipt
  SHA-256
  `923629a84df45f74404159efe6b007e2fe457924397e593e6c5f7bb268049dcd`.
  The reader ZIP SHA-256 is
  `8e69e971eb44f318772e80ca22a759d97499e16d306d6172a676d79f3446bcfc`;
  the 86-file explicit source/backend ZIP SHA-256 is
  `740fa491a223e0e8b6b01e21a06124ed9e38c734fcec3d74fc065f6c26888f40`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- No upstream message has been sent.

## Next executable action

Commit and push this verified 3-of-14 checkpoint, verify the deployed 28-file
reader anonymously, publish the nine exact assets as a new version of the
existing Zenodo concept `10.5281/zenodo.22077422`, and anonymously read every
published byte back. Then normalize and translate Lesson 02 without reopening
completed documents.

## Recovery

Read `WORKFLOW.md`, this file, `CURRENT_STATE.md`, `COMPONENT_BOUNDARY.md`,
`CHECKPOINT_2026-08-24_THROUGH_LESSON01.md`, `TRANSLATION_LEDGER.csv`, the
source/runtime/asset freeze receipts, and the latest cumulative
build/QA/visual/package/publication receipts. Conversation summaries are not
state. Do not broaden the filesystem or Git scope.
