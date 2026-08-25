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
00–09: 11 of 14 documents. It contains 3,458 translated segments, 4,775
normalized source units, 4,763 derivative units, and 2,171 protected
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

## Deterministic and browser evidence

The cumulative offline reader contains 71 files / 8,551,979 bytes. Its
manifest is 7,478 bytes with SHA-256
`fa29f2df5f34e441d976280696ef2433845a65fe4ec478674346e56e2f50ffc8`.
The build-receipt SHA-256 is
`00199cebee641d78b09e8aab1b1c7ac8c687fdad93dca848444d698bc20443a1`;
the deterministic-QA receipt SHA-256 is
`431f74cc685b73220ae7559d0299bec5e08b1637d239c901dd31280503878db3`.
Build and QA write/check-only replays pass.

The deterministic nine-file reader-first release package also passes write
and check-only replay. Its non-self-referential exact identities are recorded
in `build/THROUGH_LESSON09_PACKAGE_RECEIPT.json` and the release root receipt;
the current controls deliberately do not embed a circular hash of a package
that contains those same controls.

Desktop and mobile browser QA passes all twelve routes at 1,280 × 720 and
390 × 844 CSS pixels. All 2,171 protected mathematics nodes render; all 34
substantive images load, center exactly, and fill the available reader width;
page/main/navigation overflow is zero; Lesson 08 code scrolls internally on
mobile; and all three Lesson 09 tables scroll internally without widening the
page. Warning/error console logs are empty. The 12,207-byte visual-QA receipt
has SHA-256
`fa3ffb355a15dbeb50da1651037c1a66e85eba87617864427981ed4c9338006d`.

The 170-row adverse ledger and cumulative correction backend share the exact
ordered IDs `O006-PSU-ADV-0001` through `O006-PSU-ADV-0170`. The eleven-row
translation ledger resolves every target byte count and SHA-256 against the
current build. The glossary contains 142 decisions at SHA-256
`d0f8baa72ac1be3a3be1e5774db5608ce8655aa83aed910363727e05322b45f0`.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. Translation provenance remains exactly
`OpenAI Codex gpt-5.6-sol, Ultra`; all source and human-contributor credits are
preserved. No upstream message has been sent.

## Publication state and next work

The last anonymously verified public archive remains the 7-of-14 Zenodo
version DOI `10.5281/zenodo.22097348` in concept DOI
`10.5281/zenodo.22077422`. The compact 8-of-14 GitHub/Pages checkpoint remains
public at commit `abbadb33755be935e0b5753313f3c2967b0994e0`, successful Pages run
`32866078986`. The 11-of-14 local boundary is QA-complete and
release-package-complete but is not yet claimed public in this file: push it,
anonymously verify commit,
Pages, tag/release assets, and publish/read back the next version in the same
Zenodo lineage.

After that preservation transaction, the next source document is Lesson 10.
The independent completed Random edition remains in its separate sibling
repository and is outside this component's write boundary.
