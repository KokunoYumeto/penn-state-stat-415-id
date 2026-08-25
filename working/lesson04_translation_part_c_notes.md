# Lesson 04 translation notes — partition C

## Exact boundary

- Source: `working/lesson04_segments.csv`, 67,200 bytes, SHA-256
  `9e8798eb42a03ebfb06d8e3fe26cba57c87d5989bd405dc26d46f92404b38efe`
- Target: `working/lesson04_translation_part_c.json`
- Exact ordered range: `O006-PSU-005-S0249` through
  `O006-PSU-005-S0372`, inclusive
- Exact target count: 124
- Locale: `id-ID`
- No formulas or HTML were inserted into target strings. Formula corrections
  remain the normalized builder’s responsibility and are identified below.

## Controlling terminology

The translation follows `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv` and
`working/lesson04_terminology_qa.md`: `fungsi kemungkinan`,
`fungsi log-kemungkinan`, `penduga kemungkinan maksimum (MLE)`, realized
`nilai dugaan kemungkinan maksimum`, `fungsi indikator`, `himpunan dukungan`,
`statistik urutan`, `model berparameter tunggal`, and `model multiparameter`.
PDF, PMF, MLE, iid, R, and mathematical symbols remain unchanged.

## Disclosed source corrections represented in these targets

1. **Pareto endpoint consistency (`L04-D014`)** —
   `O006-PSU-005-S0260`–`S0264` use “lebih besar daripada atau sama dengan” so
   the prose agrees with the stated support and the proved correction from
   strict `>` to `>=`. The corresponding formula correction remains outside
   the translation strings.
2. **Monotonic-support qualification** — `O006-PSU-005-S0268`–`S0271`
   replace the source’s overgeneralized monotonicity rule with the correct
   dependence on the direction of the feasible support boundary. No new
   formula was added.
3. **Indicator terminology/source typo** — `O006-PSU-005-S0281` and `S0282`
   render the source’s erroneous “indication function” as the established
   `fungsi indikator`.
4. **Estimator versus estimate** — estimator surfaces
   `O006-PSU-005-S0255`, `S0265`, `S0286`, `S0290`, `S0310`, `S0323`,
   `S0346`–`S0348`, `S0355`, and `S0370` use `penduga`/MLE; realized-value
   surfaces `S0275` and `S0288` use `nilai dugaan`. This deliberately avoids
   collapsing the two source concepts into `estimasi`.
5. **Laplace kink and median nonuniqueness (`L04-D017`)** —
   `O006-PSU-005-S0333`–`S0338` explicitly frame the condition through a
   subgradient at the nondifferentiable kink. `S0345`–`S0347` state that any
   sample median is admissible and that, for even sample size, every value
   between the two middle order statistics can maximize the likelihood.
   `S0348` consequently says `syarat optimalitas` rather than pretending both
   equations are ordinary differentiable score equations. The corrected
   piecewise and final-estimator formulas (`L04-D017` and `L04-D018`) remain
   formula-layer corrections.
6. **Gamma parameter/score defects (`L04-D019`–`L04-D021`)** —
   `O006-PSU-005-S0353`–`S0362` remain parameter-name-neutral around the
   interleaved mathematics. The formula layer must consistently choose one
   scale symbol, restore the missing differential, and restore the omitted
   alpha-score term.
7. **Gamma numerical-solution claim** — `O006-PSU-005-S0363` replaces the
   false claim that the Gamma function is “not analytically tractable” with
   the precise fact that the shape score involves the digamma function and
   generally lacks an elementary closed-form root; after profiling the scale,
   the remaining one-dimensional shape equation is solved numerically.
8. **Likelihood definition** — `O006-PSU-005-S0368`–`S0369` define likelihood
   as the joint mass/density evaluated at the observed sample and viewed as a
   function of the parameter, explicitly not a probability distribution over
   that parameter.
9. **MLE definition** — `O006-PSU-005-S0370`–`S0371` identify the estimator as
   a statistic/function of the random sample that selects a maximizing
   parameter value, rather than calling an observed parameter value itself an
   estimator.
10. **Analytic-solution scope** — `O006-PSU-005-S0366` adds “apabila
    memungkinkan” so the summary does not claim that every MLE in the lesson
    has a closed analytic solution.

## Boundary note

Leading/trailing whitespace, newlines, commas, periods, and meaningful trailing
spaces were preserved where each segment joins an interleaved mathematical
node. In `S0341` and `S0344`, a directly attached comma replaces the source’s
directly attached English possessive suffix, preserving the no-leading-space
boundary while yielding grammatical Indonesian after the inline symbol.
At the partition seam, `S0249` says that the likelihood supremum is approached,
not attained, so it remains consistent with the source's strict open endpoint
and the correction already stated in `S0246`–`S0248`.
