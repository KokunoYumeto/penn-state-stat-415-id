# Current state — Penn State STAT 415 id-ID component

Updated: 2026-08-25

All fourteen official Penn State documents—landing/index plus Lessons 00–12—
remain frozen at exactly 1,604,869 bytes. The source-manifest SHA-256 is
622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515;
the freeze-receipt SHA-256 is
2a63e37bb6b4637cfd2522e392b140f2b625f2a1cf5f76f267a53ba4fb2e119b.
Authority bytes are immutable and unchanged.

The cumulative local edition is complete through the landing page and Lessons
00–06: 8 of 14 documents. It contains 2,487 translated segments, 3,358
normalized source units, 3,356 derivative units, and 1,648 protected
mathematics surfaces. Exactly 122 proved source defects are corrected only in
the derivative: 112 through Lesson 05 and ten in Lesson 06.

Lesson 06 is complete. Its official 77,034-byte authority has SHA-256
abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06.
Deterministic normalization emits 176 translation segments, 149 structural
units, 102 protected math nodes, no code, one PNG asset, no external
dependencies, and 429 catalogue records. The 32,426-byte normalized source has
SHA-256 a7060d1f7e3f1109d45635a79bf48aa070416bc647080faab1b0084ed8bc9d19;
the normalization-receipt SHA-256 is
0d433c72be68f19b85565111427f32f80d8f029cbf58c717de5e6e1d405963db.

All 176 Lesson 06 segments are translated into natural id-ID. The 49,074-byte
translation CSV has SHA-256
9125d88e87401f0c77c9365e2bc9be3f54b575d06677dfab9624998b5cad6ebe;
the 72,845-byte stable-ID bindings have SHA-256
6f2c1561731f1cf051727a4463d227025216f911eae789227b0d87dd79ce8cc3;
and the translation-receipt SHA-256 is
ee3564906ff873a78786f890d916a0245f83d64bf6cf86821edbc251cbd61a40.
The target Lesson 06 HTML is 36,492 bytes with SHA-256
1567542aa5ab52169d7d744664460786f7ca1d7bc9166daa00142f19a8956b6a.

The ten Lesson 06 corrections distinguish estimator from realized estimate;
restore a missing equality; identify lowercase-z critical values without
altering the source image; define lower-tail chi-square quantiles; state the
correct studentized large-sample condition; repair the estimated standard
error; state the exact iid-Normal t interval with n−1 degrees of freedom;
supply complete figure alternative text; repair seven mechanical surface
defects; and add a semantic proof role. The adverse ledger and cumulative
correction backend now contain the same ordered 122 correction IDs.

The single Lesson 06 source PNG is preserved byte-for-byte at 67,496 bytes,
SHA-256 2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f.
Its target-only alternative text and correction note describe both tails and
the critical values. The obsolete 70-percent inline width was removed, so the
reader figure fills the centered available width without changing source
pixels.

The deterministic cumulative reader contains 52 files / 3,693,257 bytes. Its
manifest SHA-256 is
c50dfab1b3d09a747efc44cad124a68659617d3561dc6dbc2bfe13b8d2abe128;
build-receipt SHA-256 is
9ccc325f8016472aa883053d2a157969a79fbd445f22b02801274eaf0015574f;
and QA-receipt SHA-256 is
2374ebf621d9d6dcd4aaec80450541ea86bb276a38c758275d6d1d5534c6d330.
Build and QA check-only replays pass.

Desktop and mobile browser QA passes all nine routes at 1,280 × 720 and
390 × 844 CSS pixels. All 1,648 protected mathematics nodes render; all
substantive images load; every figure is centered; no page, main-content, or
navigation overflow occurs; and warning/error console logs are empty. At
mobile width the Lesson 06 diagram occupies the complete 343.11-pixel figure
width. The 7,075-byte visual-QA receipt has SHA-256
fa71eae170b650e5b3bcf4346ceb10cf037fe6c0c40fdf0c8fe602850cb312a2.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. Translation provenance remains exactly
OpenAI Codex gpt-5.6-sol, Ultra; all source and human-contributor credits are
preserved. No upstream message has been sent.

The last anonymously verified public release remains the 7-of-14 boundary:
content commit 119a516cd5f933d18aa1b548608208e1be539f6d, tree
e6900190bd218f857cbb3e07946296c131e08ef1, tag v2026.08.25.7of14,
successful Pages run 32856448005, Zenodo version DOI
10.5281/zenodo.22097348, and concept DOI 10.5281/zenodo.22077422.
Lesson 06 is a closed local production checkpoint; the next batched public
preservation boundary will include further contiguous lessons rather than a
new archive cycle for every individual HTML document.

The next production document is Lesson 07. The independent completed Random
edition remains in its separate sibling repository and is outside this
component's write boundary.
