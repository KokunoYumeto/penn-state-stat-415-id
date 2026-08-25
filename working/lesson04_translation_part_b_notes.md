# Lesson 04 translation partition B notes

## Exact scope

- source: `working/lesson04_segments.csv`
- document: `O006-PSU-005` / `Lesson04`
- translated range: `O006-PSU-005-S0125` through
  `O006-PSU-005-S0248`, inclusive
- key count: 124
- target: `working/lesson04_translation_part_b.json`
- target locale: natural reader-facing `id-ID`

The JSON maps every and only the 124 consecutive stable segment IDs in this
range. It contains prose only: no formula, HTML, identifier, or mathematical
symbol absent from a segment's `source_text` was inserted. Boundary whitespace
is deliberately retained because the builder interleaves these strings with
protected math nodes.

## Terminology decisions applied

- `estimator` → **penduga**; `estimate` → **nilai dugaan**;
- `maximum likelihood estimator` → **penduga kemungkinan maksimum (MLE)**;
- `maximum likelihood estimate` → **nilai dugaan kemungkinan maksimum**;
- `likelihood (function)` → **fungsi kemungkinan**, never `peluang`;
- `log-likelihood function` → **fungsi log-kemungkinan**;
- `probability mass function` → **fungsi massa peluang (PMF)**;
- `probability density function` → **fungsi kepadatan peluang (PDF)**;
- `indicator function` → **fungsi indikator**;
- `support` → **himpunan dukungan**;
- `parameter-dependent support` → **himpunan dukungan yang bergantung pada
  parameter**; and
- `maximum order statistic` → **statistik urutan maksimum**.

The source abbreviation `MLE` and distribution names/symbols are preserved.

## Proved prose corrections encoded in this partition

1. `S0156`, `S0159`, `S0162`, `S0167`, `S0170`, and `S0180` preserve the
   distinction between a random **penduga** and its realized **nilai dugaan**.
2. `S0169` silently removes the surface typo “The the” without changing
   meaning.
3. `S0195`–`S0198` implement the proved correction to `L04-D008`: the score
   equation has no solution, the displayed candidate at infinity is explicitly
   negated, and the likelihood is described as monotonically decreasing rather
   than increasing. The prose now directs the reader to the support boundary,
   not to a nonexistent critical point.
4. `S0199`–`S0207` replace the source's category error “the parameter is in the
   support” with the intended statement that the support depends on the
   parameter and that the parameter determines its boundary.
5. `S0218`, `S0220`, `S0221`, and `S0223` correct the Bernoulli surface from
   PDF to **PMF**, as required by the mathematical audit.
6. `S0241`–`S0248` implement `L04-D013` without altering protected math: with
   the source's strict open endpoint, the stated boundary value is identified
   as a supremum and not an attained MLE. `S0246` explicitly states that the
   maximum is not attained; `S0247`–`S0248` call the maximum order statistic
   the supremum boundary.

## Adjacent protected-math corrections required at merge/build time

The prose JSON cannot and does not mutate protected formula nodes. The additive
correction layer must therefore apply the already proved findings adjacent to
this partition:

- after `S0149`, `M0098`: `L04-D003`, use `L(\theta)`, not `L(p)`;
- after `S0150`, `M0099`: `L04-D004`, remove the extra nested logarithm;
- after `S0153`, the displayed solve-for parameter must be `\theta`, not `p`;
- after `S0159`, `M0108`: `L04-D005`, use the Geometric parameter `p`, not
  `\theta`;
- after `S0170`, `M0116`: `L04-D006`, complete the value as
  `17/9 \approx 1.8889`;
- after `S0176`, `M0121`: `L04-D007`, give the factorial log term a minus
  sign; the derivative following `S0177` must also label its left side
  `d\ell/d\lambda`;
- around `S0195`–`S0198`, retain `M0135` as the negative score and treat
  `M0138` as the rejected, not asserted, infinity claim; the source's literal
  punctuation immediately after `M0138` is `!.` and should be normalized to a
  single period by the disclosed correction layer;
- around `S0222`–`S0229`, apply `L04-D009`–`L04-D011` to `M0155`, `M0157`,
  `M0160`, and `M0162`: restore `y=0`, index product factors/indicators by
  `i`, use `\sum_i y_i`, and label the score derivative;
- after `S0240`, `M0170`: `L04-D012`, index the Uniform indicator by `i`; and
- around `S0230`–`S0248`, `M0167`/`M0176`: preserve the strict-open-support
  interpretation used by the corrected prose. If the reader instead adopts a
  right-inclusive density convention, that change must be explicitly
  disclosed rather than silently mixed with the source convention.

## Partition seam

`S0248` is followed by out-of-range `S0249` (“as the likelihood is maximized
when …”). To remain consistent with the proved open-endpoint correction,
`S0249` must not reassert an attained maximum. Its eventual translation should
say that the displayed boundary is approached as a supremum, unless the reader
explicitly changes and discloses the density convention to include the right
endpoint.

## Validation contract

The final validation checks:

- valid UTF-8 JSON object;
- exactly 124 keys, in canonical consecutive order `S0125`–`S0248`;
- no missing, extra, duplicate, or blank target;
- leading/trailing whitespace parity with every source segment;
- no Unicode replacement character; and
- no HTML angle brackets in target prose.
