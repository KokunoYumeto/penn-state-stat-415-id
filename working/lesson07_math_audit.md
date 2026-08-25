# Penn State STAT 415 Lesson 07 — mathematical, computational, and source audit

Checked: 2026-08-25

The complete frozen instructional `main#quarto-document-content` was audited
without changing the authority.

- authority: `authority/upstream/stat415/Lesson07.html`
- official page: <https://online.stat.psu.edu/stat415/Lesson07>
- frozen identity: 105,026 bytes; SHA-256
  `2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`
- normalized document identity: `O006-PSU-008`
- protected topology SHA-256:
  `2a5de57cd542d33c0dd5b24c028b19c86f34bed16f5c9887181b4f3b25ddb17c`
- mathematics: 122 inline and 26 display surfaces, 148 total; protected
  formula SHA-256:
  `c2da24f78e6d812d1bd5245e5cb671b52c1f3c5053de56e8141d13512fa36bb3`
- computation: 47 `code` nodes, comprising 16 R source blocks, 12 frozen
  console-output blocks, and 19 inline-code nodes; protected code-text SHA-256:
  `13fd8dd901b6d2b5c74d5b0fb06308684cbd29b5afb9e88913dd30a391b411c5`
- structure: 399 stable units, six examples, six solution sections, one table,
  two generated histogram figures, and 237 translation segments
- dependencies: two same-origin PNG files; no script, iframe, video, audio,
  object, embed, or downloadable dependency in the instructional main
- assessment closure: no independent public exercise or hint surface

The stable catalogue contains every formula and code node. The ranges below
partition `M0001`–`M0148` without gaps, so every mathematical surface is
covered even where an inline surface is only a symbol governed by the adjacent
display.

## Decisive consistency claim: a counterexample and the needed condition

Segments `S0025`–`S0030` define consistency informally and then call
`E(hat(theta)_mle) -> theta` a corollary. That implication is false.

Take `theta=0` and define an estimator sequence `T_n` by

```text
T_n = n with probability 1/n,
T_n = 0 with probability 1-1/n.
```

For every `epsilon>0`, once `n>epsilon`,

```text
P(|T_n-0|>epsilon)=1/n -> 0,
```

so `T_n ->p 0`: the sequence is consistent for zero. Nevertheless,

```text
E(T_n)=n(1/n)=1
```

for every `n`, so its expectations do not converge to zero. Thus consistency
alone cannot justify the source's expectation claim.

A sufficient repair is: if `hat(theta)_n ->p theta` and the family
`{hat(theta)_n}` is uniformly integrable, then convergence holds in `L1`, so
`E|hat(theta)_n-theta| -> 0` and hence
`E(hat(theta)_n) -> theta`. A commonly usable stronger sufficient condition is
`sup_n E|hat(theta)_n|^(1+delta)<infinity` for some `delta>0`. MIT's probability
notes explicitly warn that convergence in probability need not preserve
expectations, and the University of Wisconsin notes state the equivalence
between convergence in probability plus uniform integrability and `L1`
convergence:

- <https://ocw.mit.edu/courses/res-6-012-introduction-to-probability-spring-2018/5cc6f5af94dfa6b23f007671ad78cd73_Ajar_6MAOLw.pdf>
- <https://people.math.wisc.edu/~tgkurtz/831/f06m831.pdf>

This is registered as `L07-D001`; it is not a stylistic preference.

## Formula census and verdicts

| Stable range | Mathematical role | Audit verdict |
|---|---|---|
| `M0001`–`M0015` | Regularity notation, consistency, expectation, and equivariance | Symbols are well formed. `M0008` participates in `L07-D001`: expectation convergence is not implied by consistency. The stated invertible-transformation version of MLE equivariance is a valid sufficient form. |
| `M0016`–`M0027` | Normal-model MLEs and standard-deviation transformation | Correct: under the source's `1/n` MLE convention, `hat(sigma)=sqrt(n^(-1) sum (x_i-xbar)^2)`. This is not the unbiased sample standard deviation. |
| `M0028`–`M0034` | Binomial `Bin(5,p)` MLE and odds-ratio transformation | Correct for an interior estimate `0<hat(p)<1`. The displayed odds-ratio MLE is the equivariant transform `hat(p)/(1-hat(p))`; boundary cases would give zero or infinity and are not discussed. |
| `M0035`–`M0044` | Generic one-parameter asymptotic Normal approximation and information | `M0040` is a conventional plug-in approximation only under suitable regularity and with total-sample information. `M0043` is malformed as an expected-information definition and later prose equates the returned observed Hessian with expected Fisher information; see `L07-D002`. |
| `M0045`–`M0064` | Bernoulli likelihood, score, MLE, information, and asymptotic variance | Algebra is correct for `0<p<1`: `hat(p)=xbar`, `I_n(p)=n/[p(1-p)]`, and the plug-in variance is `xbar(1-xbar)/n`. The source's expectations over the full sample establish that this `I` is total-sample information. |
| `M0065`–`M0073` | Generic scalar Wald interval | `hat(theta) +/- 1.96/sqrt(I_n(hat(theta)))` is a 95% asymptotic Wald interval when the regular model, interior parameter, consistent MLE, nonsingular information, and valid plug-in approximation apply. “Any MLE” must not be read without those conditions. |
| `M0074`–`M0079` | Symbolic Bernoulli Wald interval | Correct under the preceding large-sample/interior conditions. It is an interval for `p`, constructed with `hat(p)`, not an interval whose inferential target is the estimator. |
| `M0080`–`M0088` | Numerical Bernoulli example with `xbar=.6`, `n=10` | The final margin `0.3036` and endpoints `(0.2964,0.9036)` are arithmetically correct, but `M0088` drops `1.96` in the intermediate equality. The corrected middle term is `0.6 +/- 1.96 sqrt(.6(.4)/10)`; see `L07-D003`. The source's explicit small-sample warning must remain. |
| `M0089`–`M0104` | Exponential mean/scale parameterization, MLE, information, and Wald interval | `M0093`–`M0097`, `M0100`, and the final identities in `M0102` are correct for `x_i>=0`, `theta>0`: `hat(theta)=xbar` and `I_n(hat(theta))=n/hat(theta)^2`. The formula is a density, not a PMF (`L07-D009`). `M0098` omits `ell(theta)` on its left side (`L07-D011`). `M0102` improperly moves between expectation and observed substitution (`L07-D002`). `M0104` takes the reciprocal incorrectly (`L07-D004`). The corrected interval is `xbar +/- 1.96 xbar/sqrt(n)`. |
| `M0105`–`M0112` | Multiparameter approximation and Fisher information matrix | Correct as a plug-in approximation when `I_n` denotes nonsingular total-sample expected information and regularity holds. The `~` display should be read as asymptotic approximation, not an exact finite-sample law. |
| `M0113`–`M0128` | Scalar and vector 95% Wald-interval summary | The scalar formula and the diagonal entry of `I_n(hat(theta))^(-1)` are correct under the stated convention and regularity. `hat(theta_k)` is harmless notation for `hat(theta)_k`. The phrase “k-the parameter” is a source typo (`L07-D011`). |
| `M0129`–`M0145` | Symbols supporting the numerical `optim` demonstrations | The mathematical references to inverse-information diagonal entries and parameter ordering are correct. Prose incorrectly labels confidence intervals as targeting MLEs (`L07-D007`), and the Normal-example prose does not match its frozen output (`L07-D005`). |
| `M0146`–`M0148` | Final score-information form of asymptotic normality | Correct when `I(theta)=E[(partial log f(X|theta)/partial theta)^2]` is per-observation information: `sqrt(n)(hat(theta)-theta) ->d N(0,1/I(theta))`. This silently switches from the earlier total-sample convention. Translation must explicitly say “information per observation” here and “total-sample information” in the unscaled Wald formulas. |

### Correct exponential calculation replacing the defective chain

For `X_i ~ Exp(scale=theta)`,

```text
ell''(theta) = n/theta^2 - 2 sum(x_i)/theta^3,
I_n(theta) = -E_theta[ell''(theta)]
           = -[n/theta^2 - 2n theta/theta^3]
           = n/theta^2.
```

Evaluating only after taking the expectation gives
`I_n(hat(theta))=n/hat(theta)^2=n/xbar^2`; consequently
`sqrt(1/I_n(hat(theta)))=xbar/sqrt(n)`. The source instead replaces this
reciprocal by `sqrt(n^3/xbar^2)` in `M0104`.

## Complete R-source and frozen-output audit

The R installation was not needed to establish the results: all inputs and
outputs are frozen in the authority, and the displayed arithmetic was checked
directly. The official R manuals confirm that `optim(..., hessian=TRUE)`
returns the numerically differentiated Hessian at the solution, that `dgeom`
requires `0<prob<=1`, and that a negative Normal `sd` is invalid:

- <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/optim.html>
- <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Geometric.html>
- <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Normal.html>

| R source units | Operation | Audit verdict |
|---|---|---|
| `U0165`, `U0179` | Fixed geometric sample and histogram | The 45 observations and right-skewed histogram agree. `hist(x)` has no inferential role. |
| `U0194`, `U0206`, `U0224` | Geometric NLL and two `optim` calls | The objective matches R's failures-before-first-success geometric model. The approximate result `p.hat=.1546875` is close to the analytic `45/(45+246)=.154639...`; the finite-difference Hessian `2225.054` and printed interval endpoints are internally consistent. The calls do not enforce `0<p<=1`; see `L07-D006`. |
| `U0238`, `U0250`, `U0263` | Extract `p.hat`, Hessian, and two endpoints | Executing arithmetic is correct for the returned observed Hessian. Comments/prose must call it observed information (or a regular plug-in approximation), not automatically expected Fisher information (`L07-D002`). |
| `U0282`, `U0294` | `set.seed(1)`, Normal simulation, and histogram | The frozen sample and figure are mutually consistent. The code states mean `-7` and variance `16` via `sd=sqrt(16)`. |
| `U0309`, `U0325` | Normal NLL and optimizer | The likelihood parameterizes `theta=(mu,sigma^2)`. The objective calls `sqrt(vr)` without guarding `vr>0`, and the optimizer is unconstrained (`L07-D006`). The frozen optimizer returns `(-6.564774,12.773473)`. |
| `U0338`, `U0353`, `U0369`, `U0382` | Extract MLEs, invert Hessian, compute SEs and CIs | `sqrt(diag(solve(I)))` is correct for covariance approximation `I^(-1)`. The comment in `U0353` incorrectly says `sqrt(1/I.inv[p,p])` (`L07-D010`). The SEs `.357400` and `1.805645` and intervals `[-7.265278,-5.864270]`, `[9.234409,16.312537]` follow from the frozen values. |

All 12 console-output units were reconciled with those source groups:
`U0174`, `U0212`, `U0230`, `U0245`, `U0258`, `U0268`, `U0289`,
`U0331`, `U0344`, `U0361`, `U0375`, and `U0388`. The only output/prose
contradiction is `L07-D005`: `S0212`–`S0214` report unrelated values
`5.469399` and `38.620385` instead of the immediately preceding frozen MLEs.

## Source-claim audit

- `S0009`–`S0010` and `S0236`–`S0237` claim coverage of parametric and
  nonparametric bootstrap intervals, the Delta method, and t/Pareto examples.
  No instructional body section, formula, code block, example, or figure
  teaches those topics. This stale scope claim is `L07-D008`.
- `S0014`–`S0021` explicitly says the regularity-condition list and proofs are
  incomplete. That limitation is accurate and mandatory to preserve. The two
  sample conditions are not a substitute for a theorem. In particular,
  `S0019`–`S0020` confuses an interior parameter-space condition with data
  support (`L07-D012`).
- `S0023`–`S0030` correctly identifies consistency as an MLE property under
  suitable hypotheses, but its expectation “corollary” is false (`L07-D001`).
- `S0032`–`S0039` gives a valid invertible-function form of MLE equivariance.
  The two transformation examples agree with it.
- The Bernoulli derivation and symbolic interval claims are correct subject to
  `0<p<1` and large-sample qualifications. The `n=10` caution is justified and
  must not be dropped.
- The exponential model uses the mean/scale parameterization, not a rate
  parameterization. Its density label, information derivation, and final
  interval require the corrections registered above.
- The multivariate covariance statement is valid only with a nonsingular
  information matrix and regularity. Avoid translating “any MLE” as an
  unconditional finite-sample guarantee.
- `S0177`, `S0195`–`S0199` use “confidence interval for the MLE.” A confidence
  interval targets the unknown parameter; the MLE supplies its center and
  estimated standard error (`L07-D007`).
- The statements that `optim`'s Hessian “is the Fisher Information” are too
  strong. For the minimized negative log-likelihood it is an estimate of the
  observed information. Equality with expected information requires a model-
  specific identity or an asymptotic plug-in argument (`L07-D002`).

## Authority limitation that must remain visible

`S0021` says: the lesson will not provide the full regularity-condition list or
proofs and refers readers to Wasserman, Chapter 9.13. This is classified as an
explicit source limitation, not a defect. Translation must preserve it, retain
the phrase “subject to regularity conditions,” and avoid strengthening the
nearby emphatic “ANY MLE!” into a universal theorem.

## Figures, rights, accessibility, and assessment

The two same-origin PNG files are byte-frozen, CRC-valid, and covered by the
page's CC BY-NC 4.0 notice; no per-asset exception or embedded creator/rights
marker was found. Their combined size is 100,723 bytes.

- `A0001`: 51,500 bytes, 1344 by 960, SHA-256
  `261e8fee2ada5d25b3cf92d4fde1825dfcce67f97629120efc6d432b06a89372`;
  geometric histogram with mass concentrated near zero and a long right tail.
- `A0002`: 49,223 bytes, 1344 by 960, SHA-256
  `18e14d1763554c43bcc8c31ba57756918ea7e47985abbf840f40ee3842460e65`;
  roughly bell-shaped seeded Normal histogram centered near `-7`.

The source alt strings merely name the distribution. The Indonesian reader
should describe shape, center/tail, and axes in adjacent accessible text; the
authority PNG bytes remain unchanged.

No independent exercise or hint is present. The six examples all include
solutions and therefore serve as worked instruction, not closed assessment.
This is an assessment-closure fact, not permission to reconstruct private
course material.

## High-confidence register

The exact mechanically bound records are `L07-D001`–`L07-D012` in
`working/lesson07_source_findings.md` and the normalization receipt. No other
preference or speculative correction was admitted.
