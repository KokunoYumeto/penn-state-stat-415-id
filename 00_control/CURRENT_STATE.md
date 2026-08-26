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
00–11: 13 of 14 documents. It contains 4,352 translated segments, 5,664
normalized source units, 5,652 derivative units, and 2,804 protected
mathematics surfaces. The twelve removed derivative units are the two already
registered Lesson 00 source defects plus the complete nested closure of two
visible Lesson 08 internal authoring notes; no instructional unit was removed.
Lesson 12 is the only pending source document.

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
At the historical Lesson 10 boundary, the cumulative reader had 2,540
protected math nodes, 56 substantive images, seven semantic tables, zero
external runtime requests, and no sensitive/local path findings. The Lesson 10
target title, captions, alts, duplicate-ID repairs, table associations, runtime
disclosure, and responsive reflow passed its deterministic QA gate.
Translation provenance remains exactly `OpenAI Codex gpt-5.6-sol, Ultra`.

## Lesson 11 local boundary

Lesson 11 freezes 99,359 authority bytes at SHA-256
`4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32`.
Its normalization has 354 translation segments, 264 stable structural units,
264 protected mathematics surfaces, seven examples, one semantic table, four
code nodes, and one same-origin portrait. The normalization receipt is 8,194
bytes, SHA-256
`448773792cfad18d52fb883d3dba4a298d5271948fdbedd2d9e01d7d2a70cdd4`.

The portrait `bayes.png` is frozen byte-for-byte at 142,195 bytes, SHA-256
`2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22`.
The asset manifest is 434 bytes, SHA-256
`a10a6bc2c5ba7738916eeb2ac1cb12d2ed52a77d505e9843190ffa39a726379b`;
the asset-freeze receipt is 1,062 bytes, SHA-256
`2d128b3d4b4635aa45855b8d5ba82cbec408f139a1ac51bcddcbd7682221f3e2`.
It remains under the official page notice, is copied without binary
modification, and receives an Indonesian alternative description, caption,
rights notice, and responsive full-width centered layout in the derivative.

All 354 translation segments are complete. The canonical merged translation
is 86,242 bytes, SHA-256
`1b54aa89f765f3befbd9464d4382aa68551f7278947a06d01621fd26b632c20c`;
its 354-record binding backend is 165,244 bytes, SHA-256
`dbf90c6a2ed2bc7b31c0df808b28351a08ef61e14ddd73fc048562e1e350ed8f`.
The translation receipt is 3,264 bytes, SHA-256
`fc920cee18729d0e775e7e8cad922163af9a4d50f2ef4826a4c79395a615a374`.
The final Lesson 11 target is 69,861 bytes, SHA-256
`70a954496254cf26abd8d28317d45ac1bc945ed2551dd4a6b0eb902ae78e8002`.

Twenty proved target-only repairs are registered contiguously as
`O006-PSU-ADV-0199` through `O006-PSU-ADV-0218`. Five protected mathematics
surfaces change under explicit records: `O006-PSU-012-M0057`, `M0118`,
`M0134`, `M0253`, and `M0263`. The cumulative 218-record correction backend
is 313,335 bytes, SHA-256
`699377a938dcd9a2336d3d69b2d4258b3358db3f8f3beabb24f666c396c1b53a`;
the durable adverse-ledger prefix through Lesson 11 is 315,281 bytes, SHA-256
`376515c286f48ee5f648097cfa093b2b305e7dec9c67e6ca986300815fc2c17d`.
All repairs are target-only; authority bytes remain unchanged.

## Deterministic and browser evidence

The cumulative offline reader through Lesson 11 contains 96 files /
17,232,761 bytes. Its manifest is 10,290 bytes with SHA-256
`026ac69ce34ceb77d3174ff167621043bd9ff5d2e5ce82124b8bec3faf365173`.
The build receipt is 8,116 bytes with SHA-256
`421d60b88849d9f800d4dc1691d28e59f01c86ac4d892c01f797d7114ee4b98d`; the
deterministic QA receipt is 7,503 bytes with SHA-256
`d715c53a6bd48992a1bca49937adfbdf917f38c7ac1c864b76d52c0e9e104f39`.
Asset freeze, normalization, translation merge, cumulative build, and QA
check-only replays pass. The QA gate covers 13-of-14 metadata/navigation, all
2,804 math nodes, 57 substantive images, eight semantic tables, the
142,195-byte Lesson 11 asset, 218 corrections, code/runtime disclosure,
responsive reflow, privacy, and deterministic 96-file replay.

The prior 12-of-14 visual receipt remains historical evidence at
`7c1377982b1cadbd7dbd69de84a63d8bbeb6df0961758c5c8e52f25cc1fc75a5`.
The current bounded browser inspection passes at 1,280 × 720 and 390 × 844
for index, Lessons 00–11, and licenses: 14 routes and all 77 referenced local
resources return HTTP 200, all 2,804 math surfaces render, all 57 substantive
images load, all eight tables remain inside the reader, the Lesson 11 portrait
is centered and full-width, and fresh console warning/error logs are empty.
The 13-of-14 visual receipt is
`build/THROUGH_LESSON11_VISUAL_QA_RECEIPT.json`, 17,818 bytes, SHA-256
`4b7644108b5423c83ec049c6710622c1605dc4b46901c9fae9c579a1a4a1e5bc`;
the durable control copy is byte-identical.

The 218-row correction backend has the exact ordered IDs
`O006-PSU-ADV-0001` through `O006-PSU-ADV-0218`. The translation-ledger prefix
through Lesson 11 contains thirteen rows and resolves every target byte count
and SHA-256 against this build; its 5,417-byte prefix SHA-256 is
`d674909cce4e6ed9a144eda1808fff6634f1b0d91748df94241dfedd6a278a2f`.
The admitted Lesson 11 glossary prefix contains 168 decisions through
`O006-TERM-0168`; its first 17,727 bytes have SHA-256
`1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65`.
Later additive rows do not mutate this frozen boundary.

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
circular.

The next authorized operation is to package and publish the validated local
13-of-14 boundary in the existing GitHub and Zenodo lineages, then verify its
public bytes anonymously. Continue immediately afterward with Lesson 12, the
only pending source document, using the same stable-ID, translation,
correction, build, QA, and publication workflow. No upstream message has been
sent. The independent completed Random edition remains outside this
repository's write boundary.
