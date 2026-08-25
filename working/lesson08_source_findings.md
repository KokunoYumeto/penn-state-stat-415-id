# Penn State STAT 415 Lesson 08 — high-confidence source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson08.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson08`
- bytes: `135460`
- SHA-256:
  `7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`
- normalized document identity: `O006-PSU-009`
- corroborating audit: `working/lesson08_math_audit.md`

Only findings demonstrated by the frozen formulas, code, fixed outputs, model
support, or deterministic DOM/asset inspection are registered. The census has
17 stable IDs. Missing assumptions are labeled as such rather than silently
promoted to algebraic errors.

## L08-D001 — parameter, estimator, and bootstrap estimate notation is conflated

- locations: lines 585–586, 672, 691, 712, 750, 828, and 868
- source alternates `m`/`M`, calls `hat(theta)` the parameter, and writes the
  three bootstrap-estimate headings as `{theta^(m)}` without hats
- correction: estimate parameter `theta` with `hat(theta)` and write each
  bootstrap estimate as `hat(theta)^(m)`, for `m=1,...,M`

## L08-D002 — percentile interval has an extra opening brace

- location: line 697, math `O006-PSU-009-M0053`
- source writes `qhat_.975{{hat(theta)^(1),...}`
- correction: give both empirical quantiles one matched set of braces

## L08-D003 — empirical PMF ignores duplicate multiplicity

- location: line 811, math `O006-PSU-009-M0084`
- source assigns mass `1/n` to every distinct observed value
- correction: use `n^(-1) sum_i 1{x_i=x}`; this reduces to `1/n` only when the
  observed value occurs once

## L08-D004 — restated t examples fit a stale data object

- locations: lines 721 and 838
- both sections reintroduce the vector as `x`, then call `optim(...,y=y)`
- correction: call `optim(...,y=x)`; do not rely on the earlier global `y`

## L08-D005 — bootstrap result vectors are sized by n rather than M

- locations: lines 947, 983, and 1058–1059
- all three affected blocks allocate `rep(NA,n)` and then fill `1:M`
- correction: allocate each result vector with `rep(NA,M)`

## L08-D006 — optimizer domains and diagnostics are unguarded

- locations: lines 622–630, 716–724, 833–841, and 1043–1069
- `df`, Pareto `L`, and Pareto `a` must be positive; the Pareto support also
  requires `L<=min(x)`, but no call enforces these conditions
- bootstrap calls suppress warnings and no block checks `out$convergence` or
  nonfinite objectives
- correction: use bounded/transformed parameters, retain diagnostics, and
  handle failed fits explicitly

## L08-D007 — stochastic results have no reproducibility state

- locations: lines 736–747, 854–865, 934–961, 970–996, and 1054–1072
- four code blocks call `rt` or `sample`; no `set.seed`, `RNGversion`, package
  version, or session record appears
- correction: freeze an explicit RNG protocol and environment, then regenerate
  all dependent output and plots

## L08-D008 — three fixed outputs and their prose intervals disagree

- line 797 output `(2.612500,1.342177e7)` versus line 802 prose
  `(2.5789,2.68e7)`
- line 915 output `(3.339766,6.710887e6)` versus line 920 prose
  `(3.2688,6.8787e6)`
- line 1084 output `(1.277910,2.270643)` versus line 1088 prose
  `(1.2912,2.2905)`
- correction: select one seeded execution and make code, output, plots, and
  prose agree; do not guess which stale numbers were intended

## L08-D009 — expected and observed Fisher information are conflated

- locations: lines 641–644, 1099, and 1133–1136
- source calls the NLL Hessian from `optim` “Fisher Information,” defines
  `I(theta)=-E ell''(theta)`, then calls `I(hat(theta))` observed information
- correction: use `I_n(theta)=-E_theta ell_n''(theta;X)` for expected
  information and `J_n(theta)=-ell_n''(theta;x)` for observed information;
  identify `out$hessian` with the latter at the fit

## L08-D010 — the asymptotic MLE law is written as an exact law with random variance

- location: line 1099, math `O006-PSU-009-M0119`
- source writes `hat(theta) ~ N(theta_true,1/I(hat(theta)_ML))`, defines no
  per-observation/full-sample convention, and states no regularity assumptions
- correction: state the applicable convergence theorem and conditions; label
  information at `hat(theta)` as a plug-in standard-error estimate
- classification: inaccurate notation plus omitted theorem hypotheses, not a
  claim that every MLE is nonnormal

## L08-D011 — delta-method condition and limit variance are wrong

- location: line 1100, math `O006-PSU-009-M0127`–`M0129`
- source requires `g` to be invertible and puts `g'(hat(theta))` directly in
  the limiting law
- correction: require differentiability at `theta_0`, use `g'(theta_0)` in the
  limit, and identify `g'(hat(theta))` as a plug-in estimate when appropriate;
  invertibility is unnecessary

## L08-D012 — bootstrap validity is overclaimed

- locations: lines 1112 and 1173–1174
- source says bootstrap has no restrictions on `g` and enables robust
  inference without strict distributional assumptions, including small samples
- correction: say it does not require invertibility but remains dependent on
  the statistic, transformation, model/resampling scheme, sample design, and
  regularity; parametric bootstrap explicitly assumes a fitted family
- classification: scope/assumption correction, not a rejection of bootstrap

## L08-D013 — implemented Pareto support includes L

- location: line 1037, math `O006-PSU-009-M0110`
- source writes `(L,infinity)` while `EnvStats::dpareto` uses
  `[location,infinity)`
- correction: write `[L,infinity)`

## L08-D014 — the reported bootstrap interval is invalid for Pareto location L

- locations: lines 1037–1088
- observed `min(x)=5.06`; every resample minimum is at least 5.06, so the
  reported percentile interval is `(5.06,5.28)`
- for a continuous Pareto sample, `min(X)>L` almost surely; hence this interval
  excludes the true endpoint almost surely and cannot have nominal 95% coverage
- correction: retain the computation only as a counterexample and use an
  endpoint-valid inferential method for any affirmative interval claim

## L08-D015 — all four figures lack complete text equivalents

- locations: lines 593–615, 767–786, 885–904, and 1007–1034
- all visible captions are only figure numbers; the alts omit axes,
  distribution shape, extremes, and inferential meaning; Figure 8.3 says
  `boostrap`; every image is fixed to 70% width
- correction: supply full localized descriptions, preserve figure numbers as
  labels, center the images, and use available reader width

## L08-D016 — two internal authoring notes are reader-visible

- locations: lines 1125–1126 and 1168–1169
- source exposes “The following was in the current notes” and “This was in the
  new list lessons.qmd”
- correction: remove the workflow notes from the derivative while retaining
  the substantive summary content

## L08-D017 — grouped surface notation, grammar, and cross-reference defects

- lines 585–586: use `M` bootstrap data sets and index them by `m`
- line 678: “Each of the data set are” needs singular/plural agreement
- lines 691, 750, and 868: bootstrap estimates need hats (also `L08-D001`)
- line 810: sentence-initial `this` needs capitalization
- lines 930 and 966: corrupted lettered lists (`model.c.`), and line 930 has
  `opti` instead of `optim`
- line 1106: “Section 5” is not a local section; point to Section 8.1
- line 1108: two endpoints are quantiles, plural

## Correct content that must not be changed merely for stylistic uniformity

- The negative lower endpoint of the t-`df` Wald interval is possible under
  the Gaussian approximation and correctly illustrates its inadequacy.
- The parametric and nonparametric four-step algorithms are legitimate
  high-level templates once their notation and validity conditions are fixed.
- Empirical `.025` and `.975` quantiles are the percentile-bootstrap
  construction; the operator is not itself an error.
- Bootstrap transformation does not require an inverse function.
- The scalar delta variance has the correct squared-derivative structure in
  the summary once interpreted as an approximation under the stated
  conditions.

## Asset, rights, dependency, and reader disposition

Four exact current official PNGs were checked and frozen:

| Asset ID | Source file | Bytes | SHA-256 |
|---|---|---:|---|
| `O006-PSU-009-A0001` | `unnamed-chunk-1-1.png` | 47071 | `215b809d8213ef56a36c6bf69f1886f964d39d607532d551779f859052c17c0b` |
| `O006-PSU-009-A0002` | `unnamed-chunk-8-1.png` | 55503 | `c41f8223ba0306e6027ea44ec0c293b0b4a9ffdd558d7738e0c911ecc69725b6` |
| `O006-PSU-009-A0003` | `unnamed-chunk-14-1.png` | 59111 | `51ed4921773d92575cf3cb560d692c49e2022581b479093ad0a870302208798e` |
| `O006-PSU-009-A0004` | `unnamed-chunk-18-1.png` | 52007 | `11820bf246f37f1463f0384ce77672b0ce0d63466c186e6fb8bf25c5b1f522ad` |

All are 1344 by 960 PNGs, same-origin, last-modified
`Tue, 15 Jul 2025 11:06:07 GMT`, and total 213,692 bytes. Exact headers,
ETags, PNG validation, visual census, source alternatives, recommended
alternatives, and rights disposition are in
`working/lesson08_asset_closure.json`. The page footer supplies the CC BY-NC
4.0 witness and no per-image exception appears in the main.

There are no external instructional dependencies. The 185 fragment links are
code-line anchors; two relative links are the lesson breadcrumb; two empty
`href` values are tab controls. The normalized source preserves both tab
panels. An offline reader must expose both without requiring JavaScript and
must not treat copy buttons as instructional dependencies.

## Translation handoff

The segment census is 291, ordered
`O006-PSU-009-S0001` through `O006-PSU-009-S0291`. The next bounded translation
range should be `O006-PSU-009-S0001` through `O006-PSU-009-S0060`.
