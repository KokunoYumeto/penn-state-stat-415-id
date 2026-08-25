# Penn State STAT 415 Lesson 07 — mechanically proved source findings

Checked: 2026-08-25

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson07.html`
- official URL: <https://online.stat.psu.edu/stat415/Lesson07>
- bytes: `105026`
- SHA-256:
  `2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`
- normalized identity: `O006-PSU-008`
- corroborating audit: `working/lesson07_math_audit.md`

Only defects directly demonstrated by frozen prose, formula algebra, frozen R
output, official R behavior, or deterministic DOM/asset inspection are
registered. The authority remains byte-identical. Stable IDs below are the
only admitted Lesson07 correction findings.

## L07-D001 — consistency alone does not imply expectation convergence

- stable evidence: unit `U0038`; segments `S0025`–`S0030`; especially
  `S0028`, which calls the expectation statement a corollary
- source claim: consistency of `hat(theta)_n` is said to imply
  `E(hat(theta)_n) -> theta`
- proof of defect: let `T_n=n` with probability `1/n` and zero otherwise.
  Then `T_n ->p 0`, but `E(T_n)=1` for every `n`.
- proved correction: consistency plus uniform integrability is sufficient;
  equivalently in this setting it yields `L1` convergence and hence convergence
  of expectations. A bounded `(1+delta)` moment is a convenient stronger
  sufficient condition.
- translation gate: do not present the expectation statement as a corollary
  of consistency. State the missing additional condition explicitly.

## L07-D002 — expected and observed information are conflated

- stable formula evidence: `M0043`, `M0102`
- stable prose evidence: `S0177`–`S0183`, `S0190`–`S0196`, and the analogous
  multiparameter `optim` prose
- source: `M0043` puts the estimated parameter inside an expectation defining
  Fisher information; later prose says the Hessian returned by
  `optim(...,hessian=TRUE)` “is the Fisher Information”
- official behavior: R documents the returned object as the numerically
  differentiated Hessian at the solution:
  <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/optim.html>
- proved correction: define expected total-sample information as
  `I_n(theta)=-E_theta[ell_n''(theta)]`. For a minimized negative
  log-likelihood, `out$hessian` estimates observed information
  `J_n(hat(theta))=-ell_n''(hat(theta))`. It may be used as a regular plug-in
  covariance approximation, but the two objects are not definitionally
  identical.

## L07-D003 — Bernoulli interval drops `1.96` in an intermediate equality

- stable evidence: `M0088`
- source chain:
  `0.6 +/- sqrt(.6(1-.6)/10) = 0.6 +/- .3036`
- proof: `sqrt(.024)=.154919...`, whereas
  `1.96 sqrt(.024)=.303641...`
- proved correction:
  `0.6 +/- 1.96 sqrt(.6(1-.6)/10)=0.6 +/- .3036`
- unchanged result: the endpoints `(0.2964,0.9036)` are correct; do not
  recalculate them to match the defective middle expression.

## L07-D004 — exponential Wald interval uses the reciprocal incorrectly

- stable evidence: `M0102`, `M0104`
- correct source result retained: `I_n(hat(theta))=n/hat(theta)^2=n/xbar^2`
- source error: `M0104` replaces `sqrt(1/I_n(hat(theta)))` by
  `sqrt(n^3/xbar^2)`
- proved correction:
  `sqrt(1/I_n(hat(theta)))=sqrt(xbar^2/n)=xbar/sqrt(n)` because exponential
  observations and `xbar` are nonnegative
- corrected interval: `xbar +/- 1.96 xbar/sqrt(n)` under the usual regular
  large-sample conditions

## L07-D005 — Normal-example prose contradicts its frozen optimizer output

- stable evidence: output units `U0331`, `U0344`; segments `S0212`–`S0214`
- frozen output: `hat(mu)=-6.564774`, `hat(sigma^2)=12.773473`
- source prose: `5.469399`, `38.620385`
- proved correction: use the two values from the immediately preceding frozen
  output. They also agree with the reported standard errors and confidence
  intervals; the prose pair does not.

## L07-D006 — numerical objectives do not enforce parameter domains

- stable geometric units: `U0194`, `U0206`, `U0224`
- stable Normal units: `U0309`, `U0325`
- source behavior: the default unconstrained calls can propose invalid
  geometric probabilities, while the Normal objective evaluates `sqrt(vr)`
  without requiring `vr>0`
- official domains: R specifies `0<prob<=1` for `dgeom`, and a negative `sd`
  is invalid for `dnorm`:
  <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Geometric.html>,
  <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Normal.html>
- proved correction: constrain `p` to `(0,1]` and `sigma^2` to `(0,infinity)`
  through a valid reparameterization, guarded objective, or bounded optimizer.
  Preserve the frozen demonstration and add the domain qualification; do not
  pretend convergence code `0` proves global or domain-safe optimization.

## L07-D007 — confidence-interval target is mislabeled as the MLE

- stable evidence: `S0177`, `S0195`–`S0199`
- source phrases include “confidence intervals for MLEs,” “confidence interval
  for our MLE,” and “CI for the MLE of p”
- proved correction: the inferential target is the fixed unknown parameter
  `p` (or `theta`); the MLE is the random statistic used to center the interval
  and estimate its uncertainty
- translation: use **selang kepercayaan asimtotik untuk parameter p,
  berdasarkan MLE**.

## L07-D008 — overview and summary claim instructional content that is absent

- stable evidence: `S0009`–`S0010`, `S0236`–`S0237`
- claimed content: parametric and nonparametric bootstrap confidence
  intervals, the Delta method, transformations by bootstrap, and t/Pareto
  examples
- deterministic body census: none of those methods has an instructional
  section, derivation, code block, example, output, or figure in Lesson07
- proved correction: label those sentences as stale scope/forward-looking
  material; do not translate them as a report of skills taught in this lesson
- preserved actual scope: MLE properties, scalar/vector asymptotic Wald
  intervals, and geometric/Normal numerical demonstrations

## L07-D009 — a continuous exponential density is called a PMF

- stable evidence: `S0138`–`S0139`, `M0090`, `M0093`
- source: “The PMF is” before
  `f(x_i|theta)=theta^(-1) exp(-x_i/theta)`
- proof: `Exp(theta)` is continuous; this is a probability density, with
  support `x_i>=0` and `theta>0`
- proved correction: **fungsi kepadatan peluang (PDF)**, not **fungsi massa
  peluang (PMF)**, and state the support/parameter domain.

## L07-D010 — a code comment reverses the inverse-information entry

- stable evidence: `U0353`
- source comment: `standard errors = sqrt(1/I.inv[p,p])`
- executing code: `sqrt(diag(solve(I)))`
- proof: if `I.inv=I^(-1)`, the covariance diagonal is `I.inv[p,p]`; the
  standard error is `sqrt(I.inv[p,p])`, not its reciprocal square root
- proved correction: repair the explanatory comment or add an adjacent note;
  retain the correct executing expression.

## L07-D011 — nine unambiguous surface defects

Each entry has a stable translation/math boundary and can be repaired without
changing topology:

1. `S0049`: `respectfully` -> `respectively`;
2. `S0061`: missing space in `.Therefore`;
3. `S0089`: `lets` -> `let's`;
4. `S0099`: `Parmater` -> `Parameter`;
5. `S0131`: duplicated construction `it is chosen it`;
6. `M0098`: the derivative's left side omits `ell(theta)`, so write
   `d ell(theta)/d theta`;
7. `S0152`: `Parmater` -> `Parameter`;
8. `S0155`: `as follows. as` -> `as follows. As`; and
9. `S0169`: `k-the parameter` -> `k-th parameter`.

Indonesian translation should repair the surfaces naturally while preserving
leading/trailing whitespace and the stable fragment boundaries.

## L07-D012 — parameter boundary is confused with data support

- stable evidence: `S0019`–`S0020`, `M0002`
- source: the estimator should not be “on the edge of allowable values,”
  followed by “the MLE is not in the support”
- proof: a support is the set of possible values of the observed random
  variable, while the relevant asymptotic regularity condition is that the
  true parameter is an interior point of the parameter space. An estimator
  takes values in the parameter space; saying that it is “not in the support”
  confuses different mathematical sets.
- proved correction: say that the true parameter lies in the interior of the
  parameter space. Preserve the source's explicit admission that its list of
  regularity conditions is incomplete.

## Explicit limitation — preserve; do not “correct” away

Segment `S0021` says the lesson does not show the full regularity-condition
list or proofs and points to Wasserman, Chapter 9.13. This is a genuine scope
limitation and not a defect. It must remain visible in Indonesian. The nearby
“ANY MLE!” claim must remain subordinate to “subject to regularity
conditions”; the translation must not manufacture omitted hypotheses or
proofs and must not erase the disclaimer.

## Correct material that must not be changed

- The MLE-equivariance calculations for Normal standard deviation and the
  binomial odds ratio are correct for their stated/interior cases.
- The Bernoulli likelihood, score, `hat(p)=xbar`,
  `I_n(p)=n/[p(1-p)]`, and symbolic Wald interval are correct.
- The final numeric Bernoulli margin and endpoints are correct despite the
  omitted factor in the intermediate equality.
- The exponential likelihood, log-likelihood, MLE, second derivative, and
  final plug-in information value are correct; only the classification,
  expectation/observation chain, missing derivative label, and reciprocal
  interval term need repair.
- The multivariate inverse-information diagonal formula is correct under
  regularity and a nonsingular total-sample information matrix.
- `M0146`–`M0148` are correct when `I(theta)` is explicitly identified as
  per-observation information.
- The geometric and Normal output-based confidence-interval arithmetic is
  internally correct. Do not replace frozen output or code bytes.

## Asset, dependency, rights, and assessment disposition

Two official same-origin images were frozen exactly:

- `A0001`: `Lesson07_files/figure-html/unnamed-chunk-1-1.png`, 51,500 bytes,
  SHA-256
  `261e8fee2ada5d25b3cf92d4fde1825dfcce67f97629120efc6d432b06a89372`;
- `A0002`: `Lesson07_files/figure-html/unnamed-chunk-6-1.png`, 49,223 bytes,
  SHA-256
  `18e14d1763554c43bcc8c31ba57756918ea7e47985abbf840f40ee3842460e65`.

Both are 1344 by 960 CRC-valid PNGs, have no trailing bytes or embedded
rights/creator marker, and inherit the page's CC BY-NC 4.0 notice because no
per-asset exception is visible. The source alt text is nonempty but generic;
two Indonesian accessibility descriptions are required downstream. No
external dependency remains.

The lesson contains six fully worked examples and no independent public
exercise or hint. Treat that as an assessment-closure gap, not as authority to
reconstruct private course questions.
