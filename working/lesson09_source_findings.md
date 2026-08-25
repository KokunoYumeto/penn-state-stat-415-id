# Penn State STAT 415 Lesson 09 — mechanically proved source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson09.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson09`
- bytes: `114901`
- SHA-256:
  `87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319`
- normalized document identity: `O006-PSU-010`
- corroborating audit: `working/lesson09_math_audit.md`

Only findings demonstrated by frozen prose/formulas, elementary probability
or algebra, exact asset bytes/pixels, or deterministic DOM inspection are
registered. Each item says whether it is an outright defect or an omission.

## L09-D001 — beta and power lose their parameter dependence

- classification: qualification omission
- source: “Typical beta values are 0.05, 0.10, and 0.20.”
- proved correction: for a composite alternative, use `beta(theta)` and
  `power(theta)=1-beta(theta)`. They depend on the specified true alternative
  value and are not free-standing constants.

## L09-D002 — the alpha/beta tradeoff is overgeneralized

- classification: outright overgeneralization
- source: “we cannot decrease both. As alpha decreases, beta increases.”
- proved correction: this monotone tradeoff needs a fixed sample size, test
  family, and specified alternative. Increasing information can reduce both.

## L09-D003 — the generic critical boundary has no decision

- classification: boundary omission
- source rules: `|T*|>c` rejects and `|T*|<c` fails to reject.
- proved correction: specify the action at `|T*|=c`. It is probability-zero
  only for an appropriate continuous null law. For a discrete exact-level test,
  specify a deterministic boundary action or randomize on the equality set.

## L09-D004 — the p-value definition drops equality

- classification: boundary omission
- source: “more extreme statistic than we did”; later `P<=alpha`; the summary
  says “smaller than alpha.”
- proved correction: define the p-value with outcomes **at least as extreme**
  as observed and use one complete decision-boundary convention.

## L09-D005 — the rounded proportion cutoff is not equivalent

- classification: outright mathematical defect
- source: `Z>1.645 or equivalently p-hat>0.273`.
- proof: the unrounded cutoff is `0.27252509017739995`. Since
  `p-hat=Y/1000`, the discrete equivalent is `Y>=273` or
  `p-hat>=0.273`, not `p-hat>0.273`.

## L09-D006 — approximate size and beta are written as exact

- classification: approximation-qualification omission
- source: the critical-region “size” is stated as `0.05`, and the Type II
  display uses equality ending in `0.5847`.
- exact witnesses:
  `P_.25(Y>=273)=0.051194671302778`,
  `P_.25(Y>=274)=0.044096329716543`, and
  `P_.27(Y<=272)=0.572735965453399`.
- proved correction: label the Normal results approximate. If exact size 0.05
  is intended, reject for `Y>=274` and reject at `Y=273` with probability
  `0.831697124143108`.

## L09-D007 — rejection is described as proof of the alternative

- classification: inferential overstatement
- source: “conclude that the alternative hypothesis is true.”
- proved correction: say the data provide sufficient evidence against `H0` in
  favor of `Ha`; a controlled Type I error remains possible.

## L09-D008 — the two-tailed rejection conditions disappear

- classification: outright surface defect
- source: “reject the null hypothesis or ... reject the null hypothesis.”
- proved correction: restore `Z<=-1.96` or `Z>=1.96`, equivalently
  `|Z|>=1.96`, in the prose.

## L09-D009 — n=25 is claimed universally sufficient for the CLT

- classification: outright mathematical overclaim
- source: `n=25` is “large enough for the Central Limit Theorem to apply”
  regardless of whether weights are Normal.
- proved correction: the result is exact for an iid Normal sample. Otherwise,
  no universal finite n guarantees an adequate Normal approximation; state the
  relevant distributional conditions and label the result approximate.

## L09-D010 — Example 9.6 has a decimal and inequality error

- classification: outright numerical defect
- source first gives `P(Z<-1.75)=0.0401`, then writes
  `0.401<alpha=0.05`.
- proved correction: `0.0401<0.05`. The source's `0.401<0.05` is false.

## L09-D011 — one t quantile is assigned both signs

- classification: outright notation defect
- source: `t_(.025,99)=1.9842` and `t_(.025,99)=-1.9842`.
- proved correction under the upper-tail convention:
  `T>=t_(.025,99)` or `T<=-t_(.025,99)`; alternatively define separate
  lower-tail quantiles.

## L09-D012 — the displayed p-value bound is silently strengthened

- classification: proof omission
- source display proves `p<0.05`; the next sentence asserts `p<=0.01`.
- disposition: the stronger claim is numerically true—the two-sided value is
  `0.000006560183365621494`—but does not follow from the shown bound. Add the
  tail calculation or state only `p<0.05`.

## L09-D013 — the exact t law lacks the iid sampling assumption

- classification: assumption omission
- source: says “if the data are normally distributed,” then the statistic has
  a `t_(n-1)` distribution.
- proved correction: require an iid Normal random sample. Marginal Normality
  alone does not imply the stated exact law.

## L09-D014 — the summary Type II sentence has no hypothesis subject

- classification: outright surface defect
- source: “Type II error: failing to reject when is true.”
- proved correction: “failing to reject `H0` when `Ha` is true,” equivalently
  when `H0` is false at the specified alternative.

## L09-D015 — image alternatives and captions are incomplete or wrong

- classification: accessibility defect
- frozen evidence: `ht5.png` has no alt; `h10.png` and `h11.png` say
  “two-tail,” but their pixels show left-tail regions at `-1.645`/`-1.75`;
  eight captions are figure numbers only; two generated plots lack captions.
- correction: provide complete, non-color-dependent descriptions naming the
  distribution, cutoff(s), tail area, and decision meaning.

## L09-D016 — six figure identifiers are duplicated

- classification: topology/accessibility defect
- ids: `fig-h10`, `fig-h11`, `fig-ht6`, `fig-ht7`, `fig-ht8`, and
  `fig-rttailcritical1645` each occur on a wrapper and an image.
- additive correction: preserve normalized source topology, but mint unique
  reader DOM ids while retaining stable catalogue bindings.

## L09-D017 — the decision tables lack complete semantics

- classification: accessibility defect
- DOM proof: all three tables lack `caption`; tables 1–2 have zero `th`; table
  3 has three `th` and zero `scope` attributes.
- additive correction: add concise captions and semantic row/column headers
  without changing the decision/error cell content.

## L09-D018 — five unambiguous mechanical defects

- classification: outright mechanical defects
- frozen strings: `was is building is not safe`, `procedure outlines above`,
  `more that four`, `lets choose`, and unmatched quotation in
  `(or critical value” or “critical region”)`.
- correction: remove the duplicated verb, fix agreement, replace `that` by
  `than`, add the apostrophe to `let's`, and balance quotation marks.

## L09-D019 — generated plot outputs have no reproducibility inputs

- classification: reproducibility omission
- proof: two images occur under `Lesson09_files/figure-html/`; the semantic main
  has zero code/pre nodes and no data, package lock, runtime, or random state.
- disposition: freeze and integrity-check the outputs, but do not claim
  source-level plot reproducibility.

## Correct material that must not be “fixed”

- The conditional descriptions of Type I/II errors and the warning not to
  accept `H0` are correct.
- The observed one-proportion statistic in Example 9.3 is correct; the defect
  is its rounded discrete equivalence and missing approximation label.
- The left-tail decisions at alpha 0.05 and 0.01 in Example 9.4 are correct.
- The two-sided p-value `0.055` in Example 9.5 is the correctly rounded
  `2(0.0274)=0.0548`.
- The one-mean `Z=-1.75` arithmetic and p-value `0.0401` are correct before the
  final decimal typo.
- The one-sample `t=4.762`, degrees of freedom 99, and rejection conclusion are
  correct once assumptions, signed quantile notation, and the p-value proof are
  repaired.
- `power=1-beta` is correct at a specified alternative parameter value.

## Asset, rights, links, and closure disposition

The lesson has ten direct same-origin assets: nine PNGs and one SVG. Their exact
official bytes total `4259848`; individual URLs, hashes, HTTP witnesses,
dimensions/view box, validation records, alt states, and visual descriptions
are in `authority/LESSON09_ASSET_MANIFEST.csv` and
`working/lesson09_asset_closure.json`.

There are eight links in the instructional main: two same-site navigation links
and six same-origin image lightboxes. There are no external instructional
dependencies. The footer supplies the CC BY-NC 4.0 witness, no per-asset
exception appears, and no frozen asset contains an embedded rights/creator
marker. Redistribution is admitted only with page attribution, license notice,
and derivative-change notice.

The complete next translation range is
`O006-PSU-010-S0001` through `O006-PSU-010-S0443` (443 segments).
