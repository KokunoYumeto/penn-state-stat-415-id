# Checkpoint — complete STAT 415 reader, LF reproducibility repair

Date: 2026-08-26

The complete landing/index plus Lessons 00–12 reader remains 14 of 14
documents, 4,932 translated segments, 6,510 source units / 6,498 target units,
3,156 protected source-mathematics surfaces, 242 target-only corrections, and
106 reader files / 17,614,553 bytes. Its 11,573-byte manifest remains SHA-256
`697c9ee8e23cc10469fea4d1894e16471ffb4276edd1f0d25bebfb5be0dbe79e`.
No reader-facing byte changed in this repair.

The first complete GitHub workflow exposed a cross-platform source-witness
identity mismatch. `working/lesson12_source_findings.md` is committed and
checked out under the repository's LF policy as 8,203 bytes, SHA-256
`8b087fb8e545f14ba323afd1caa5672117d60878c3c5924a0b0455136078109c`;
two scripts and their receipts still bound an 8,209-byte CRLF copy. Those exact
bindings now use the canonical LF identity. The repaired receipt identities
are:

- Lesson 12 normalization: 9,727 bytes, SHA-256
  `ef7b86ff5d6e46237688051fe1ffd867d2a2006d2c8393370b697abe2fae8156`;
- Lesson 12 translation: 3,748 bytes, SHA-256
  `5514555698cd07737d12e3b91e440af9f9302dc32de5df49716c8b532f248364`;
- Lesson 12 materialization: 3,911 bytes, SHA-256
  `e55f6154cf8555edbed8eda452aa058186d3067b5e2e1b4061a5fd697b91fa67`;
- cumulative build: 17,276 bytes, SHA-256
  `d7bae677a7d93023322773806a96418b3d96af19bae39bfd5fe967c327d01954`;
- cumulative deterministic QA: 12,428 bytes, SHA-256
  `44a0fd8e432f81da65776b45f33cccda0e462db32bb04bf8ecdb6d11eeca5560`.

The exact full GitHub Actions command chain passes locally after the workflow
was advanced from the obsolete through-Lesson11 replay to the complete Lesson
12 freeze/normalize/translate/materialize/ledger/build/QA chain. Browser QA is
still bound to the unchanged reader: 21,702 bytes, SHA-256
`2fe1f40b8748b0dcc67e08e6a87e6ba402b5323b581744f73e35c787ae583d5f`.

Zenodo record `22105226`, DOI `10.5281/zenodo.22105226`, is public in concept
`22077422`; anonymous readback matched its nine files / 55,308,347 bytes, and
the authenticated concept audit found one submitted matching version and zero
drafts. Its immutable source ZIP predates this six-byte binding repair, so one
corrected version must be published in the same concept after the repaired
GitHub gate. Do not create a competing concept.

Next executable action: commit and push the narrow LF/workflow repair, require
the exact CI/Pages run to pass, publish and anonymously verify GitHub tag and
release `v2026.08.26.14of14`, rebuild the reader-first package with the repaired
source receipts, publish the corrected Zenodo version, and anonymously verify
all files. Then begin the consolidated PDF/EPUB boundary.
