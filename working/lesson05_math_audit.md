# Lesson 05 mathematical/source audit

## Authority and audit boundary

- Authority: `authority/upstream/stat415/Lesson05.html`
- Official document represented: Penn State STAT 415, Lesson 05, *Maximum
  Likelihood Estimation (MLE) (Part II)*
- Authority bytes: 190,308
- Authority SHA-256:
  `dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`
- Completely audited instructional boundary: `<main
  id="quarto-document-content">`, source lines 546–1890, 132,217 UTF-8 bytes
- Audit disposition: usable instructional source, but the derivative must not
  reproduce the mathematical, computational, reproducibility, and numerical
  optimization defects below.

## High-confidence defects and exact corrections

1. **The generic `dXXX` explanation conflates densities, masses, and
   likelihoods** — `#r-functions-for-statistical-distributions`, lines
   1086–1092. A `d*` function returns a density value for a continuous model or
   a probability-mass value for a discrete model. It becomes one factor of a
   likelihood only after observations are held fixed and its parameter is
   treated as variable. Correct the prose to distinguish these three roles;
   do not describe every `dXXX` value as a probability density or a
   likelihood.

2. **The Normal simulation assigns one draw to `x`, then repeatedly claims
   that `x` contains ten draws** — `#examples-from-the-gaussian-normal-distribution`,
   lines 1106–1193. Line 1110 prints ten unassigned draws, but line 1121 uses
   `x=rnorm(n=1,...)`. Consequently the displayed `dnorm(x,...)`, product, and
   log-likelihood outputs contain one contribution even though lines
   1149–1169 use \(X_1,\ldots,X_{10}\). The intended correction is
   `x=rnorm(n=10, mean=3, sd=2)`, followed by regeneration of all dependent
   vector, product, and log-density outputs. The alternative is to retain
   `n=1` and change every “ten” and \(X_1,\ldots,X_{10}\) statement to one;
   the current mixed state is impossible.

3. **Most simulated outputs are not reproducible** — lines 1096–1299. The
   first Normal and Exponential simulations call `rnorm`/`rexp` without a
   preceding `set.seed`, yet the document presents exact downstream values,
   summaries, CDF estimates, likelihoods, and plots. Add a documented seed
   before each independent simulation or freeze the generated vectors
   explicitly. Example 5.2 correctly uses `set.seed(123)` and is the model to
   follow.

4. **“Likelihood” is repeatedly written as a function of random data rather
   than of a parameter given fixed data** — lines 1089, 1149–1169, and 1285.
   For example, `L(X_1,...,X_10)=prod f_X(X_i)` is a joint density expression,
   not likelihood notation. Write, for fixed observations \(\mathbf x\),
   \[
   L(\mu,\sigma;\mathbf x)=\prod_{i=1}^{10}
   f(x_i\mid\mu,\sigma),
   \qquad
   \ell(\mu,\sigma;\mathbf x)=\sum_{i=1}^{10}
   \log f(x_i\mid\mu,\sigma).
   \]
   When the parameter is fixed at a demonstration value, call the result a
   joint density, not “the likelihood of the random variables.”

5. **The visible grid-search program never fills `lik.vals`** —
   `#mle-through-grid-search`, lines 1392–1423. The source creates an all-`NA`
   vector, describes a loop, then jumps directly to a plot and
   `which.max(lik.vals)`. As reader-visible code, it cannot produce the shown
   index or estimate. Insert the missing computation, for example:
   ```r
   for (i in seq_along(theta.vals)) {
     lik.vals[i] <- lik.exp.2(theta.vals[i], x)
   }
   plot(theta.vals, lik.vals, type = "l")
   ```
   before calling `which.max`.

6. **A grid maximizer is called the exact MLE** — lines 1346 and 1418–1437.
   The exact notation is
   \[
   \hat\theta=\operatorname*{arg\,max}_{\theta>0}
   L(\theta;\mathbf x).
   \]
   The value 8.9 is only the maximizer over the chosen 0.1-spaced grid, hence
   an approximation. For these data, \(n=15\), \(\sum x_i=133\), and the exact
   exponential-mean MLE is \(\bar x=133/15=8.866666\ldots\).

7. **The score function is defined as an equation instead of a function** —
   `#newtons-method-approach-idea`, lines 1478–1480. Define
   \(h(\theta)=\ell'(\theta)\), then state that the task is to solve
   \(h(\theta)=0\). The source incorrectly writes
   \(h(\theta)=\ell'(\theta)=0\). The next expression is also missing a closing
   parenthesis; it must be
   \(h(\theta^{(0)})=\ell'(\theta^{(0)})\).

8. **The Newton narrative takes the tangent of the wrong function** — lines
   1481–1498. The displayed tangent and update apply to the score
   \(h=\ell'\), not to the log-likelihood \(\ell\). Correct the narrative to:
   evaluate \(h(\theta^{(0)})\), take the tangent to \(h\), use its x-intercept
   as \(\theta^{(1)}\), and iterate. A score root still requires a maximum and
   domain check; Newton’s method itself does not prove that the root maximizes
   \(\ell\).

9. **The Newton iteration index skips the first update** — lines 1514–1518.
   Given \(\theta^{(0)}\), the recurrence
   \(\theta^{(t+1)}=\theta^{(t)}-h(\theta^{(t)})/h'(\theta^{(t)})\)
   begins at \(t=0\), not \(t=1\).

10. **The exponential log-likelihood drops its parameter from density
    notation** — lines 1524–1528. Use
    \[
    \ell(\theta;\mathbf x)
      =\sum_{i=1}^n\log f(x_i\mid\theta)
      =\sum_{i=1}^n\left[-\log\theta-\frac{x_i}{\theta}\right],
      \qquad \theta>0,
    \]
    not `f_X(x_i,theta)` in one expression followed by parameter-free
    `f_X(x_i)`.

11. **The presentation risks identifying `optim` with Newton’s method** —
    lines 1523 and 1665–1668. The hand-coded recurrence in lines 1531–1623 is
    Newton–Raphson. Base R’s `optim()` defaults to Nelder–Mead when no `method`
    is supplied; it is not executing that Newton update. State this separation
    explicitly. If Newton is intended, use a Newton implementation with the
    supplied score/Hessian; if `optim` is intended, name its chosen method.

12. **Example 5.1 reverses exponential rate and mean/scale** — `#exm-mle1`,
    lines 1679–1719. The prose says \(\theta\) is a rate, but the code uses
    `dexp(..., rate=1/theta)`, so \(\theta\) is the mean/scale. These data have
    \[
    \widehat{\text{mean}}=\bar x=\frac{133}{15}=8.866666\ldots,
    \qquad
    \widehat{\text{rate}}=\frac{15}{133}=0.11278195\ldots.
    \]
    Retain the code and change every “rate parameter \(\theta\)” to
    “mean/scale parameter \(\theta\), with rate \(1/\theta\).” Alternatively,
    retain “rate” and change the code to `rate=theta`, in which case the MLE is
    0.11278195. Do not mix these parameterizations.

13. **Positive parameter domains are not enforced during optimization** —
    lines 1670, 1714–1729, and 1839–1856. A positive starting value does not
    prevent `optim` from trying a nonpositive exponential mean or Normal
    variance. Use a log parameterization, e.g. \(\eta=\log\theta\) and
    \(\xi=\log\sigma^2\), or a bounded method such as `L-BFGS-B` with strictly
    positive lower bounds. Merely choosing a positive initial value does not
    make the objective valid over the optimizer’s search path.

14. **The instruction to ignore most `optim` warnings is unsafe and
    mathematically wrong** — line 1729. Warnings caused by invalid trial
    parameters expose an incorrectly unconstrained objective; they can also
    accompany nonfinite values, failed finite differences, or unreliable
    convergence. Inspect and remedy each warning. For this example, enforce
    positivity rather than telling the learner to ignore domain violations.

15. **The reported objective-value verification uses the reciprocal
    parameter** — line 1757. With the implemented mean parameterization,
    `nll.exp(8.865625,x)` is approximately 47.73448. The printed call
    `nll.exp(0.112793,x)` is not equivalent: it is approximately 1146.42 under
    the actual function. The value 0.112793 would make sense only as the rate
    under a different objective.

16. **`out$counts` is misdefined and its displayed value is misreported** —
    lines 1737–1748 and 1758. `optim` reports counts of calls to the objective
    and gradient, not the number of algorithmic iterations. The shown output
    records 30 objective calls and `NA` gradient calls, while the prose claims
    32 iterations.

17. **`convergence == 0` is treated as proof that an MLE is trustworthy** —
    lines 1759 and 1877. Code 0 means `optim` satisfied its own termination
    condition; it does not prove a global optimum, adequate numerical
    accuracy, valid parameter domain, finite objective, or correct model/code.
    A valid conclusion additionally checks the domain, objective value,
    sensitivity to starts/method/tolerances, and a gradient/Hessian or known
    analytic benchmark. A nonzero code requires diagnosis rather than the
    source’s binary trust rule.

18. **The comparison of the two exponential runs gives neither printed
    estimate correctly** — lines 1770–1787. The outputs are 8.865625 and
    8.86875; the prose instead says 8.6875 and 8.65625. Correct the prose and
    note that both are loose numerical approximations to
    8.866666\(\ldots\).

19. **The Normal objective has the same unguarded-domain defect and should be
    benchmarkable exactly** — `#exm-thenormaldistributionmle`, lines
    1839–1877. `sqrt(s2)` is invalid for \(s^2\le0\), yet the optimizer is
    unconstrained. Parameterize `log_s2` and pass
    `sd=exp(log_s2/2)`, or impose a positive bound. For a Normal model with
    both parameters unknown, the exact benchmarks are
    \[
    \hat\mu=\bar y,
    \qquad
    \widehat{\sigma^2}=\frac1n\sum_{i=1}^n(y_i-\bar y)^2.
    \]
    From the displayed rounded values these are approximately -3.188415 and
    14.885449, so the numerical result should be checked against them rather
    than accepted solely from `convergence=0`.

20. **The Normal mean estimate is labeled with the wrong symbol** — line
    1877. The first parameter is \(\mu\), so write
    \(\hat\mu_{\mathrm{ML}}=-3.186135\) for the displayed numerical result,
    not \(\hat\theta_{\mathrm{ML}}\). Retain a separate symbol for the full
    parameter vector if desired.

## Unambiguous source and surface defects

- The title categories at lines 553–559 are stale Lesson 03 topics
  (`Unbiased Estimation`, `Factorization`, `Sufficiency`, and `Method of
  Moments`) rather than Lesson 05’s R/numerical-MLE content.
- Line 900 says character values need “parentheses”; it means quotation marks.
  Its “Section 3.2” cross-reference should point to the local scalar/vector
  subsection, 5.1.2.
- Line 1117 has an unmatched closing quotation mark after “future use”.
- Line 1446 says “Interactively finding”; the intended word is “Iteratively”.
- Line 1480 says “tangent like”; the intended phrase is “tangent line”.
- Line 1531 says R cannot directly calculate derivatives. That is too broad:
  base R has limited symbolic facilities such as `D`/`deriv`, and numerical
  derivative tools also exist. Say that this example derives and codes the
  derivatives manually.
- Line 1730 needs the possessive `optim`’s`, and line 1758 should say “stopping
  criterion”, not “criteria”.
- Both “Video 5.1” and “Video 5.2” embed the exact same Kaltura URL and use the
  same DOM id `kaltura_player` (lines 1463–1472 and 1499–1508). Both wrappers
  also contain malformed CSS `padding-bottom:2 %>% %`. Deduplicate the surface
  or identify genuinely distinct assets, assign unique IDs, and provide a
  static textual derivation/fallback.
- The main DOM also duplicates each of the IDs `fig-boxplotcornyield`,
  `fig-histogramcornyield`, and `fig-scattercornyield` between a container and
  its image. Normalize to one unique ID per element.
- `Lesson05_files/figure-html/unnamed-chunk-28-1.png` has no alt text. The five
  Newton sequence images all reuse the vague alt text “A series of graphs”; a
  derivative should describe the iteration-specific point/tangent/root shown
  in each frame.

## Source-surface census

- 22 `<section>` elements.
- One H1; four H2 surfaces (Overview, 5.1, 5.2, 5.3); 14 H3 surfaces
  (Objectives, eight R subsections, and five numerical-MLE subsections); four
  H4 distribution/help subsections.
- Two structured examples (5.1 Exponential and 5.2 Normal); zero structured
  definitions; zero `Solution` headings; zero public exercise/solution sets.
- 97 reader-visible R source-code blocks, 79 stdout blocks, and eight graphical
  output blocks.
- 98 inline-math and ten display-math surfaces.
- 14 distinct image sources grouped under 11 figure captions; one image has no
  alt text.
- Two remote iframes, both pointing to the same Kaltura video; one callout.

## Coverage

1. R arithmetic and logarithms.
2. Scalars, vectors, vectorized operations, indexing, logical selection, and
   `which`.
3. Data frames, grouped summaries, variance/standard deviation, boxplots,
   histograms, and scatterplots.
4. R’s `r`/`d`/`p`/`q` distribution-family convention, illustrated with Normal
   and Exponential simulation, densities, CDFs, quantiles, and likelihood-like
   products.
5. Exponential-mean MLE by a discrete grid search.
6. Newton–Raphson as root finding for the likelihood score, including a manual
   Exponential update.
7. Negative-log-likelihood minimization with `optim`, using one-parameter
   Exponential and two-parameter Normal examples.

## Translation traps

- Distinguish *density/mass*, *joint density/mass*, *likelihood*,
  *log-likelihood*, and *negative log-likelihood*; they are not interchangeable.
- Distinguish the Exponential **rate** \(\lambda\) from its **mean/scale**
  \(\theta=1/\lambda\). The source’s central Example 5.1 currently reverses
  them.
- Distinguish an exact MLE from a grid approximation and from an optimizer’s
  tolerance-dependent numerical estimate.
- Preserve uppercase random variables versus lowercase observed realizations,
  and estimator versus estimate.
- Translate the prose around R, but preserve executable identifiers, function
  names, argument names, operators, output keys (`$par`, `$value`, `$counts`,
  `$convergence`), decimal points, and string literals unless a deliberate
  locale-safe code adaptation is tested.
- Render *iteration* and *function evaluation* as different concepts;
  `optim`’s `$counts` is not an iteration count.
- Treat Newton–Raphson as a root finder for the score and `optim()`’s default
  Nelder–Mead routine as a different algorithm.
- Preserve domain constraints explicitly: Exponential means/rates and Normal
  variances are positive; a positive starting value alone is not a constraint.
- Seed every simulation whose exact output is retained. Do not translate
  frozen random outputs while leaving code that cannot reproduce them.
- Keep remote no-sound video surfaces optional and provide the complete static
  mathematical explanation; do not make an external iframe necessary to
  understand the algorithm.
