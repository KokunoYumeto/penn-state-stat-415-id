# Lesson 03 source findings and derivative corrections

## Boundary

- Authority: `authority/upstream/stat415/Lesson03.html`
- Official URL: `https://online.stat.psu.edu/stat415/Lesson03`
- Authority identity: 118,925 bytes; SHA-256
  `26dd4efe75abc879a5316c215eaedbfe713c77e742898eb86e7f3d88cb0c04c9`.
- Rule: the frozen authority remains byte-identical. Every repair below is made
  only in the Indonesian derivative, receives a stable correction identity,
  and is exposed in the reader's modification record.

## Admitted findings

### L03-D001 — missing parenthesis in a normal-distribution call

Authority line 797 writes `N(\theta_1,\theta_2.`. The derivative closes the
distribution call before the period: `N(\theta_1,\theta_2)`.

### L03-D002 — equality sign inside a density product

Authority line 803 contains `\times\cdots\times =` before the last normal
density factor. Multiplication cannot be followed by an equality sign there.
The derivative removes the stray equality sign.

### L03-D003 — wrong index in a sufficient-statistic label

Authority line 811 correctly derives `\sum_i x_i^2` but labels its underbrace
as `\sum x_1^2`. The derivative uses `\sum_i x_i^2`.

### L03-D004 — reversed normalizing-term sign

Authority line 839 places an outer minus around
`\theta_1^2/(2\theta_2)-\log\sqrt{2\pi\theta_2}`, making the logarithmic
normalizer positive. Both terms must be negative. The derivative writes the
normal kernel with
`-\theta_1^2/(2\theta_2)-\log\sqrt{2\pi\theta_2}`.

### L03-D005 — non-injectivity is not by itself a proof of insufficiency

Authority line 649 concludes that `\bar X^2` is not sufficient for `\mu`
solely because squaring is not one-to-one. That inference is invalid in
general. The conclusion is true for this model: samples
`(a,\ldots,a)` and `(-a,\ldots,-a)` have the same `\bar X^2`, while their
likelihood ratio is `\exp(2na\mu)`, which depends on `\mu`. The derivative
replaces the invalid justification with this explicit counterexample.

### L03-D006 — unmatched parenthesis in the factorization theorem

Authority line 600 writes `h((x_1,\ldots,x_n)`. The derivative removes the
extra opening parenthesis.

### L03-D007 — malformed factor labels

The `\phi` underbrace labels at authority lines 617, 646, 667, and 759 have
mismatched delimiters, a stray subscript, or use `\mu` where the generic
function label should be `u`. The derivative labels the factors respectively
as `\phi(\sum_i x_i;\lambda)`, `\phi(\bar x;\mu)`,
`\phi(\sum_i x_i;\theta)`, and `\phi(\sum_iK(x_i);\theta)`.

### L03-D008 — factors are multiplied; only exponent arguments are added

Authority line 664 says that the `n` occurrences of `\theta` are “added up”
with the `x_i` terms in the exponents. The factors `\theta^{-1}` multiply to
`\theta^{-n}`; only the exponential arguments sum. The Indonesian prose states
that distinction explicitly.

### L03-D009 — ambiguous logarithm grouping

Authority line 695 writes `\ln(1-p)^{1-x}`, which conventionally means a power
of the logarithm rather than the logarithm of a power. The derivative writes
`\ln((1-p)^{1-x})`.

### L03-D010 — false intermediate Bernoulli equality

Authority line 701 displays an exponent whose labelled terms simplify to
`x\ln p`, not the Bernoulli log-pmf. The derivative retains the genuine
intermediate identity
`x\ln p+\ln(1-p)-x\ln(1-p)` before combining the `x` terms.

### L03-D011 — two reversed signs in the Poisson exponential form

Authority line 709 assigns positive `\ln(x!)` and positive `\lambda`. From
`e^{-\lambda}\lambda^x/x!`, the exponent is
`x\ln\lambda-\ln(x!)-\lambda`. The derivative uses those signs.

### L03-D012 — wrong coefficient and normalizer in the one-parameter normal form

Authority line 717 uses the undefined symbol `u` as the coefficient of `x` and
again makes the log-normalizer positive. The derivative writes
`x\mu-x^2/2-\mu^2/2-\tfrac12\ln(2\pi)`.

### L03-D013 — trailing multiplication sign

Authority line 801 ends the full joint-density product with an unpaired
`\times`. The derivative removes it.

### L03-D014 — logarithm and exponent are grouped incorrectly

Authority line 807 writes `\log(a)^n`, which means `(\log a)^n`, while the
derivation needs `\log(a^n)=n\log a`. The derivative places
`n\log(1/\sqrt{2\pi\theta_2})` in the exponent.

### L03-D015 — variance statistic uses a subscript instead of a square

Authority line 813 labels the sample variance `S_2` although the following
prose and standard formula use `S^2`. The derivative uses `S^2`.

### L03-D016 — an unknown parameter remains inside an estimator

Authority line 894 writes the method-of-moments estimator as
`n^{-1}\sum_iX_i^2-\mu^2` before equating it to the version with `\bar X^2`.
The first expression is not an estimator because it contains unknown `\mu`.
The derivative writes
`n^{-1}\sum_iX_i^2-\widehat\mu_{MM}^{,2}=n^{-1}\sum_iX_i^2-\bar X^2`.

### L03-D017 — gamma density changes variables mid-formula

Authority line 914 begins with `f(x_i)` but uses `x` on the right and in the
support statement. The derivative uses `x_i` consistently and states
`x_i>0`.

## Disposition

All seventeen findings are local, mechanically testable mathematical,
logical, or markup defects. They are admitted for target-only repair; function
names on repaired surfaces are also normalized to `\exp`, `\ln`, `\log`, and
`\operatorname{Var}` without altering their meaning. They remain queued for
the single deduplicated upstream report only after the entire relevant corpus
is complete. No upstream contact is made during production.

Separately, source text nodes bound to `O006-PSU-004-S0246`, `S0248`, and
`S0419` begin with a literal space before a comma following inline mathematics.
The translation merge removes only those three pre-comma spaces. At `S0306`,
the source omits the sentence-ending period between the geometric support and
the next sentence; the derivative inserts that exact boundary period. The
merge also preserves one registered word-separating space after inline
mathematics at `S0135`, `S0137`, `S0208`, `S0209`, `S0501`, `S0504`, `S0521`,
`S0523`, and `S0263`, where source-node segmentation otherwise glues the
translated word to the formula. All stable IDs are recorded in the translation
receipt. These punctuation and boundary-spacing normalizations do not alter
mathematical or prose content and are not counted as additional mathematical
corrections.
