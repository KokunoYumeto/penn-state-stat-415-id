# Lesson 05 translation part B notes

Scope: `O006-PSU-006-S0116` through `O006-PSU-006-S0230` from
`working/lesson05_segments.csv` (115 consecutive segments).

Terminology follows `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv` and
`working/lesson05_terminology_qa.md`. The translation preserves each source
segment's leading and trailing whitespace boundary. Formula/code units,
identifiers, source hashes, authority bytes, and the segment CSV were not
modified.

## Corrected target-language surfaces

- `O006-PSU-006-S0156` — `L05-D031`: replaces an exposed internal
  authoring note with a reader-facing transition into numerical optimization.
- `O006-PSU-006-S0122`–`S0124` — `L05-D004`: calls the displayed product a
  joint density for the fixed rate rather than a joint likelihood of random
  variables.
- `O006-PSU-006-S0147` — `L05-D005`: states that the `for` loop must fill
  `lik.vals` before the result is used. The absent executable loop is a
  source/code-unit defect outside this target-text file.
- `O006-PSU-006-S0149`, `S0152`, `S0153`, and `S0216` — `L05-D006`: labels
  the finite-grid result as an approximation, not the exact MLE.
- `O006-PSU-006-S0160` — `L05-D024`: translates the intended
  **iteratively**, correcting source “Interactively.”
- `O006-PSU-006-S0172`–`S0174` and `S0182` — `L05-D007`: distinguishes the
  score-function definition from the equation solved for its root. The
  malformed immutable formula unit still requires correction in the formula
  layer.
- `O006-PSU-006-S0180` — `L05-D025`: corrects “tangent like” to tangent line.
- `O006-PSU-006-S0190` and `S0192` — `L05-D008`: takes and evaluates the
  tangent of the score function, then requires domain and maximum checks for
  the resulting root.
- `O006-PSU-006-S0196`–`S0197` — `L05-D009`: states that the first Newton
  update uses `t=0`. The immutable displayed recurrence-index formula remains
  a formula-layer correction.
- `O006-PSU-006-S0201` — `L05-D011`: explicitly distinguishes default
  `optim()` (Nelder–Mead) from the manually coded Newton–Raphson update.
- `O006-PSU-006-S0213` — `L05-D026`: replaces the overbroad claim that R
  cannot calculate derivatives with the accurate statement that this example
  derives and codes them manually.

## Reader-prose QA refinements

- `O006-PSU-006-S0121` replaces the calque “hampiran dekat terhadap” with
  natural Indonesian stating that the sample approximation is close to the
  displayed true value.
- `O006-PSU-006-S0129` states that the MLE cannot be obtained analytically and
  therefore requires numerical optimization; it no longer says that an
  estimator itself is “solved” or refers to an unspecified equation.
- `O006-PSU-006-S0152` explicitly maps the first displayed value to the grid
  approximation and the second to the analytic MLE used for comparison.
- `O006-PSU-006-S0174` labels `h(theta)=ell'(theta)` as the definition of the
  score rather than as the root equation.
- `O006-PSU-006-S0189` truthfully introduces the retained static summary rather
  than promising an animation.
- `O006-PSU-006-S0196`–`S0197` now form one grammatical instruction around the
  corrected recurrence range beginning at `t=0`.

## Out-of-scope registered surfaces in this slice

`L05-D003`, `L05-D028`, `L05-D030`, and the formula/code portions of
`L05-D005`, `L05-D007`, `L05-D009`, and `L05-D010` require changes to
simulation setup, executable code, formula units, embedded media, or image
metadata rather than to these CSV target-text rows. They were not silently
changed here.
