# Current state — Penn State STAT 415 id-ID component

Updated: 2026-08-26

## Authority and boundary

All fourteen official Penn State documents—landing/index plus Lessons 00–12—
remain frozen at exactly 1,604,869 bytes. The source-manifest SHA-256 is
`622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`;
the freeze-receipt SHA-256 is
`2a63e37bb6b4637cfd2522e392b140f2b625f2a1cf5f76f267a53ba4fb2e119b`.
Authority bytes are immutable and unchanged.

The cumulative local edition is complete through the landing page and Lessons
00–10: 12 of 14 documents. It contains 3,998 translated segments, 5,400
normalized source units, 5,388 derivative units, and 2,540 protected
mathematics surfaces. The twelve removed derivative units are the two already
registered Lesson 00 source defects plus the complete nested closure of two
visible Lesson 08 internal authoring notes; no instructional unit was removed.

## Lessons 07–09 contiguous batch

Lesson 07 freezes 105,026 authority bytes at SHA-256
`2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`.
Its 237 segments, 399 units, 148 math nodes, two PNG assets, and twelve proved
repairs are complete. The 74,079-byte target SHA-256 is
`d5714697191c3530be7183ee15a8ae3dffda87596338eadb293ac58c0d1cb440`.
The derivative explicitly corrects the source implication that consistency
alone yields expectation convergence: an additional condition such as uniform
integrability is required.

Lesson 08 freezes 135,460 authority bytes at SHA-256
`7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`.
Its 291 segments, 604 source units / 594 derivative units, 156 math nodes, four
PNG assets, 28 visible code surfaces, and seventeen proved repairs are
complete. The 113,208-byte target SHA-256 is
`d902c11f06ed884d3124596c9c178e87dbd993063b65c454176e73c96b4d3daf`.
Code-line stable IDs are preserved even where corrected code has a different
line count. Bootstrap validity, reproducibility, Pareto endpoint inference,
expected versus observed information, and delta-method conditions are repaired
only in the derivative.

Lesson 09 freezes 114,901 authority bytes at SHA-256
`87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319`.
Its 443 segments, 414 units, 219 math nodes, ten assets, three semantic tables,
and nineteen proved repairs are complete. The 95,275-byte target SHA-256 is
`539cf8f248e654ccb70bf12c98318ece8ac9de7281ae1f1ea5bb3d364d134f64`.
All decision tables have captions, row/column semantics, and explicit header
associations; all images have complete Indonesian alternatives and responsive
reader layout.

## Lesson 10 contiguous boundary

Lesson 10 freezes 152,767 authority bytes at SHA-256
`0cb938a114d27b03ef3196c24a2e87b79a1a466b9dcbe370e6e6553947446bf5`.
Its complete target has 540 segments, 625 source units, 369 math surfaces,
22 byte-preserved assets totaling 8,313,758 bytes, nine code surfaces, two
semantic tables, and 28 proved target-only corrections. The target is 153,768
bytes with SHA-256
`8fb91a9fc5ef0b5a163767aec5e760d19c3e56f6c3dee35ee58323d6c45359c5`.
The cumulative build has 94 files / 17,020,141 bytes; its manifest is 10,100
bytes with SHA-256
`08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663`.
The build receipt is 24,978 bytes, SHA-256
`0f440e56bf71e172815ac0933e752e3f3f12383573e4c501db8fe5aa1922a520`; the
deterministic QA receipt is 6,118 bytes, SHA-256
`6bc589012a12e93d9418fe9f26029ca8b58b6de61235a4d6181114afa2300180`.
Both write and check-only replays pass. The cumulative correction backend now
has the ordered IDs `O006-PSU-ADV-0001` through `O006-PSU-ADV-0198`; the
Lesson 10 suffix is 300,910 bytes, SHA-256
`2450673f606d7a308dd7490cd811f81dcd3c42cc382b1eefe2b21d3dbb2f2032`.
The cumulative reader has 2,540 protected math nodes, 56 substantive images,
seven semantic tables, zero external runtime requests, and no sensitive/local
path findings. The Lesson 10 target title, captions, alts, duplicate-ID
repairs, table associations, runtime disclosure, and responsive reflow pass
the deterministic QA gate. Translation provenance remains exactly
`OpenAI Codex gpt-5.6-sol, Ultra`.

## Deterministic and browser evidence

The cumulative offline reader through Lesson 10 contains 94 files /
17,020,141 bytes. Its manifest is 10,100 bytes with SHA-256
`08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663`.
The build receipt is 24,978 bytes with SHA-256
`0f440e56bf71e172815ac0933e752e3f3f12383573e4c501db8fe5aa1922a520`; the
deterministic QA receipt is 6,118 bytes with SHA-256
`6bc589012a12e93d9418fe9f26029ca8b58b6de61235a4d6181114afa2300180`.
Build and QA write/check-only replays pass. The QA gate covers 12-of-14
metadata/navigation, all 2,540 math nodes, 56 substantive images, seven
semantic tables, 22 Lesson 10 assets, 198 corrections, code/runtime
disclosure, responsive reflow, privacy, and deterministic 94-file replay.

The prior 11-of-14 visual receipt remains historical evidence at
`fa3ffb355a15dbeb50da1651037c1a66e85eba87617864427981ed4c9338006d`.
The current bounded browser inspection passes at 1,280 × 720 and 390 × 844
for index, Lessons 00–10, and licenses: all 2,540 math surfaces render, all
56 substantive figures are centered and full-width, tables/code remain inside
the reader, and fresh console warning/error logs are empty. Four deferred
index thumbnails were additionally verified with same-origin HTTP checks. The
12-of-14 visual receipt is
`build/THROUGH_LESSON10_VISUAL_QA_RECEIPT.json`, 13,129 bytes, SHA-256
`7c1377982b1cadbd7dbd69de84a63d8bbeb6df0961758c5c8e52f25cc1fc75a5`.

The 198-row adverse/correction backend now shares the exact ordered IDs
`O006-PSU-ADV-0001` through `O006-PSU-ADV-0198`. The twelve-row translation
ledger resolves every target byte count and SHA-256 against the current build.
The glossary contains 150 decisions at SHA-256
`68e65dbf862ed9e1c1f1d6e5fca857f2112fbb08dc4f9fa9ba86419992425a67`.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. Translation provenance remains exactly
`OpenAI Codex gpt-5.6-sol, Ultra`; all source and human-contributor credits are
preserved. No upstream message has been sent.

## Publication state and next work

The 12-of-14 boundary is public and anonymously verified. GitHub commit
`a342a4cf4de7464f42d6a3f2aa97bfcdf66293a1`, tree
`0f399d4efef53c29f5e0123a7febf8eb2305f869`, Pages run `32917215255`, tag
`v2026.08.26.12of14`, and the corresponding release are public. All 611
commit-tree files, all 94 Pages files, and all nine release assets matched
their local byte counts and SHA-256 values without credentials. The
commit/Pages receipt SHA-256 is
`89989d0eefbb59f4591eab929045a4bbb07451b07de272f9c4ab85be2455128d`;
the release-asset receipt SHA-256 is
`668f570a4e4daaadcbb36e34083e1dfc0d7df90d4b473d20046979927864b598`.

Zenodo DOI `10.5281/zenodo.22104074` is the one submitted 12-of-14 version in
concept DOI `10.5281/zenodo.22077422`; zero draft remains. Its anonymous
readback matched all nine files / 49,769,118 bytes. The publication, public
readback, and final lineage-audit receipt SHA-256 values are respectively
`73dd8c11d02c51dba254c6b49d070ae5398410cd6e659035a55fd04d32f61f02`,
`e6c071838a0f350ea559fb4113b38c5bbcc549c126bf8015473bd206f3417dfe`,
and `87147a07c7dc5bc3c33e985c07bb803d1fe5b9f700f351b354b3ad7e1d6f6d39`.
The lineage pointer SHA-256 is
`270223022aa3a8f8bcd1bbed25190f0b4337bd3646a58f64ea1d13cdb65b0cd6`.

The published deterministic reader-first package contains nine files /
49,769,118 bytes, 94 reader files, and 432 bounded source entries. Its package
receipt is `build/THROUGH_LESSON10_PACKAGE_RECEIPT.json`; that receipt carries
the exact asset inventory and hashes. Its self-hash is intentionally kept out
of this source-package closure so the ZIP remains reproducible rather than
circular. Continue now in source order with Lesson 11 and then Lesson 12,
reusing the same stable-ID, translation, correction, build, QA, and publication
workflow. No upstream message has been sent. The independent completed Random
edition remains outside this repository's write boundary.
