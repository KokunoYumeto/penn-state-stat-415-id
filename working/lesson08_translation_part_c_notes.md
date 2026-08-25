# Lesson 08 translation part C — decisions and deferred corrections

Scope: exactly `O006-PSU-009-S0201` through
`O006-PSU-009-S0291` (91 text segments), in source order.

Authority and binding:

- `authority/upstream/stat415/Lesson08.html`: 135,460 bytes; SHA-256
  `7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`
- `working/lesson08_segments.csv`: SHA-256
  `48a0fdf1d9c039cbb02fbdf8549092f27ef2997451d57e0571dbc110d9c0a8a5`
- assigned source-binding digest: SHA-256
  `c31b82d10742733e82685f07bf8740098ec77a14cf15312a2c686a89e55bbdb7`
  over 7,644 UTF-8 bytes of
  `segment_id<TAB>source_sha256<LF>`
- translation JSON: 8,211 bytes; SHA-256
  `7792fa22b64842703e5d9f4a712fb631f523032b4459c3d8d5ede28822cf9340`

## Translation decisions

- Applied the controlling distinctions **penduga** / **nilai dugaan** /
  **pendugaan**, **fungsi kemungkinan**, **himpunan dukungan**, **selang
  kepercayaan**, **distribusi asimtotik**, **informasi Fisher**, and
  **distribusi empiris**.
- Followed the Lesson08 QA wording **bootstrap parametrik**, **bootstrap
  nonparametrik**, **sampel bootstrap**, **nilai dugaan bootstrap**,
  **pengambilan sampel ulang dengan pengembalian**, **metode Delta**,
  **parameter bentuk**, **parameter lokasi**, and **fungsi mulus**.
- Preserved decimal points, `MLE`, `lessons.qmd`, distribution names, all
  fragment boundaries, and the leading/trailing whitespace of every source
  segment. Formulae, executable identifiers, code, and figure alternatives are
  outside this target JSON.
- Applied registered surface finding `L08-D017` at `S0241` by correcting the
  nonexistent “Section 5” reference to **Bagian 8.1**, and at `S0245` by
  treating `.025` and `.975` as two endpoint quantiles.

## Registered downstream correction obligations

This JSON remains the source-bound language layer. The cumulative correction
layer must still apply the following already registered findings rather than
silently changing protected formula, code, output, or asset surfaces here:

- `L08-D008`, `L08-D013`, and `L08-D014`: reconcile the seeded Pareto outputs,
  correct the support to `[L, infinity)`, and retain the ordinary percentile
  interval for `L` only as an invalid endpoint-inference counterexample.
- `L08-D009`–`L08-D011`: distinguish expected from observed information and
  the numerical NLL Hessian; state the MLE result as an asymptotic theorem; and
  require differentiability at the true parameter in the delta method, using
  the derivative there in the limit.
- `L08-D012`: replace the unrestricted-bootstrap and small-sample overclaims
  in `S0247`–`S0249` and `S0290`–`S0291` with the registered validity
  conditions.
- `L08-D015`: supply the full Indonesian alternative for Figure 8.4 outside
  this segment map.
- `L08-D016`: remove the two reader-visible authoring-note callouts represented
  by `S0257`–`S0258` and `S0288`–`S0289`; they are translated here only so the
  lossless source map remains complete and nonempty.

## Validation contract

- JSON has exactly 91 sorted keys, the contiguous assigned range, no metadata
  keys, no empty values, and no U+FFFD.
- Leading and trailing whitespace matches the corresponding frozen source text
  for all 91 values.
- No shared glossary, control, script, source, backend, Git, build, or
  publication artifact is modified by this part.
