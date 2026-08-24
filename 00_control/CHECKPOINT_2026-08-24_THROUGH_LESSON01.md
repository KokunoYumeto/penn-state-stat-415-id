# Checkpoint — cumulative edition through Lesson 01

Date: 2026-08-24
Status: release-ready; public transaction pending

## Exact scope

- Complete documents: `index`, `Lesson00`, `Lesson01` (3 of 14).
- Next document: `Lesson02`.
- Translation: 744 segments; all admitted segments complete.
- Structure: 750 normalized source units / 748 derivative units.
- Mathematics: 500 protected surfaces (331 Lesson 00; 169 Lesson 01).
- Corrections: 20 registered and applied (14 first-unit; 6 Lesson 01).
- Reader: 28 files / 2,598,449 bytes.
- Reader manifest: `build/THROUGH_LESSON01_MANIFEST.csv`, 2,798 bytes,
  SHA-256
  `6a047b981eeb71e740450678b4f802fb7ec3eb954cf92ffc3cebbaf8a050b5a7`.

## Deterministic evidence

- Build receipt: `build/THROUGH_LESSON01_BUILD_RECEIPT.json`, 7,122 bytes,
  SHA-256
  `ae926ca4f9a3d0d1723b059fbc578365bfd5fc704521a7a990b98bdd4bc4a1c2`.
- QA receipt: `build/THROUGH_LESSON01_QA_RECEIPT.json`, 9,610 bytes,
  SHA-256
  `3143ff7a9f8127d76370c52e93567e74b1fa328c52f0916d31eb59a9f3a4548f`.
- Visual-QA receipt: `build/THROUGH_LESSON01_VISUAL_QA_RECEIPT.json`,
  5,403 bytes, SHA-256
  `74fc753f0191adfcc6545c3bf728c7feaba0f67ad2b5cf76b213fd871521401a`.
- Package receipt: `build/THROUGH_LESSON01_PACKAGE_RECEIPT.json`, 4,434 bytes,
  SHA-256
  `923629a84df45f74404159efe6b007e2fe457924397e593e6c5f7bb268049dcd`.
- Release payload: 9 files / 7,150,601 bytes. Primary reader ZIP: 2,606,679
  bytes, SHA-256
  `8e69e971eb44f318772e80ca22a759d97499e16d306d6172a676d79f3446bcfc`.
  Explicit 86-file source/backend ZIP: 4,520,133 bytes, SHA-256
  `740fa491a223e0e8b6b01e21a06124ed9e38c734fcec3d74fc065f6c26888f40`.
  Root receipt SHA-256:
  `ce31ccec23f86dd592807e56be6efefff6c61457483cb373ea807f692d32b0fb`.

All source, asset, runtime, normalization, translation, build, and deterministic
QA scripts passed in check-only mode immediately before this checkpoint. The
reader was inspected at 1440×900 and 390×844 CSS-pixel viewports. All three
routes fill the available main-content width; none widens the page; all 500
mathematics surfaces render; fresh console logs are empty.

## Rights and next action

Penn State remains CC BY-NC 4.0 except where otherwise noted; MathJax remains
Apache-2.0; original repository support remains CC BY-SA 4.0. The collection is
not uniformly relicensed. Translation provenance is `OpenAI Codex gpt-5.6-sol,
Ultra`; source and human-contributor credits remain preserved.

Regenerate the reader-first release from its explicit immutable allowlist,
commit and push this boundary, verify all 28 deployed reader bytes, publish the
exact release files as a new version inside Zenodo concept
`10.5281/zenodo.22077422`, anonymously read every public byte back, and record
sanitized publication receipts. Then begin Lesson 02 without reopening the
completed documents.
