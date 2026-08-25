# Penn State STAT 415 Lesson 08 — mathematical, executable, and source audit

Audited the complete instructional `main#quarto-document-content` in
`authority/upstream/stat415/Lesson08.html` without changing the authority.

- official URL: `https://online.stat.psu.edu/stat415/Lesson08`
- frozen bytes: `135460`
- frozen SHA-256:
  `7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`
- normalized document identity: `O006-PSU-009`
- mathematics: 140 inline and 16 display surfaces (156 total)
- executable material: 28 `pre` nodes, 49 `code` nodes, 20 embedded
  code-label styles, 4 stochastic code blocks, and 8 fixed output blocks
- structured instruction: 13 sections, 14 headings, one example, four
  instructional PNGs, no tables, and no independent exercise/solution pair
- dependencies in the instructional main: four same-origin PNG references and
  no script, iframe, audio, video, object, embed, or download dependencies

The statistical conclusions below use the frozen formulas and code as primary
evidence. Supporting implementation checks use the official R documentation
for [`optim`](https://www.stat.ethz.ch/R-manual/R-devel/library/stats/html/optim.html),
[`mle`](https://stat.ethz.ch/R-manual/R-patched/library/stats4/html/mle.html),
and [R random-number state](https://stat.ethz.ch/R-manual/R-devel/library/base/help/Random.html).
The percentile method is also checked against the
[NIST bootstrap documentation](https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/bootplot.htm),
which explicitly treats it as a first-order interval rather than a universally
valid exact construction.

## Section 8.1 — bootstrap confidence intervals

The four-step description is directionally correct: fit an approximation to
the data-generating law, simulate or resample data sets, recompute a statistic,
and use the resulting empirical distribution. The source repeatedly blurs the
objects, however. `theta` is the parameter, `hat(theta)` is an estimator before
data are observed and a realized estimate after substitution of observed data,
and `hat(theta)^(m)` is the estimate from bootstrap data set `m`. The three
headings that write `{theta^(m)}` need hats. The introductory `m` data sets and
`hat(theta)_i`, `i=1,...,m`, should use the lesson's later convention `M` and
bootstrap index `m`.

The generic percentile interval in math surface `M0053` has an extra opening
brace in the upper-quantile argument. Its intended form is

```text
( qhat_.025({hat(theta)^(1),...,hat(theta)^(M)}),
  qhat_.975({hat(theta)^(1),...,hat(theta)^(M)}) ).
```

This is a percentile-bootstrap interval, not a model-free exact 95% interval.
Its coverage requires bootstrap consistency for the statistic and problem;
bias, skewness, boundaries, weak identification, and nonsmooth statistics can
make its coverage poor. That qualification is omitted rather than disproved in
the generic algorithm. The later Pareto-location example supplies a concrete
case where the method is invalid, discussed below.

### Asymptotic Normal interval for Student-t degrees of freedom

The fixed 25-value data vector and the printed numerical estimate near
`df.hat=6.63125` are mutually plausible. The displayed interval is the Wald
calculation formed from the inverse numerical Hessian. It is reasonable for the
lesson to use its negative lower endpoint as evidence that the Gaussian
approximation is poor here.

Two distinctions must be preserved:

1. `out$hessian` is the numerical Hessian of the **negative observed
   log-likelihood** at the solution. It estimates observed information
   `J_n(hat(theta))=-ell_n''(hat(theta);x)`; it is not the expected Fisher
   information `I_n(theta)=-E_theta ell_n''(theta;X)` defined later.
2. A Wald interval based on either consistent information estimate remains an
   asymptotic approximation under the applicable regularity conditions. An
   optimizer-returned Hessian and convergence code are numerical evidence, not
   a theorem that those conditions hold.

The code also leaves `df>0` unenforced. Official `optim` documentation exposes
box constraints through `method="L-BFGS-B"`, `lower`, and `upper`, and returns a
`convergence` component that the lesson never checks. A log-`df`
parameterization is another valid repair. Suppressing warnings inside 1,000
bootstrap fits without retaining convergence/domain diagnostics is not a
reproducible inferential workflow.

### Parametric bootstrap example

The example reintroduces the data as `x`, but its MLE block calls
`optim(...,y=y)`. It succeeds only when the earlier, same-valued object `y`
remains in the global environment. The local and self-contained call is
`optim(...,y=x)`.

The simulation and refitting steps otherwise implement the stated parametric
bootstrap idea. They do not supply `set.seed`, `RNGversion`, a package version,
or a session record, so the 1,000 estimates, histogram, and quantiles are not
reproducible from the page. R's official RNG documentation says that different
sessions generate different state by default and recommends `set.seed` for
reproduction.

The fixed output and the following prose cannot both describe the same run:

```text
printed quantiles:  (2.612500, 1.342177e7)
prose interval:     (2.5789,   2.68e7)
```

A derivative must choose and record one seeded run, then keep its code, plot,
printed quantiles, and prose byte-consistent. Merely copying the prose numbers
would not repair reproducibility.

### Nonparametric bootstrap and empirical distribution

For observations `x_1,...,x_n`, the empirical mass at a distinct value `x` is

```text
P_n({x}) = (1/n) sum_(i=1)^n 1{x_i=x}.
```

The source instead assigns `1/n` whenever `x=x_i` for some `i`. That is correct
only when all observed values are distinct and contradicts the preceding claim
that the support comprises unique values. Sampling observation indices with
replacement, as the R code does, automatically gives the correct multiplicity.

The restated MLE block again defines `x` but fits the stale `y`. It has the same
missing domain/convergence controls and RNG state as the parametric example.
Its fixed output and prose also disagree:

```text
printed quantiles:  (3.339766, 6.710887e6)
prose interval:     (3.2688,   6.8787e6)
```

## Section 8.1.4 — template code

Both one-parameter templates allocate `theta.hat.vals=rep(NA,n)` and then fill
indices `1:M`. The result vector must be allocated with `M`. R silently extends
the vector in the shown `M>n` configuration, but the template is still wrong:
if `M<n`, unused trailing `NA` values remain and contaminate `quantile` unless
removed. The Pareto template repeats the defect for both result vectors.

The prose introducing the two templates has a corrupted inline list:
`data b. ... model.c. ... d.` in the first panel and `data b. ... model.c.` in
the second; the first also says `opti` rather than `optim`. These are reader
surface defects, not R semantics.

## Section 8.1.5 — two-parameter Pareto example

The lesson loads `EnvStats` and calls `EnvStats::dpareto`. That implementation
has positive `location` and `shape` parameters and support
`[location,infinity)`, as documented in the official
[EnvStats package manual](https://stat.ethz.ch/CRAN/web/packages/EnvStats/EnvStats.pdf).
The source's `(L,infinity)` therefore excludes an endpoint that its own code
includes. Write `[L,infinity)`.

For the implemented Pareto-I model, the maximum-likelihood location estimate is
the sample minimum. Here the observed minimum is `5.06`. Every nonparametric
bootstrap resample is drawn from observed values, so every resample minimum is
at least `5.06`. By contrast, for a continuous Pareto sample the observed
minimum is strictly greater than the true `L` with probability one. Therefore
any percentile interval whose lower endpoint is a bootstrap resample minimum
cannot cover `L`; the reported `(5.06,5.28)` location interval has zero nominal
coverage in the model, apart from a probability-zero equality event. This is a
proved nonregular-endpoint failure, not merely an omitted caveat.

The Pareto optimizer also fails to constrain `L>0`, `a>0`, and `L<=min(x)`, and
does not retain convergence diagnostics. The source's own density function
throws an error for nonpositive `L` or `a`. A robust derivative should use the
analytic MLE or an explicitly constrained/transformed parameterization and
explain that ordinary iid percentile bootstrap is not valid for the endpoint.

The printed shape interval and prose differ:

```text
printed quantiles:  (1.277910, 2.270643)
prose interval:     (1.2912,   2.2905)
```

The location output `(5.06,5.28)` does match its prose, but the inferential
claim is invalid for the reason above.

## Section 8.2 — Fisher information and the delta method

The source states an exact-looking law

```text
hat(theta) ~ N(theta_true, 1/I(hat(theta)_ML)).
```

This combines a limiting theorem with a random plug-in variance. A rigorous
scalar statement, with `I_1` denoting per-observation expected information, is

```text
sqrt(n)(hat(theta)-theta_0) ->d N(0, I_1(theta_0)^(-1)),
```

under consistency, an interior identifiable parameter, differentiability and
integrability conditions that justify information identities, nonsingular
information, and the other relevant regularity assumptions. Equivalently, an
approximate unscaled law may use full-sample information `I_n=n I_1`, but the
convention must be defined. `I_n(hat(theta))` or observed
`J_n(hat(theta))` is then a plug-in estimate for constructing a standard error.
The lesson omits these regularity and scaling conventions and later calls the
same symbol both expected and observed information.

For a differentiable scalar transformation, the first-order delta method is

```text
sqrt(n){g(hat(theta))-g(theta_0)}
  ->d N(0, [g'(theta_0)]^2 I_1(theta_0)^(-1)).
```

Invertibility of `g` is not required. If `g'(theta_0)=0`, the first-order limit
is degenerate and a higher-order method may be needed; that is different from
requiring `g` to be one-to-one. The derivative at `hat(theta)` is a consistent
plug-in for the estimated standard error, not the derivative that belongs in
the limiting variance itself. Absolute-value signs are harmless after
squaring, but ordinary multiplication should be typeset rather than the source
asterisk.

Transforming each bootstrap replicate is computationally straightforward and
does not require invertibility. The source goes too far in saying bootstrap has
“no restrictions” on `g`: validity still depends on the statistic,
transformation, resampling scheme, and regularity. The summary's phrase
“without strict distributional assumptions” also cannot describe the
parametric bootstrap, which explicitly assumes and fits a distribution family.

## Findings versus omitted assumptions

The following are outright formula, code, output, or model-specific defects:

- `L08-D001`–`L08-D009`: estimator notation, malformed braces, empirical PMF,
  stale data objects, vector sizes, unguarded optimization, absent stochastic
  state, mismatched fixed outputs, and expected/observed information;
- `L08-D011`: invertibility is not a delta-method condition;
- `L08-D013`–`L08-D017`: Pareto support, invalid endpoint interval,
  accessibility, exposed editorial notes, and mechanical/cross-reference
  defects.

`L08-D010` includes both inaccurate asymptotic notation and omitted regularity
and scaling conventions. `L08-D012` corrects unconditional bootstrap
overclaims. The generic percentile algorithm itself is not declared false;
its missing validity conditions are recorded, while the Pareto endpoint is the
separate proved counterexample `L08-D014`.

## Calculations and claims that must not be “fixed”

- The parametric and nonparametric resampling algorithms are valid high-level
  descriptions once their conditions and notation are repaired.
- A negative lower endpoint from an unconstrained Gaussian Wald approximation
  can occur even though the true `df` is positive; the source correctly uses
  this as a warning about approximation quality.
- Direct empirical `.025` and `.975` quantiles implement the percentile
  bootstrap method. The method is approximate and sometimes invalid, but the
  quantile operation itself is not an algebra error.
- The summary delta formula with `[g'(theta)]^2 Var(hat(theta))` has the correct
  first-order scalar structure when read as an approximation and paired with
  the missing conditions.
- Applying `g` to every bootstrap estimate does not require `g` to be
  invertible.

## Figures, rights, and accessibility

All four official same-origin PNGs are frozen byte-for-byte under
`authority/assets/stat415/lesson08/`, with identities and rights disposition in
`authority/LESSON08_ASSET_MANIFEST.csv` and
`working/lesson08_asset_closure.json`. Each is 1344 by 960 pixels; their total
is 213,692 bytes. PNG signatures, chunk lengths, CRCs, dimensions, EOF, and
embedded rights/creator marker absence were checked. Each contains `iCCP` and
`eXIf` metadata chunks but no embedded copyright, creator, author, license, or
rights marker. The page footer applies CC BY-NC 4.0 except where otherwise
noted, and no per-image exception appears in the instructional main.

Visual census:

1. Figure 8.1 is a six-bin histogram of 25 `y` observations from about -2.3 to
   2.6, concentrated between -1 and 1.
2. Figure 8.2 is a strongly right-skewed histogram of 1,000 parametric
   bootstrap `df` estimates, with sparse extremes near 28 million.
3. Figure 8.3 is an even more concentrated, strongly right-skewed histogram of
   1,000 nonparametric bootstrap `df` estimates, again with sparse extremes
   near 28 million.
4. Figure 8.4 is a strongly right-skewed histogram of 40 Pareto observations;
   27 are below 10 and one is near 66.

The four source alternatives are generic, omit axes/distribution shape and the
inferential point, and Figure 8.3 misspells “bootstrap” as “boostrap.” Every
visible caption is only `Fig 8.x`; every image is forced to 70% inline width.
Supply complete Indonesian alternatives or adjacent descriptions, retain the
figure numbers as labels rather than descriptions, center the figures, and let
them use available reader width. Both code-tab panels must remain available in
an offline reader without relying on Bootstrap JavaScript.

## Translation traps

- Preserve `theta`, `hat(theta)`, and `hat(theta)^(m)` as parameter, estimator/
  realized estimate, and bootstrap estimate respectively.
- Use `M` for the number of bootstrap repetitions, `m` for an index, and `n`
  for observations per data set.
- Distinguish expected Fisher information from observed information and from a
  numerical Hessian returned by `optim`.
- Mark convergence with `->d` and finite-sample approximations with
  “approximately”; do not translate asymptotic notation as an exact law.
- Translate the delta-method condition as differentiability/smoothness, not
  invertibility.
- Keep “sample bootstrap” for a resampled data set distinct from a “bootstrap
  replicate/estimate” of a statistic.
- Preserve the implemented Pareto support `[L,infinity)` and explicitly warn
  that the ordinary nonparametric percentile interval is invalid for `L`.
- Preserve every executable R identifier (`optim`, `set.seed`, `df.hat`,
  `theta.hat.vals`, `sim.data`) even when surrounding code comments are
  translated later.
