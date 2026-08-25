# Lesson 02 source findings and derivative corrections

## Boundary

- Authority: `authority/upstream/stat415/Lesson02.html`
- Official URL: `https://online.stat.psu.edu/stat415/Lesson02`
- Authority identity: 93,418 bytes; SHA-256
  `29890184a4f2ba91fcd10425e0a941e7eab0f3ac9ab158b2ba469d0744ec69e5`.
- Rule: the frozen authority remains byte-identical. Every repair below is made
  only in the Indonesian derivative, receives a stable correction identity,
  and is exposed in the reader's modification record.

## Admitted findings

### L02-D001 — wrong denominator in the first estimator

- Evidence: authority line 616 defines
  `\hat p_1=X_1/n`, while the example has three observations
  `X_i\sim\operatorname{Bin}(10,p)`. Lines 642–643 and every later recurrence
  instead use `\hat p_1=X_1/10` and `E(X_1)=10p`.
- Finding: dividing by the sample count `n=3` does not estimate the binomial
  success probability. The consistent intended denominator is the ten trials
  in each binomial observation.
- Derivative repair: use `\hat p_1=X_1/10`.

### L02-D002 — escaped text substituted for TeX alignment markers

- Evidence: authority lines 635–637 contain three literal `&amp;amp;` sequences
  in an `aligned` environment; after one HTML parse they remain the text
  `&amp;`, rather than becoming TeX `&` alignment markers.
- Derivative repair: replace the three protected formula tokens with TeX `&`.

### L02-D003 — wrong binomial expectation

- Evidence: authority line 642 states `E(X)=p` for a binomial random variable,
  then line 643 correctly substitutes `E(X_1)=10p`.
- Finding: for `X\sim\operatorname{Bin}(n,p)`, `E(X)=np`.
- Derivative repair: display `E(X)=np` while retaining
  `\operatorname{Var}(X)=np(1-p)`.

### L02-D004 — incomplete answer to Example 2.6

- Evidence: line 639 asks for the bias of all three estimators, but the worked
  solution at lines 641–643 stops after `\operatorname{Bias}(\hat p_1)=0`.
  Lines 880–888 later establish all three required expectations and biases.
- Derivative repair: keep the supplied derivation and add the two omitted
  results, derived explicitly:
  `E(\hat p_2)=p`, so `\operatorname{Bias}(\hat p_2)=0`; and
  `E(\hat p_3)=p+0.1`, so `\operatorname{Bias}(\hat p_3)=0.1`.

### L02-D005 — invalid sample-variance algebra

- Evidence: authority line 669 adds an erroneous outer square to the expanded
  summand, drops the summation in that step, and drops `1/n` from the middle
  term.
- Derivative repair: use the valid identity
  `n^{-1}\sum_i(x_i-\bar x)^2`
  `=n^{-1}\sum_i(x_i^2-2x_i\bar x+\bar x^2)`
  `=n^{-1}\sum_i x_i^2-(2\bar x/n)\sum_i x_i+\bar x^2`
  `=n^{-1}\sum_i x_i^2-\bar x^2`.

### L02-D006 — wrong exponent in an antiderivative

- Evidence: authority line 758 writes
  `y^{1/\theta}\ln y-\theta y^{1-\theta}`.
- Finding: integration by parts with
  `dv=(1/\theta)y^{1/\theta-1}dy` gives `v=y^{1/\theta}`.
- Derivative repair: use
  `y^{1/\theta}\ln y-\theta y^{1/\theta}`; the evaluated expectation remains
  `E(\ln Y_i)=-\theta`.

### L02-D007 — wrong parameter symbol

- Evidence: authority line 796 defines
  `X_i\overset{iid}{\sim}\operatorname{Bin}(10,p)` and the three statistics
  are `\hat p_1,\hat p_2,\hat p_3`, but calls the first two unbiased estimators
  of `\theta`.
- Derivative repair: replace that isolated `\theta` with `p`.

### L02-D008 — missing closing parenthesis

- Evidence: authority line 817 contains
  `\operatorname{Var}(\hat p_1)>\operatorname{Var}(\hat p_2.`.
- Derivative repair: close the second variance call before the period:
  `\operatorname{Var}(\hat p_1)>\operatorname{Var}(\hat p_2)`.

### L02-D009 — sign, argument, and delimiter errors in MSE

- Evidence: authority line 867 writes
  `\operatorname{MSE}(\hat\theta)=\operatorname{Var}(\hat\theta)-`
  `[\operatorname{Bias}(\theta)]^2`. Lines 892–894 repeat the wrong minus sign,
  omit a closing parenthesis in each bias call, and conclude that the squared
  bias of `\hat p_3` is subtracted.
- Finding: squared bias is nonnegative and is added to variance:
  `\operatorname{MSE}(\hat\theta)=\operatorname{Var}(\hat\theta)+`
  `[\operatorname{Bias}(\hat\theta)]^2`.
- Derivative repair: use the plus sign and the estimator argument throughout,
  close all three calls, and give
  `\operatorname{MSE}(\hat p_3)=p(1-p)/30+0.01`.

## Disposition

All nine findings are local, mechanically testable mathematical or markup
defects with no plausible pedagogical alternative. They are admitted for the
Indonesian derivative. They remain queued for the single deduplicated upstream
report only after the entire relevant corpus is complete; no upstream contact
is made during production.
