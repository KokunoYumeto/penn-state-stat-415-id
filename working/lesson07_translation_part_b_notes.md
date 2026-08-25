# Lesson 07 translation part B — decisions and deferred corrections

Scope: exactly `O006-PSU-008-S0081` through
`O006-PSU-008-S0160`, in source order.

Authority and ledger:

- `authority/upstream/stat415/Lesson07.html`: 105,026 bytes; SHA-256
  `2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`
- `source/normalized/en-US/Lesson07.html`: 69,757 bytes; SHA-256
  `c67926962dc23726b74668536aac11b5c054f44faf416a8a84bcefa3191aa9d8`
- `working/lesson07_segments.csv`: 42,812 bytes; SHA-256
  `1d7f6cb87bb3faedfabeb66709ceca6cea1c33a818f2e30708c30ebeb908c1e3`
- protected source formula SHA-256:
  `c2da24f78e6d812d1bd5245e5cb671b52c1f3c5053de56e8141d13512fa36bb3`

## Translation decisions

- Applied the controlling terms **peubah acak**, **sampel acak**, **fungsi
  massa peluang (PMF)**, **fungsi kepadatan peluang (PDF)**, **nilai
  harapan**, **fungsi kemungkinan**, **fungsi log-kemungkinan**, **pendugaan
  selang**, **selang kepercayaan asimtotik**, and **matriks informasi
  Fisher**.
- Retained `MLE`, `PMF`, `PDF`, `Normal`, all mathematical symbols, and all
  protected formula boundaries. No formula, inline HTML, or code text occurs
  inside this target JSON.
- Preserved source order and the newline boundaries in `S0104` and `S0131`.
  Word-boundary spaces adjacent to retained theorem titles and formulas follow
  the established Lesson07 part-A pattern so the reconstructed reader text
  remains grammatical.
- Rendered the source's “any MLE” in `S0102` as **setiap MLE**, without
  silently turning the surrounding, explicitly incomplete regularity
  discussion into an unconditional finite-sample theorem.

## Registered corrections and protected obligations

### `L07-D009` — exponential density mislabeled as a PMF (`S0138`)

The continuous exponential model is rendered as **fungsi kepadatan peluang
(PDF)**. The correction layer must also retain the registered domain
qualification `x_i >= 0`, `theta > 0`; no mathematical material was inserted
into this language fragment.

### `L07-D011` — mechanical surfaces in this range

The following language-level repairs were made naturally and are disclosed
here:

- `S0089`: `lets` was rendered with the intended invitation;
- `S0099` and `S0152`: `Parmater` was treated as `Parameter`;
- `S0131`: the duplicated construction `it is chosen it` was removed; and
- `S0155`: the duplicated `as follows. as` was repaired while preserving the
  transition to `n -> infinity`.

The protected `M0098` surface also belongs to `L07-D011`: its derivative's
left side must read `d ell(theta)/d theta`. It remains outside this JSON and
must be supplied by the deterministic correction layer.

### Protected mathematical corrections not folded into translation

- `L07-D003` / `M0088`: restore the omitted `1.96` in the intermediate
  Bernoulli margin while retaining the already correct `0.3036` and endpoints.
- `L07-D004` / `M0104`: replace the erroneous reciprocal step by
  `sqrt(1/I_n(hat(theta))) = xbar/sqrt(n)`.
- `L07-D002` / `M0102`: distinguish expected Fisher information from an
  observed substitution; the protected display is not rewritten here.

## Validation contract

- JSON contains exactly 80 nonempty string values and no metadata keys.
- Keys are the contiguous ordered range `S0081`–`S0160` and bind the frozen
  per-segment `source_sha256` values in the Lesson07 ledger. The 21 leading
  word-boundary spaces retained by those hashes are also present in the
  corresponding targets.
- Mathematical surfaces remain in the normalized source and are not copied or
  altered in the target JSON.
- No shared glossary, control, script, normalized source, backend, Git,
  Lesson08, earlier lesson, or publication artifact is modified by this part.
