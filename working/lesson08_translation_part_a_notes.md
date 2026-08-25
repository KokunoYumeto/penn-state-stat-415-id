# Lesson 08 translation part A — decisions

Scope: exactly `O006-PSU-009-S0001` through
`O006-PSU-009-S0100`, in source order.

- Frozen segment ledger: `working/lesson08_segments.csv`, SHA-256
  `48a0fdf1d9c039cbb02fbdf8549092f27ef2997451d57e0571dbc110d9c0a8a5`.
- Assigned source-hash binding digest: SHA-256
  `45430a0a325f61e9a6392f2ed0849d60853c6567d68273df14d323c1b3eced0f`
  over the 100 ordered `segment_id<TAB>source_sha256<LF>` lines.

## Translation decisions

- Applied the cumulative glossary distinctions **penduga**, **nilai dugaan**,
  **pendugaan**, **selang kepercayaan**, **fungsi kemungkinan**, **fungsi
  log-kemungkinan**, **hampiran**, and **kuantil**.
- Applied the Lesson 08 terminology decisions **bootstrap parametrik**,
  **bootstrap nonparametrik**, **sampel bootstrap**, **metode delta**, and
  **parameter derajat kebebasan**. Preserved `MLE`, `R`, `optim`, and all
  executable identifiers.
- Retained every segment boundary and the exact leading/trailing whitespace of
  its source segment. The broken source quote bytes were rendered as proper
  Indonesian quotation marks, so the target contains no replacement character.

## Registered corrections represented in this part

- `L08-D001`: prose consistently distinguishes the parameter, its **nilai
  dugaan**, and bootstrap estimates. Corrections to the protected math node
  `M0035` remain for the bound correction layer.
- `L08-D015`: the number-only `Fig 8.1` caption is expanded into an Indonesian
  text equivalent that identifies both axes, the observed range and the main
  histogram shape. The image asset itself is untouched.
- `L08-D017`: repaired the `M`/`m` prose, singular/plural agreement, and broken
  quotation surface in natural Indonesian. Protected formulas remain available
  for the separately registered correction layer.

Other registered issues in this range reside in protected formula or R-code
nodes (`L08-D002`, `L08-D004`, `L08-D006`, `L08-D007`, and `L08-D009`) and are
not silently rewritten by this text-only translation part.

## Validation

- JSON parses and contains exactly 100 nonempty string values.
- Keys are exactly the contiguous, sorted range `S0001`–`S0100`.
- Leading/trailing whitespace matches each source segment.
- U+FFFD count: zero.
- Translation JSON: 10,691 bytes; SHA-256
  `f0f9b1640966d12b5588b383df12e0dfe0ab0507c4997dad74d61a131b441238`.

No glossary, source, script, backend, build, Git, or publication path was
modified.
