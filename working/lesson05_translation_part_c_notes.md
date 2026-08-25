# Lesson 05 translation part C notes

## Scope

- Source: `working/lesson05_segments.csv`
- Exact segment range: `O006-PSU-006-S0231`–`O006-PSU-006-S0340`
- Expected and produced mapping count: 110
- Only `target_text` strings were translated; segment identifiers and source authority were not changed.

## Corrected source surfaces

- `S0231`, `S0260` — audit defects 13/19: clarified that a valid positive starting value does not enforce the parameter domain throughout optimization.
- `S0242`–`S0243` — audit defect 12: treated `theta` as the exponential mean/scale used by `dexp(..., rate=1/theta)`, with rate `1/theta`, rather than reproducing the source's reversed rate label.
- `S0247`, `S0250`–`S0252` — audit defects 1/4: distinguished per-observation log-density from likelihood, and stated that summing fixed-data log-density contributions forms the log-likelihood.
- `S0279`–`S0284` — audit defects 13/14: replaced the unsafe instruction to ignore `optim` warnings with domain enforcement and warning diagnosis.
- `S0287` — audit defect 6: described optimizer output as a tolerance-dependent numerical approximation rather than automatically as the exact MLE.
- `S0288`–`S0289` — audit defect 15: the derivative's repaired inline call evaluates `nll.exp(out$par,x)` and the prose reports its checked value, `47.73448`.
- `S0290` — audit defect 16: identifies `$counts` as objective/gradient function-evaluation counts and reports the repaired bounded run's 12 objective plus 12 numerical-gradient evaluations, rather than calling them iterations.
- `S0291`–`S0295`, `S0299`–`S0303`, `S0327`–`S0329`, `S0335` — audit defects 13/17/19: limited convergence code 0 to an internal stopping result; required domain, objective, sensitivity, and analytic checks; and supplied the Normal-variance analytic benchmark.
- `S0298` — audit defect 18: reports the two reproducible bounded-run approximations, 8.866665 and 8.866664, and compares them with the analytic MLE 8.866666....
- `S0333`–`S0335` — audit defects 19/20: reads fluently around the repaired formulas for the bounded Normal fit, with mean -3.188414 and variance 14.885495.
- `S0338`–`S0339` — audit defect 11: separated Newton–Raphson from `optim()`'s default Nelder–Mead method.

## Reader-prose QA refinements

- `S0245` and `S0306` spell out `Gambar`, consistently with every preceding
  figure caption in this lesson.
- `S0265`–`S0266` make the retained intervening term part of the grammatical
  phrase “fungsi yang menghitung negatif log-kemungkinan tersebut” and remove
  the doubled “fungsi negatif fungsi” calque. The correction layer should set
  immutable unit `U1318` to the exact reader term `log-kemungkinan`.
- `S0279`–`S0280` now form a grammatical sentence that requires every `optim`
  warning to be examined; the case of the immutable inline code token remains
  a correction-layer concern.
- `S0339` applies the lesson's established capitalization consistently to
  `Normal` and `Eksponensial` in the same distribution list.

## Validation record

- Authority SHA-256: `dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`.
- Source CSV SHA-256: `c6feafa8f43d442256dc118491186c274e9197edc925096f2ebfc586abea5f36`.
- Translation JSON SHA-256: `7975f8cd990c4e9f899ab7e2a2b8f6119e30c3b097b4198e71a0728aac5eabc3`.
- Deterministic validation: JSON parse passed; 110 mappings; exact contiguous ID range and order; zero missing, extra, empty, or duplicate keys; zero leading/trailing whitespace-boundary mismatches; all target strings NFC-normalized; zero rejected glossary variants.
- Terminal state: translation and deterministic QA complete; no publication or Git action was authorized or performed.
