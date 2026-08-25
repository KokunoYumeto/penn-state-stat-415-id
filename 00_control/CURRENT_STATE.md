# Current state — Penn State STAT 415 id-ID component

Updated: 2026-08-25

All fourteen official Penn State documents—landing/index plus Lessons 00–12—
remain frozen at exactly 1,604,869 bytes. The source-manifest SHA-256 is
`622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`;
the freeze-receipt SHA-256 is
`2a63e37bb6b4637cfd2522e392b140f2b625f2a1cf5f76f267a53ba4fb2e119b`.

The cumulative local edition is complete through the landing page and Lessons
00–03: 5 of 14 documents. It contains 1,599 translated segments, 1,399
normalized source units, 1,397 derivative units, and 1,149 protected
mathematics surfaces. Exactly 46 proved source defects are corrected only in
the derivative—fourteen from the first unit, six from Lesson 01, nine from
Lesson 02, and seventeen from Lesson 03. Authority bytes are unchanged.

Lesson 03 is complete. Its 118,925-byte authority, SHA-256
`26dd4efe75abc879a5316c215eaedbfe713c77e742898eb86e7f3d88cb0c04c9`,
was normalized into 531 translation segments, 421 stable units, 440 protected
mathematics nodes, zero content assets, and 1,393 catalogue records. The final
translation CSV is 123,145 bytes with SHA-256
`ab96512a2b7f8eb5d86b60dbcc2ad6779f74623367e4537b04167ce22bc8215a`;
its bindings SHA-256 is
`00202b65c0376c7065de20270980da6f0d14c50f38e7e946609e31981b903781`.
An independent audit replayed all 531 mappings and found no missing or extra
IDs, English leakage, terminology violations, metadata/order changes, or
formula/text boundary defects.

The deterministic cumulative reader contains 32 files / 2,804,159 bytes. Its
manifest SHA-256 is
`15e979bbd3b791b0a7d2a25873e9450030c5a1b7019455982b84e0dac6287831`;
build-receipt SHA-256 is
`4ffb6a9963cc7581139a8f5123225b5fd3c6dc7fc8792f60dc0414bf1b371246`;
QA-receipt SHA-256 is
`262b4143aecc4f4c546adcb5aaf7fec13832f071a2d5a5e43009a8a3204f7eda`.
Normalization, merge, build, manifest, topology, mathematics, stable-ID,
rights, privacy, asset, and internal-link checks replay in check-only mode.

Desktop/mobile inspection at 1280×720 and 390×844 confirmed no page-level or
navigation overflow on the landing, Lessons 00–03, or licence route. The exact
1,149 mathematics nodes rendered at both viewports; all twenty reader images
loaded; fresh warning/error logs were empty. The repaired Lesson 03
likelihood-ratio counterexample (U0127) and factor-versus-exponent explanation
(U0140) were inspected in the mobile reader, and the full Lesson 03 opening was
inspected at desktop width. The 6,042-byte visual receipt has SHA-256
`f80ba6dc59e3ce4e869950b3b6175b75af5affb4a445a3f1881a129fba3f34f7`.
The 5-of-14 boundary is public and anonymously verified.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. No aggregate uniform relicensing is claimed. The
translation provenance is exactly `OpenAI Codex gpt-5.6-sol, Ultra`; all source
and human-contributor credits are preserved. No upstream message has been sent.

The public checkpoint is commit
`5727d8fc056d9535ac5d75a4305166f7c027b13f`, GitHub release
`v2026.08.25.5of14`, and Zenodo version DOI `10.5281/zenodo.22088315` inside
concept DOI `10.5281/zenodo.22077422`. Anonymous readback matched all 244
commit files, all 32 Pages reader files, and all nine GitHub/Zenodo release
files / 10,260,651 bytes. The Zenodo lineage audit reports one submitted latest
version and zero drafts. The next action is Lesson 04 production in source
order.

The independent completed Random edition remains in its separate sibling
repository and is outside this component's write boundary.
