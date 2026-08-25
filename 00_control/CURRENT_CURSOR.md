# Production cursor

Updated: 2026-08-25

## Current boundary

- Role: O006 / C140 Mathematical Statistics.
- Component: Penn State STAT 415 external narrative spine, `id-ID`.
- Frozen corpus: landing/index plus Lessons 00–12, fourteen official documents,
  1,604,869 bytes; source-manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Translation complete locally: landing/index plus Lessons 00–05, 7 of 14
  documents and 2,311 admitted segments.
- Structure and mathematics: 3,209 normalized source units, 3,207 derivative
  units, and 1,546 protected mathematics surfaces. The two removed Lesson 00
  units are registered source defects; all other topology is preserved.
- Corrections: 112 target-only proved repairs—81 through Lesson 04 and 31 in
  Lesson 05. Authority bytes remain unchanged.
- Lesson 05 authority: 190,308 bytes; SHA-256
  `dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`.
  Deterministic normalization emits 340 segments, 1,475 units, 108 mathematics
  nodes, 267 code nodes, fourteen same-origin PNG assets, one external video
  dependency, 1,939 catalogue records, and 31 proved source defects;
  normalization-receipt SHA-256
  `d00f4238f3fe3b5104c0169a89c00aa940c25bff26ec311354b0651c443d03be`.
- Lesson 05 translation CSV: 101,032 bytes; SHA-256
  `9f9247ff3d7c66e164bc6691fee67da51fcdf88cd951a9582ff32dae3015e3ac`.
  Its 340 stable-ID bindings are 141,524 bytes; SHA-256
  `85821982f209874b0270d24fb9a3ac863139ab6d090e4c9ab34c88d262212f58`.
- Lesson 05 target HTML: 195,351 bytes; SHA-256
  `254cc78ca7b633c15356c90ebb37d646d39a22acffd52fd965f07563e9722308`.
- Cumulative offline reader: 50 files / 3,588,430 bytes; manifest SHA-256
  `fb600bfedb1792d8b1c9ba8d72d3e5ef6bf94e7a9744a387e15b1d5a7b5f8e6f`.
- Deterministic build-receipt SHA-256:
  `afe2b51786792ecfc88e556c9a5dd26e1ff45524f45799a64f1f694c77e322a0`.
- Deterministic QA-receipt SHA-256:
  `462b7c15f3d506d5028ba2c2c4737dc2bba701bdb91acb0b967620f23c3b3f68`.
  Write and check-only replays pass. All 340 Lesson 05 mappings, 108 protected
  math surfaces, 31 correction records, fourteen image routes, seeded output,
  manifest entries, links, rights, privacy, and static video fallbacks are
  closed.
- Desktop/mobile visual QA passes all eight reader routes at 1,280 x 720 and
  390 x 844 CSS pixels with exact mathematics counts, zero broken images, zero
  page or navigation overflow, and zero console errors or warnings. Visual-QA
  receipt SHA-256:
  `c595832f3a2efd8b83b3b0fb03051cf271e717a871023cceef0ef83d30a35245`.
- The local release package is ready: nine files / 15,405,517 bytes. The
  3,603,326-byte offline-reader ZIP has SHA-256
  `89a4e458ee9aa30d2293cb95b9f0be3ecef947241ddd6dfca473ac568c6ceecf`;
  the 11,782,243-byte resumable source/backend ZIP has SHA-256
  `41b2dcc52ec736b1125e91f0d1d2f0a0e7570af191843204c943fe2e418cd189`.
  Package-receipt SHA-256:
  `40d11b1df08c9568cf25188f1431943a7b7fed477eefb1798a7bae608f4674af`.
- Rights remain component-separated: Penn State CC BY-NC 4.0 except where
  otherwise noted; MathJax Apache-2.0; original repository layer CC BY-SA 4.0.
- Last public boundary remains 5 of 14 at commit
  `5727d8fc056d9535ac5d75a4305166f7c027b13f`, tag
  `v2026.08.25.5of14`, and Zenodo version DOI `10.5281/zenodo.22088315`.
  The 7-of-14 package is complete locally but is not recorded as public until
  its public-byte readback succeeds.
- No upstream message has been sent.

## Next executable action

Publish the completed 7-of-14 package to the dedicated repository and existing
Zenodo concept lineage, then anonymously verify every public byte and record
the receipts. Continue immediately with Lesson 06 in source order: normalize
its exact authority and asset closure, translate all admitted segments into
natural `id-ID`, preserve code and mathematics, apply only proved target-side
corrections, and advance the cumulative reader without reopening Lessons
00–05.

## Recovery

Read `WORKFLOW.md`, this file, `CURRENT_STATE.md`, `COMPONENT_BOUNDARY.md`,
`CHECKPOINT_2026-08-25_THROUGH_LESSON05_LOCAL.md`, the Lesson 05 normalization,
translation, build, QA, visual-QA, and package receipts, and the Lesson 05 math
audit, terminology QA, source findings, and asset closure. Conversation
summaries are not state. Do not broaden the filesystem or Git scope.
