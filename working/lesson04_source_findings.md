# Penn State STAT 415 Lesson 04 — mechanically proved source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson04.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson04`
- bytes: `106614`
- SHA-256: `9fe5790e577c6ce0b808c92683aea45442187f80f74d540b20bd4514bdefc060`
- normalized document identity: `O006-PSU-005`

These findings are restricted to defects that follow directly from the frozen
source text/formulas and elementary algebra or calculus. The authority bytes
remain unchanged. Any reader correction must be additive, disclosed, and bound
to the stable IDs below.

## L04-D001 — parameter case mismatch

- location: `O006-PSU-005-M0030` in `O006-PSU-005-U0049`
- source: the likelihood is introduced as `L(p)`, but the derivative is labeled
  `dL(P)/dp`.
- proved correction: use lowercase `p` consistently: `dL(p)/dp`.

## L04-D002 — missing conditional-density delimiter

- location: `O006-PSU-005-M0073` in `O006-PSU-005-U0093`
- source: the final summand is `ln f(x_i\theta)` although the immediately
  preceding equal expression is `ln f(x_i|\theta)`.
- proved correction: restore the conditioning bar: `ln f(x_i|\theta)`.

## L04-D003 — wrong likelihood parameter in Gamma example

- location: `O006-PSU-005-M0098` in `O006-PSU-005-U0123`
- source: the Gamma model declares unknown `\theta`, but its likelihood is
  labeled `L(p)`.
- proved correction: label it `L(\theta)`.

## L04-D004 — extra logarithm in Gamma log-likelihood

- location: `O006-PSU-005-M0099` in `O006-PSU-005-U0126`
- source: `(\alpha-1)\ln(\ln\prod x_i)`.
- proof: `\ln[(\prod x_i)^{\alpha-1}] =
  (\alpha-1)\ln(\prod x_i) = (\alpha-1)\sum_i\ln x_i`.
- proved correction: remove the nested logarithm.

## L04-D005 — wrong parameter name in Geometric estimate prompt

- location: `O006-PSU-005-U0135`, especially `S0158`–`S0159` and `M0108`
- source: Example 4.6 states a Geometric model and the solution applies
  `\hat p=n/\sum x_i`, but the prompt asks for the estimate of `\theta`.
- proved correction: ask for the estimate of `p`.

## L04-D006 — unfinished numerical Gamma estimate

- location: `O006-PSU-005-M0116` in `O006-PSU-005-U0145`
- source: `(3.4+8.1+5.5)/(3(3))=` ends at the equals sign.
- proved correction: complete the exact arithmetic as `17/9` (approximately
  `1.8889`).

## L04-D007 — factorial sign in Poisson log-likelihood

- location: `O006-PSU-005-M0121` in `O006-PSU-005-U0153`
- source likelihood: `e^{-n\lambda}\lambda^{\sum x_i}/\prod x_i!`.
- source log-likelihood instead adds `+\ln(\prod x_i!)`.
- proved correction: the denominator contributes
  `-\ln(\prod x_i!) = -\sum_i\ln(x_i!)`.

## L04-D008 — reversed monotonicity and nonexistent critical solution

- locations: `O006-PSU-005-M0135`/`U0171`, `M0138`/`U0172`, and
  `S0198`/`U0173`
- source: for `L(a)=a^{-n}`, it displays `d\ell/da=-n/a`, then says setting
  this equal to zero yields `\hat a=\infty`, and calls the likelihood
  monotonically increasing.
- proof: for `a>0`, `-n/a<0` and never equals zero; `a^{-n}` is strictly
  decreasing.
- proved correction: state that the score has no interior zero and that the
  constrained maximum/supremum is governed by the support boundary.

## L04-D009 — missing Bernoulli support value

- location: `O006-PSU-005-M0155` in `O006-PSU-005-U0189`
- source indicator case: “if `y=` or `y=1`”.
- proved correction: “if `y=0` or `y=1`”.

## L04-D010 — fixed index inside Bernoulli product

- location: `O006-PSU-005-M0157` in `O006-PSU-005-U0194`
- source: `\prod_{i=1}^n p^{y_1}(1-p)^{1-y_1}` but the same display then
  produces sums over `y_i`.
- proved correction: every factor must use `y_i` (and its indicator must also
  be indexed by `i`).

## L04-D011 — malformed Bernoulli score

- locations: `O006-PSU-005-M0160`/`U0198` and `M0162`/`U0200`
- source: the derivative left side is only `d/dp`, and both numerators are
  written `\sum y_1` before the algebra switches to `\sum y_i`.
- proved correction: use `d\ell(p)/dp` and `\sum_i y_i` consistently.

## L04-D012 — unindexed Uniform indicator inside a product

- location: `O006-PSU-005-M0170` in `O006-PSU-005-U0212`
- source: `\prod_{i=1}^n a^{-1}\mathbf 1_{x\in(0,a)}`.
- proved correction: the factor indexed by `i` must contain
  `\mathbf 1_{x_i\in(0,a)}`.

## L04-D013 — Uniform endpoint contradiction

- locations: `O006-PSU-005-M0167`/`U0204` and `M0176`/`U0214`
- source: the indicator uses strict support `x\in(0,a)`, but the claimed MLE
  sets `a=\max_i X_i`.
- proof: with that strict indicator, the largest observation equals the
  excluded right endpoint and makes the likelihood zero.
- proved correction: either use a right-inclusive density convention and state
  the attained MLE, or preserve strict support and call `\max_i X_i` the
  boundary supremum rather than an attained maximizer.

## L04-D014 — Pareto endpoint inequality contradiction

- locations: `O006-PSU-005-M0183`/`U0218` and `M0185`/`U0223`
- source density support: `x\ge m`; source likelihood indicator: `x_i>m`;
  claimed estimator: `m=\min_i x_i`.
- proof: the strict indicator is zero at the claimed estimate.
- proved correction: use `x_i\ge m` consistently with the stated density.

## L04-D015 — malformed final vector component

- location: `O006-PSU-005-M0230` in `O006-PSU-005-U0270`
- source: `\hat{\theta_p}`.
- proved correction: the component is `\hat{\theta}_p`, matching
  `\hat{\theta}_1` earlier in the same tuple.

## L04-D016 — missing sign in Laplace likelihood product

- location: `O006-PSU-005-M0249` in `O006-PSU-005-U0294`
- source: the product begins with `e^{|x_i-\mu|/b}` but its final equality has
  `e^{-\sum|x_i-\mu|/b}` and the immediately preceding density also has the
  negative exponent.
- proved correction: restore the negative sign in every product factor.

## L04-D017 — contradictory derivative at the absolute-value kink

- location: `O006-PSU-005-M0259` in `O006-PSU-005-U0306`
- source piecewise derivative assigns `-1` when `x_i\ge\mu` and `+1` when
  `x_i\le\mu`; both cases apply at equality.
- proof: `|x_i-\mu|` is not differentiable at `x_i=\mu`.
- proved correction: use strict inequalities away from the kink and a
  subgradient/set-valued argument at equality when deriving the median MLE.

## L04-D018 — unclosed Laplace estimator expression

- location: `O006-PSU-005-M0273` in `O006-PSU-005-U0315`
- source: the final `|x_i-\operatorname{median}(...)` lacks its closing
  vertical bar and ends with mismatched parentheses.
- proved correction: close the absolute value and the estimator tuple, e.g.
  `\hat b=n^{-1}\sum_i|x_i-\hat\mu|`.

## L04-D019 — Gamma scale parameter changes name

- locations: `O006-PSU-005-U0318` (`S0353`–`S0356`, `M0275`–`M0277`) and
  `O006-PSU-005-M0278` onward
- source: Example 4.16 defines the parameter vector `(\alpha,\beta)`, but the
  likelihood, log-likelihood, and both score equations use `\theta` as the
  scale parameter.
- proved correction: choose one scale-parameter name and use it throughout.

## L04-D020 — missing differential in Gamma score label

- location: first line of `O006-PSU-005-M0282` in `O006-PSU-005-U0323`
- source: `\ell(\underline\theta)/d\theta`.
- proved correction: write `d\ell(\underline\theta)/d\theta` (or the
  corresponding partial derivative).

## L04-D021 — omitted term in Gamma alpha score

- location: second line of `O006-PSU-005-M0282` in `O006-PSU-005-U0323`
- source log-likelihood includes `-n\alpha\ln\theta`, while its derivative
  with respect to `\alpha` omits the resulting `-n\ln\theta` term.
- proved correction: add `-n\ln\theta` to the alpha score.

## Asset disposition

The semantic main contains exactly one direct instructional dependency:
`assets/STAT-415-SEC-1-15.svg`, stable ID `O006-PSU-005-A0001`, used once as
an image and once as a same-URL lightbox target. Its alt text is “Natural
logarithm graph.” The normalized source records the exact official URL and
reference topology, but the SVG bytes are not part of this normalization
boundary. `working/lesson04_asset_inventory.json` therefore truthfully requires
a separate byte/rights freeze before an offline reader may claim asset closure.

## Additional independently admitted findings

The complete mathematical audit in `working/lesson04_math_audit.md` checked the
entire semantic main independently of the mechanical normalizer. The exact SVG
freeze and translation partitions then supplied the remaining surface evidence.
The following findings are also admitted. They do not mutate the frozen HTML or
SVG authority; they are repaired only in the Indonesian derivative and recorded
in the cumulative correction backend.

## L04-D022 — the graph repeats the first coordinate label

The frozen SVG places `x_1` below both horizontal coordinates, while the left
axis labels and geometry use `f(x_1)` and `f(x_2)`. The second coordinate is
therefore `x_2`. The derivative changes only that second subscript and preserves
the byte-identical official SVG separately.

## L04-D023 — likelihood is not a probability distribution over the parameter

Units `U0031`, `U0085`, and `U0333` call likelihood the joint probability
distribution of the sample. For observed data it is the joint PMF or density
evaluated at that data and viewed as a function of the parameter; it need not
integrate or sum to one over the parameter. Translation segments `S0021`,
`S0030`, `S0033`–`S0034`, `S0099`, and `S0368`–`S0369` state the correct
distinction.

## L04-D024 — the monotone-log argument names the wrong function

Unit `U0058` says `x_1<x_2` implies `f(x_1)<f(x_2)` and presents that as the
reason logarithms preserve the maximizer. The needed fact is that, for positive
arguments, `x_1<x_2` implies `ln(x_1)<ln(x_2)`. Hence applying `ln` to a
positive likelihood preserves its ordering and argmax; zero likelihood values
may be assigned log-likelihood `-infinity`. Segments `S0064`–`S0069` state this
valid argument.

## L04-D025 — the Binomial second-derivative claim omits boundary samples

The displayed substitution and strict interior maximum are valid only when
`0 < sum_i x_i < 10n`. If every observation is zero or ten, the MLE is the
parameter-space boundary `p=0` or `p=1`, respectively, and the displayed
interior substitution is undefined. Segments `S0085`–`S0088` add the necessary
qualification without deleting the source derivation.

## L04-D026 — a critical point is not automatically an MLE

Units `U0082`, `U0095`, `U0096`, and the later multiparameter recipe promote a
critical point directly to an MLE. A critical point can be a minimum, saddle,
nonglobal maximum, or absent; boundaries and parameter-dependent support must
also be checked. The shortcut is valid only after concavity/unimodality and an
interior maximum are established. The target qualifies every affected recipe.

## L04-D027 — estimator and observed estimate are collapsed

Definition 4.2 writes the maximizing functions of lowercase observations both
when defining the random estimator and when reporting its observed value. The
estimator must use `u_i(X_1,...,X_n)` and its realization
`u_i(x_1,...,x_n)`. The target repairs math nodes `M0063` and `M0065` and uses
`penduga` versus `nilai dugaan` consistently in the prose and summary.

## L04-D028 — the Gamma derivation says to solve for the wrong parameter

Unit `U0130` asks the reader to solve the Gamma score for `p`, although the
model and every equation vary `theta`. Math node `M0103` must be `theta`.

## L04-D029 — the Poisson score omits the differentiated function

Math node `M0122` has only `d/dlambda` on its left side. It is the derivative
of the log-likelihood and must read `d ell(lambda)/d lambda`.

## L04-D030 — the shifted-Uniform endpoint convention is inconsistent

Example 4.13 announces the open interval `(3c,10)` but its density, likelihood,
and attained estimate all use inclusive endpoint inequalities. The derivative
adopts the density version on `[3c,10]`, which defines the same continuous
distribution while making the stated maximizer attained, and states the
nonempty-interval parameter condition `c<10/3`.

## L04-D031 — monotonicity alone does not select an order statistic

Unit `U0231` says increasing likelihood usually means the sample minimum and
decreasing likelihood the sample maximum. The relevant order statistic is
determined jointly by the monotonic direction and the feasible-set boundary
induced by the support. Segments `S0268`–`S0271` state this qualified rule.

## L04-D032 — the Laplace location MLE need not be unique

Beyond the kink defect in `D017`, the source treats the median as a unique
differentiable solution. Any minimizer of `sum_i |x_i-mu|` is an MLE; for even
sample size the full interval between the two central order statistics may
maximize the likelihood. The corrected formula uses a set-valued median and
the prose uses the subgradient optimality condition.

## L04-D033 — the two-parameter Gamma root is described imprecisely

The source says the Gamma function is “not analytically tractable” and that no
analytic solution is possible. With scale `theta`, the scale score gives
`theta-hat = x-bar/alpha-hat`; the remaining shape equation is
`ln(alpha-hat)-psi(alpha-hat) = ln(x-bar) - n^{-1} sum_i ln(x_i)` and generally
requires a numerical root. The target states this precise reduction.

## L04-D034 — five unambiguous prose/markup typos

The source contains literal `** likelihood**`, `definition og`, `0ne`,
`The the`, and two instances of `indication function`. Their intended surfaces
are likelihood, definition of, one, the, and indicator function. The
translation repairs them without changing content.

## L04-D035 — Bernoulli has a PMF, not a PDF

Example 4.10 repeatedly calls the Bernoulli probability mass function a PDF.
Segments `S0218`, `S0220`, `S0221`, and `S0223` use PMF consistently.

## Final disposition

All `L04-D001`–`L04-D035` findings are locally testable mathematical, logical,
asset-label, or surface defects. The official HTML and SVG remain immutable.
Every changed target surface must receive a stable correction record and a
source/target hash; no upstream message is sent during production.
