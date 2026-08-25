# Current state — Penn State STAT 415 id-ID component

Updated: 2026-08-25

All fourteen official Penn State documents—landing/index plus Lessons 00–12—
remain frozen at exactly 1,604,869 bytes. The source-manifest SHA-256 is
`622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`;
the freeze-receipt SHA-256 is
`2a63e37bb6b4637cfd2522e392b140f2b625f2a1cf5f76f267a53ba4fb2e119b`.

The cumulative local edition is complete through the landing page and Lessons
00–05: 7 of 14 documents. It contains 2,311 translated segments, 3,209
normalized source units, 3,207 derivative units, and 1,546 protected
mathematics surfaces. Exactly 112 proved source defects are corrected only in
the derivative: 81 through Lesson 04 and 31 in Lesson 05. Authority bytes are
unchanged.

Lesson 05 is complete. Its official 190,308-byte authority, SHA-256
`dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`,
was normalized into 340 translation segments, 1,475 structural units, 108
protected math nodes, 267 code nodes, fourteen same-origin PNG assets, one
external video dependency, and 1,939 catalogue records. Its normalized source
is 187,687 bytes with SHA-256
`d47e377a40f78ade8c83ae8cb0a3fcaa8dbf87555d5e0751d5316f0ec6e354dc`;
the normalization-receipt SHA-256 is
`d00f4238f3fe3b5104c0169a89c00aa940c25bff26ec311354b0651c443d03be`.
The final translation CSV is 101,032 bytes with SHA-256
`9f9247ff3d7c66e164bc6691fee67da51fcdf88cd951a9582ff32dae3015e3ac`;
its 141,524-byte stable-ID bindings have SHA-256
`85821982f209874b0270d24fb9a3ac863139ab6d090e4c9ab34c88d262212f58`.
The translation-receipt SHA-256 is
`56ce80c909c360a90e9cbf7b410480cf74e875093e5ada5d12333372c48d6506`.
The target HTML is 195,351 bytes with SHA-256
`254cc78ca7b633c15356c90ebb37d646d39a22acffd52fd965f07563e9722308`.

Lesson 05 has 31 high-confidence mathematical, computational, reproducibility,
surface, DOM, interface, asset, and accessibility corrections. Its fourteen
reader images total 498,847 bytes; thirteen preserve authority bytes and one
simulation plot is a disclosed seeded derivative. Two external video iframe
occurrences are excluded from the offline reader and replaced with complete
static instructional fallbacks. The locally frozen MathJax 3.1.2 runtime now
includes its exact `boldsymbol` autoload dependency.

The deterministic cumulative reader contains 50 files / 3,588,430 bytes. Its
manifest SHA-256 is
`fb600bfedb1792d8b1c9ba8d72d3e5ef6bf94e7a9744a387e15b1d5a7b5f8e6f`;
build-receipt SHA-256 is
`afe2b51786792ecfc88e556c9a5dd26e1ff45524f45799a64f1f694c77e322a0`;
QA-receipt SHA-256 is
`462b7c15f3d506d5028ba2c2c4737dc2bba701bdb91acb0b967620f23c3b3f68`.
Normalization, merge, build, manifest, topology, mathematics, stable-ID,
correction, rights, privacy, asset, seeded-output, static-fallback, and
internal-link checks replay in check-only mode.

Desktop and mobile browser QA passes all eight routes at 1,280 x 720 and
390 x 844 CSS pixels. All 1,546 source mathematics nodes render exactly; all
images load; no page or navigation overflows; and the console is clean. The
visual-QA receipt is 6,691 bytes with SHA-256
`c595832f3a2efd8b83b3b0fb03051cf271e717a871023cceef0ef83d30a35245`.

The local 7-of-14 release package is ready: nine files / 15,429,698 bytes. Its
primary 3,603,326-byte offline-reader ZIP has SHA-256
`89a4e458ee9aa30d2293cb95b9f0be3ecef947241ddd6dfca473ac568c6ceecf`;
the 11,806,424-byte resumable source/backend ZIP has SHA-256
`a43219092614e24db2a829b4e2cc4ed90ccf215313671ff99cc405735625aa1b`.
The package receipt is 4,696 bytes with SHA-256
`7db3e2a7699e2f5441ebd0db14189efb9fa5cb4649ae02eab6f8b6cc45664fe0`.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. Translation provenance remains exactly
`OpenAI Codex gpt-5.6-sol, Ultra`; all source and human-contributor credits are
preserved. No upstream message has been sent.

The 7-of-14 checkpoint is public at content commit
`119a516cd5f933d18aa1b548608208e1be539f6d`, tree
`e6900190bd218f857cbb3e07946296c131e08ef1`, GitHub tag
`v2026.08.25.7of14`, successful Pages run `32856448005`, and Zenodo version
DOI `10.5281/zenodo.22097348` inside concept DOI
`10.5281/zenodo.22077422`. Anonymous readback matched all 362 commit files /
32,109,463 bytes, all 50 Pages files / 3,588,430 bytes, all nine GitHub release
assets / 15,429,698 bytes, and the same nine Zenodo files / 15,429,698 bytes.
The GitHub publication and release receipt SHA-256 values are respectively
`72906372bcead09ac3e6d8b6f3a82fcc5b55ee631bcafddb16686eef4ff444a5` and
`f9d6632e27a4ca66bfea436465cef458bfed3f1c7cdd96ea022a55b0c5947a1a`.
The Zenodo publication, public-readback, and lineage-audit receipt SHA-256
values are respectively
`1d61e2795dc2d559a9fb1786006a9beed7ad5ac4582d62a31b8a858ee3187f1c`,
`4a5b0420f442910ddcbeed03bf686028fd7c9e655b5230881db2421e1e622f94`, and
`e0d2e7c41a822483521859f2755005f1eda8eadea991b37e4d4d06867c5791d7`.
The next production document is Lesson 06.

The independent completed Random edition remains in its separate sibling
repository and is outside this component's write boundary.
