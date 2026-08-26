# Penn State STAT 415 Lesson 10 — mathematical and source audit

The complete `main#quarto-document-content` was audited without changing the
152767-byte authority (`0cb938a114d27b03ef3196c24a2e87b79a1a466b9dcbe370e6e6553947446bf5`). The frozen
boundary contains 369 math surfaces, 540
translation segments, 625 structural units, 22
unique images, 2 tables, five R source blocks, and three published
R output blocks.

## Exact discrete test in Example 10.2

For a Poisson(3.2) sum, the source rule `Y>=6` has size
`0.105408105469177`, which exceeds 0.10. The conservative rule `Y>=7`
has size `0.044619100955301`. Exact size 0.10 is obtained by rejecting
for `Y>=7` and rejecting with probability
`0.911034807817211` when `Y=6`. The source's
0.1054/0.1055 mismatch is secondary to this level violation.

## Confidence-interval duality

The two-sided t interval and test use the same pivot, but endpoint treatment
depends on the decision convention. With a closed 95% interval and the usual
`p<alpha` rejection rule, reject exactly when the null value lies outside the
interval. If `p<=alpha` is used, equality at an endpoint must be handled
explicitly. The positive p-value must not be rounded to the misleading string
`0.000`.

## Power and sample-size calculations

Power is a function of the alternative parameter. In this right-tailed test it
increases as mu moves to the right, not with unqualified absolute distance from
100. The source's `1-0.326=0.6278` confuses its z-score with power; the correct
complement is `1-0.3722=0.6278`.

Rounding the Normal-mean design to n=13 and recalculating the alpha-based cutoff
gives `c=42.737445468371504`, alpha `0.049984905539121`, beta at mu=45
`0.086974143114224`, and power `0.913025856885776`.
Thus the rounded design exceeds 0.90 power; it does not retain beta exactly 0.10.

For the proportion design, `phat>0.5367` at n=1001 means `X>=538`. Exact
Binomial probabilities are alpha `0.009647335485396` and beta at
p=0.55 `0.203436671383695`. The displayed 0.01 and 0.20 values
are Normal-approximation targets, not exact operating characteristics.

## Wald theory and Bernoulli example

The claim that every MLE is asymptotically Normal regardless of distribution is
false. The usable theorem requires an identifiable regular model, an interior
true parameter, consistency, differentiability and interchange conditions,
and nonsingular Fisher information; boundary and nonregular cases can fail.
The approximation should be expressed through a scaled limit, with observed or
expected information and its evaluation point identified.

For `T~N(c,se^2)`, the source's unstandardized p-value
`P(|T|>=|theta-hat|)` is not centered at c. Use
`P(|T-c|>=|theta-hat-c|)` or the standardized statistic. Define “at least as
extreme” consistently, include the p=alpha boundary, and do not describe a
rejection as accepting the alternative or disproving the null.

The Bernoulli demonstration has n=20 and one success. Its plug-in Wald p-value
is about 0.000040, whereas a doubled exact lower tail is
`0.048625249730321` and a probability-ordered exact
two-sided p-value is `0.038177041808922`.
This is a direct warning against an unqualified Wald approximation near a
parameter boundary. The numerical `optim` call is unconstrained and calls its
returned numerical Hessian Fisher information; the derivative must constrain
p, handle invalid likelihoods, and distinguish observed from expected
information. The final reference to a stated rate of 0.025 is a typo for 0.25.

## Preservation, accessibility, and reproducibility

The normalization keeps every formula, code/pre/style node, native anchor,
table, link, and image reference. Nineteen native identifiers are duplicated
between figure/image surfaces; the reader must mint unique DOM ids additively.
Both tables lack captions and their header cells lack scope. Nineteen captions
are labels only, three images are uncaptioned, and three alts contradict their
surrounding right-tail/beta/power semantics.

All 22 direct same-origin assets are frozen and hash-checked. The five R source
blocks and three outputs remain protected, but the source supplies no R version,
package/session lock, or expected-output contract. The reader should state the
base-R/runtime assumption and mechanically verify the outputs.

## Translation traps

- Use `kuasa uji`, `tingkat signifikansi`, `galat Tipe I/II`, `nilai-p`, and
  `informasi Fisher` consistently.
- Preserve alpha, beta, mu, p, c, Z, and the distinction between expected and
  observed information.
- Say `gagal menolak H0`; never translate rejection as proof or acceptance of HA.
- Mark Normal and Wald results as approximations where the source does not have
  an exact finite-sample law.
- Keep the Poisson equality-set randomization and the proportion-grid boundary
  explicit rather than silently treating a discrete statistic as continuous.
