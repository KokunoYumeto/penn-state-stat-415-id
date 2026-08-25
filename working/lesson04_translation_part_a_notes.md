# Lesson 04 translation partition A — source notes

Scope: exactly `O006-PSU-005-S0001`–`O006-PSU-005-S0124`.

## Corrected or clarified source prose

- `S0011`–`S0015`: the English objectives call every requested quantity an
  *estimate*. The Indonesian target distinguishes **nilai dugaan** when
  observed values are supplied from **penduga** when the data remain random
  variables. `S0015` also replaces the imprecise “parameter is in the support”
  with the intended condition **himpunan dukungan bergantung pada parameter**.
- `S0021`, `S0030`, and `S0033`–`S0034`: the source alternates between
  probability, probability distribution, and likelihood. The target states
  the mathematically correct meaning: a likelihood is the joint PMF/density
  evaluated at the observed sample and viewed as a function of the parameter;
  it is not a probability distribution over the parameter.
- `S0052`: a zero derivative gives a critical point, not by itself a proved
  maximum. The target retains the intended calculus workflow and explicitly
  requires the second-derivative and parameter-boundary checks.
- `S0064`–`S0069`: the source's displayed prose incorrectly uses
  `f(x_1)<f(x_2)` as though it proved monotonicity of the logarithm. Without
  adding any target formula, the Indonesian prose states the valid
  order-preservation argument for a positive function: the natural logarithm
  preserves its ordering, so both objectives have the same maximizers.
- `S0085`–`S0088`: the source's strict second-derivative claim omits the
  binomial boundary cases. The target distinguishes the interior case from
  all-zero/all-ten samples and also distinguishes the random estimator from
  its observed estimate.
- `S0090`–`S0091`: the claim that one may almost always accept a critical
  point as the MLE is false without shape and interior hypotheses. The target
  states the valid concavity/unimodality qualification and requires boundary
  or second-derivative checks otherwise.
- `S0099`–`S0110`: the repeated likelihood definition is repaired as above.
  The source also writes lowercase observed values in both the estimator and
  estimate displays. The Indonesian prose preserves the distinction between
  the statistic **penduga kemungkinan maksimum** and its observed **nilai
  dugaan kemungkinan maksimum**; the associated math correction must retain
  uppercase random variables for the estimator and lowercase realizations for
  the estimate.
- `S0119`–`S0123`: the recipe incorrectly promotes any critical value directly
  to an MLE. The target calls it a candidate until a maximum and boundary check
  has passed.

## Mechanical surface/math defects adjacent to this partition

- `S0092`: silently repairs the prose typo `definition og`.
- `S0113`: silently repairs `0ne` to “Satu”.
- `S0058`–`S0060` surround math block `O006-PSU-005-M0030`, whose derivative
  label must use lowercase `p` in `L(p)` rather than source `L(P)`.
- `S0117` introduces math block `O006-PSU-005-M0073`, whose final density term
  needs the missing conditioning bar: `f(x_i|\theta)`, not
  `f(x_i\theta)`.

No formula or HTML was inserted into the translation JSON. Boundary spaces and
punctuation were retained where segments join preserved math nodes; all source
replacement characters were replaced by valid Indonesian punctuation.
