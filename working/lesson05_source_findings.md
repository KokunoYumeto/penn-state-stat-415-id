# Penn State STAT 415 Lesson 05 — mechanically proved source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson05.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson05`
- bytes: `190308`
- SHA-256: `dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`
- normalized document identity: `O006-PSU-006`
- corroborating, non-authoritative audit:
  `working/lesson05_math_audit.md`, SHA-256
  `65c29afb0ca867fc6cb40666e1af5d2837dd488be0880e043fd13bc5df805fcd`

Only defects directly demonstrated by the frozen source, elementary
probability/calculus, the visible R code/output, or deterministic DOM/asset
inspection are registered. Authority bytes, formulas, code, outputs, anchors,
and assets are not silently corrected in the normalized source.

## Mathematical, computational, and reproducibility findings

### L05-D001 — density, mass, and likelihood conflation

- locations: `S0078` and `S0080`
- source calls the value returned by a generic `dXXX` function a PDF and also
  groups PDF, PMF, and likelihood as the same task.
- correction: `d*` returns a density for continuous models or a mass for
  discrete models; it is a likelihood factor only after the observation is
  fixed and a parameter is varied.

### L05-D002 — one Normal draw is called ten draws

- locations: code unit `U0674` and prose `S0096`; downstream formulas
  `M0009`–`M0010`
- source assigns `x=rnorm(n=1,mean=3,sd=2)` and outputs one value, then says
  `x` contains ten simulated observations and uses ten-observation notation.
- correction: assign the intended ten draws to `x` and regenerate dependent
  values, or consistently change the later surface to one draw.

### L05-D003 — exact random outputs are unseeded

- code units include `U0648`, `U0662`, `U0674`, `U0776`, and `U0812`
- the first Normal and Exponential simulations call `rnorm`/`rexp` without a
  preceding seed while retaining exact vectors, summaries, probabilities,
  products, and plots.
- correction: set and document a seed before each independent simulation or
  freeze explicit generated vectors. Example 5.2's `set.seed(123)` is the
  reproducible pattern.

### L05-D004 — likelihood is written as a function of random data

- locations: `M0009` and `M0010`
- source writes `L(X_1,...,X_10)` and `l(X_1,...,X_10)` with model parameters
  fixed.
- correction: call these joint-density expressions, or write likelihood and
  log-likelihood as functions of parameters for fixed observations.

### L05-D005 — grid-search vector is never filled

- location: code unit `U0986` and the following grid-search surface
- source creates `lik.vals=rep(NA,length(theta.vals))` but contains no visible
  assignment to `lik.vals[i]` before plotting and calling `which.max`.
- correction: add the stated loop/equivalent vectorized computation before
  consuming `lik.vals`.

### L05-D006 — grid approximation is called the exact MLE

- locations: code unit `U0972` and `M0032`
- source searches a grid spaced by `0.1` and calls `8.9` “our MLE.”
- correction: label 8.9 the grid approximation. For the listed data,
  `sum(x)=133`, `n=15`, and the exact exponential-mean MLE is
  `133/15 = 8.866666...`.

### L05-D007 — score function is defined as an equation

- locations: `M0041` and `M0049`
- source writes `h(theta)=ell'(theta)=0`, then omits the closing parenthesis in
  `h(theta^(0))`.
- correction: define `h(theta)=ell'(theta)`, separately solve `h(theta)=0`,
  and close the evaluation delimiter.

### L05-D008 — Newton tangent is taken on the wrong function

- location: especially `S0190` and surrounding `M0051`–`M0055`
- source derives Newton root finding for the score `h=ell'`, but the animation
  narrative says to evaluate and take the tangent of the log-likelihood.
- correction: evaluate/tangent the score and use its x-intercept. A score root
  still needs domain and maximum checks.

### L05-D009 — Newton recurrence starts at the wrong index

- locations: `M0062` and `M0063`
- source gives `theta^(0)` but begins the recurrence at `t=1`.
- correction: the first update uses `t=0`.

### L05-D010 — parameter disappears inside one equality

- location: `M0065`
- source first writes `f_X(x_i,theta)` and then `log f_X(x_i)` for the same
  parameter-dependent density.
- correction: retain explicit conditioning/parameter notation consistently.

### L05-D011 — Newton–Raphson and `optim()` method are blurred

- visible `optim()` calls include `U1308`, `U1377`, and `U1459`
- no call specifies `method`; base R therefore defaults to Nelder–Mead, not
  the hand-coded Newton recurrence taught immediately beforehand.
- correction: name the methods separately and explicitly select/implement the
  intended one.

### L05-D012 — exponential rate and mean/scale are reversed

- locations: `S0242` and code unit `U1292`
- prose calls `theta` a rate while code evaluates
  `dexp(...,rate=1/theta)`.
- correction: keep the code and call `theta` the mean/scale with rate
  `1/theta`, or reparameterize all code/results consistently as a rate.

### L05-D013 — positive exponential domain is not enforced

- location: `U1308`, `optim(2,nll.exp,x=x)`
- a positive starting value does not stop unconstrained `optim()` from trying
  nonpositive mean/scale values.
- correction: optimize a log parameter or use an explicitly bounded method.

### L05-D014 — unsafe advice to ignore optimizer warnings

- locations: `S0279`–`S0284`
- the source tells readers to ignore most warnings even while explaining that
  the objective was evaluated at invalid negative parameters.
- correction: enforce the domain and diagnose every warning/nonfinite value.

### L05-D015 — objective verification uses the reciprocal parameter

- location: inline code unit `U1358`
- source says `nll.exp(0.112793,x)` returns `47.73448`, although the implemented
  function treats its input as the mean/scale and obtains that value near
  `8.865625`.
- correction: verify at the implemented estimate, or change the entire
  objective to a rate parameterization.

### L05-D016 — `$counts` is misdefined and misreported

- locations: output unit `U1349` and `S0290`
- source output is 30 objective calls and `NA` gradient calls; prose calls
  `$counts` 32 optimization iterations.
- correction: distinguish function/gradient evaluations from iterations and
  report the visible values accurately.

### L05-D017 — convergence code is overclaimed

- locations: `S0292`–`S0294` and `S0329`
- source treats `convergence == 0` as sufficient proof that the MLE can be
  trusted.
- correction: also verify parameter domain, finite/correct objective,
  derivative/Hessian or analytic benchmark, and sensitivity to starts/method.

### L05-D018 — both optimizer estimates are copied incorrectly

- location: `S0298`
- prose says `8.6875 vs 8.65625`; displayed outputs are `8.865625` and
  `8.86875`.
- correction: use the displayed values and identify both as numerical
  approximations to `8.866666...`.

### L05-D019 — Normal variance domain is unguarded

- locations: objective code `U1433` and optimizer call `U1459`
- objective evaluates `sqrt(s2)` but the optimizer is unconstrained and may
  try `s2<=0`.
- correction: optimize log variance or apply a strictly positive bound, then
  compare with the exact Normal MLE benchmark.

### L05-D020 — Normal mean estimate has the wrong symbol

- location: `M0106`
- source labels the first Normal parameter estimate
  `hat(theta)_ML=-3.186` even though that parameter is `mu`.
- correction: use `hat(mu)_ML`.

## Mechanically proved surface and accessibility findings

### L05-D021 — stale title categories

- locations begin at `S0004`–`S0010`
- all seven categories—Point Estimation, Unbiased Estimation, Bias, Variance
  and Mean Square, Factorization, Sufficiency, and Method of Moments—belong to
  earlier lessons rather than Lesson 05's R/numerical-MLE content.

### L05-D022 — character-vector instruction and cross-reference

- location: `S0046`
- source says letters need “parentheses”; executable R strings need quotation
  marks. It also points to Section 3.2 instead of local subsection 5.1.2.

### L05-D023 — unmatched closing quotation mark

- location: `S0087`
- source ends “for future use” with a closing quote that has no opening quote.

### L05-D024 — “Interactively” typo

- location: `S0160`
- intended process is **iteratively** finding a parameter sequence.

### L05-D025 — “tangent like” typo

- location: `S0180`
- intended phrase is **tangent line**.

### L05-D026 — overbroad R derivative claim

- location: `S0213`
- source says R cannot directly calculate derivatives; base R has limited
  symbolic facilities such as `D` and `deriv`.
- correction: say that this example derives and codes the derivatives
  manually.

### L05-D027 — `optim` grammar

- locations: `S0285` and `S0290`
- use possessive `optim`'s output and singular “a stopping criterion.”

### L05-D028 — duplicated/malformed remote video surface

- dependency: `O006-PSU-006-D0001`
- the main contains two iframe occurrences with the exact same Kaltura URL,
  title, and duplicated DOM id `kaltura_player`; both wrappers contain invalid
  `padding-bottom:2 %>% %` CSS.
- correction: deduplicate or identify distinct media, assign unique IDs, and
  retain a complete static derivation/fallback. Third-party video bytes are
  not frozen or assumed covered by the page licence.

### L05-D029 — duplicate figure DOM IDs

- native IDs: `fig-boxplotcornyield`, `fig-histogramcornyield`, and
  `fig-scattercornyield`
- each occurs on both a container and its image; HTML IDs must be unique.

### L05-D030 — missing and non-specific image descriptions

- missing alt: `O006-PSU-006-A0004`
- vague repeated alt: `O006-PSU-006-A0008`–`A0012`
- correction: describe the unlabelled exponential histogram and give each
  Newton frame an iteration-specific point/tangent/root description.

## Asset closure disposition

All 14 same-origin instructional PNG references are frozen at their exact
official URLs under `authority/assets/stat415/lesson05/`; total 484,520 bytes,
13 unique payload hashes. Each file passed PNG signature, chunk-boundary, CRC,
IHDR dimension, terminal-IEND, no-trailing-byte, and embedded-metadata checks,
and was visually matched to its lesson context. The page-level CC BY-NC 4.0
witness is present and no per-image exception appears in the instructional
main. Exact URLs, response headers, byte counts, hashes, dimensions, alt text,
rights, and local paths are in `working/lesson05_asset_closure.json`.

The generated PNGs report a 2026-08-24 Last-Modified date, later than the
frozen HTML's 2026-08-19 header; the closure truthfully records them as current
official bytes checked on 2026-08-25, not as a byte-synchronous export from the
older HTML timestamp. The two identical external Kaltura iframe occurrences
remain excluded and require reader replacement/static fallback.

### L05-D031 — exposed internal editorial note

- location: `S0156`
- source exposes `---I moved this from under the single header!--`, an internal
  authoring note with no instructional meaning.
- correction: replace it in the derivative with a concise reader-facing
  transition into the numerical-optimization discussion.
