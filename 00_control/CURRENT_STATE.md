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
`b31ed728f1b66dc257000aac334fdb5a0240a646777295db1c99396a6884538d`; the
deterministic QA receipt is 6,118 bytes, SHA-256
`c6a1fcf4a2318e2e783f806214dc824fd73da104f19c81fe6965263b1ec7066e`.
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
`b31ed728f1b66dc257000aac334fdb5a0240a646777295db1c99396a6884538d`; the
deterministic QA receipt is 6,118 bytes with SHA-256
`c6a1fcf4a2318e2e783f806214dc824fd73da104f19c81fe6965263b1ec7066e`.
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
`386428d44a9d59f30f2a0b5a263144b0203a233f9c53e63c94ad3229832c76e9`.

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

The 11-of-14 boundary is public and anonymously verified. GitHub commit
`57170f9f7d914f3d13c716d19818ec64c3896df5`, tree
`d94da2ca46268c1d93201e036d91d38132228669`, Pages run `32906124668`, and tag
`v2026.08.26.11of14` are public. All 526 commit-tree files, all 71 Pages files,
and all nine release assets matched their local byte counts and SHA-256 values
without credentials. The commit/Pages receipt SHA-256 is
`c29b263e2e131c224da7cb34c3835f221dd496475e4827055f73b48c97b1a7da`;
the release-asset receipt SHA-256 is
`32099aeaa755ef97b793e987b0000d58218bbda44fa8841a4862b4e295f0c807`.

Zenodo DOI `10.5281/zenodo.22103203` is the one submitted 11-of-14 version in
concept DOI `10.5281/zenodo.22077422`; zero draft remains. Its anonymous
readback matched all nine files / 30,362,116 bytes. The publication, public
readback, and final lineage-audit receipt SHA-256 values are respectively
`b377bab6f477e06a79a118a53d58dafa0e04967a31068addf105bf84960cba80`,
`347069df9554f24b85ef83ad9fa32628038dd6109252b2da8db9659ec1158bff`,
and `21ff308362a8aa6ac1d194d697f7b803482766f503113e902920ed3202933ad3`.

The deterministic reader-first 12-of-14 package is ready and passes write and
check-only replay: nine files / 49,763,980 bytes, 94 reader files, and 432
bounded source entries. Its package receipt is
`build/THROUGH_LESSON10_PACKAGE_RECEIPT.json`, SHA-256
`02c50f2af1f752130b6999048f2d3caa242c22906fd09ae836251136a27415cc`.
The next release action is explicitly authorized: push the dedicated GitHub
repository and Pages, publish the next version in the existing Zenodo concept,
and anonymously verify every public byte. No upstream message has been sent.
After that release, continue in source order with Lessons 11–12; the
independent completed Random edition remains outside this repository's write
boundary.
