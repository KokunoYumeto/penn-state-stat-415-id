# Local production complete — cumulative edition through Lesson 06

Date: 2026-08-25
Status: deterministic local checkpoint passed; next public archive boundary is batched

## Boundary

- Complete documents: landing/index plus Lessons 00–06, 8 of 14.
- Translation segments: 2,487.
- Normalized source units: 3,358.
- Derivative units: 3,356.
- Protected mathematics nodes: 1,648.
- Target-only proved corrections: 122, including ten in Lesson 06.
- Reader: 52 files / 3,693,257 bytes.
- Reader manifest: 5,289 bytes; SHA-256
  c50dfab1b3d09a747efc44cad124a68659617d3561dc6dbc2bfe13b8d2abe128.

## Lesson 06 identity

- Authority: authority/upstream/stat415/Lesson06.html, 77,034 bytes,
  SHA-256
  abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06.
- Normalized source: source/normalized/en-US/Lesson06.html, 32,426 bytes,
  SHA-256
  a7060d1f7e3f1109d45635a79bf48aa070416bc647080faab1b0084ed8bc9d19.
- Translation: source/id-ID/lesson06_translation.csv, 49,074 bytes,
  SHA-256
  9125d88e87401f0c77c9365e2bc9be3f54b575d06677dfab9624998b5cad6ebe.
- Stable-ID bindings: backend/lesson06_translation_bindings.jsonl,
  72,845 bytes, SHA-256
  6f2c1561731f1cf051727a4463d227025216f911eae789227b0d87dd79ce8cc3.
- Target HTML: source/id-ID/Lesson06.html, 36,492 bytes, SHA-256
  1567542aa5ab52169d7d744664460786f7ca1d7bc9166daa00142f19a8956b6a.
- Figure: build/html-id/assets/lesson06/ci_1.png, 67,496 bytes,
  SHA-256
  2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f;
  byte-identical to authority.

## Deterministic gates

- Normalization receipt SHA-256:
  0d433c72be68f19b85565111427f32f80d8f029cbf58c717de5e6e1d405963db.
- Translation receipt SHA-256:
  ee3564906ff873a78786f890d916a0245f83d64bf6cf86821edbc251cbd61a40.
- Build receipt SHA-256:
  9ccc325f8016472aa883053d2a157969a79fbd445f22b02801274eaf0015574f.
- QA receipt SHA-256:
  2374ebf621d9d6dcd4aaec80450541ea86bb276a38c758275d6d1d5534c6d330.
- Visual-QA receipt: 7,075 bytes; SHA-256
  fa71eae170b650e5b3bcf4346ceb10cf037fe6c0c40fdf0c8fe602850cb312a2.
- Build and QA check-only replays pass.
- All 122 ordered adverse-ledger IDs equal the cumulative correction backend;
  all eight translation-ledger target sizes and hashes match live artifacts.
- Desktop 1,280 × 720 and mobile 390 × 844 passes cover all nine routes:
  exact MathJax counts, no broken substantive images, centered figures, zero
  page/main/navigation overflow, and empty warning/error console logs.
- At mobile width the Lesson 06 diagram occupies the full 343.11-pixel figure
  width; the upstream 70-percent inline constraint is absent.

## Rights and publication state

Penn State remains CC BY-NC 4.0 except where otherwise noted; MathJax remains
Apache-2.0; original repository support remains CC BY-SA 4.0. Translation
provenance is OpenAI Codex gpt-5.6-sol, Ultra. No upstream message was sent.

The last complete anonymously verified public archive is still the 7-of-14
Lesson 05 release: GitHub content commit
119a516cd5f933d18aa1b548608208e1be539f6d, tag v2026.08.25.7of14,
Pages run 32856448005, and Zenodo DOI 10.5281/zenodo.22097348 in concept
10.5281/zenodo.22077422. Lesson 06 is deliberately carried into the next
substantial multi-lesson public preservation boundary instead of creating a
full release/archive cycle for one HTML document.

## Next action

Translate Lesson 07 completely, including the registered consistency-versus-
expectation correction and the source's omitted-regularity boundary. Continue
through Lessons 08 and 09, then run one cumulative build, backend, visual, and
public-byte verification gate. Do not reopen Lessons 00–06.
