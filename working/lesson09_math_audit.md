# Penn State STAT 415 Lesson 09 — mathematical and source audit

Audited the complete instructional `main#quarto-document-content` in
`authority/upstream/stat415/Lesson09.html` without changing the authority.

- official URL: `https://online.stat.psu.edu/stat415/Lesson09`
- frozen bytes: `114901`
- frozen SHA-256:
  `87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319`
- normalized document identity: `O006-PSU-010`
- normalized bytes: `82797`
- normalized SHA-256:
  `d2c7f39369911013434920b937daa060d4271dff2004faa10c116584b3277140`
- mathematics: 190 inline and 29 display surfaces (219 total)
- structured instruction: five definitions, seven examples, nine `Solution`
  sections, three decision tables, and ten instructional images
- executable material: zero `pre` nodes, zero code nodes, zero scripts, zero
  iframes, and zero media elements
- stable catalogue: 414 structural units, 443 translation segments, ten
  assets, and 1,087 total records

Every mathematical surface and every claim about hypotheses, rejection
regions, critical values, Type I/II error, p-values, and power was checked.
The Neyman–Pearson lemma, likelihood ratios, and likelihood-ratio tests do not
occur in this lesson. Their census is zero; they are not missing steps in a
derivation that the source actually attempts.

## General testing framework and equality boundaries

The null/alternative distinction, the two-by-two decision/error table, and the
conditional meanings of Type I and Type II error are materially correct. The
page also correctly warns readers to **fail to reject**, rather than “accept,”
the null when evidence is insufficient.

Three boundary qualifications must not be lost:

1. The generic rules `|T*|>c` and `|T*|<c` omit `|T*|=c`. For a continuously
   distributed statistic this equality set can have null probability zero; for
   a discrete statistic it can have positive probability.
2. A p-value uses outcomes **at least as extreme** as the observation. The
   source's strict “more extreme” wording omits the observed equality set.
3. If a discrete nonrandomized cutoff cannot attain the requested test size,
   an exact-level test requires an explicit randomized decision on a boundary
   equality set. This is a mathematical requirement only when exact size is
   claimed; a clearly labelled large-sample approximation does not need to be
   disguised as an exact randomized test.

The source alternates `P<=alpha` and “p-value is smaller than alpha.” A
derivative must state one complete convention. For the standard tests here,
use “reject when `p<=alpha`,” while retaining any exact discrete boundary rule
that defines the p-value.

## Type I error, Type II error, and power

The conditional definitions are:

```text
alpha(theta) = P_theta(reject H0), theta in Theta_0,
beta(theta)  = P_theta(fail to reject H0), theta in Theta_a,
power(theta) = 1-beta(theta), theta in Theta_a.
```

For a composite null, the level is the supremum of the rejection probability
over `Theta_0`. For a composite alternative, `beta` and power are functions of
the true parameter, not single free-standing constants.

The statement “we cannot decrease both; as alpha decreases, beta increases”
needs a fixed-design qualification. Holding sample size, test family, and a
specified alternative fixed commonly creates that tradeoff. Increasing sample
size or information can reduce both error probabilities.

The source sentence that rejecting the null lets us “conclude that the
alternative hypothesis is true” is too strong. Rejection supplies controlled
evidence against `H0`; a Type I error remains possible.

## Example 9.3 — one proportion

The setup and observed statistic are correct:

```text
H0: p=0.25,  Ha: p>0.25,
p-hat=290/1000=0.29,
SE_0=sqrt(.25*.75/1000)=0.013693...,
Z=(.29-.25)/SE_0=2.921...
```

The displayed equivalence is not correct after rounding. The actual cutoff is

```text
.25 + 1.645*sqrt(.25*.75/1000) = .27252509017739995.
```

Thus `Z>1.645` is equivalent to `p-hat>.27252509017739995`. Since
`p-hat=Y/1000`, its exact discrete form is `Y>=273`, equivalently
`p-hat>=.273`, not `p-hat>.273`.

The source's “size 0.05” and Type II value `0.5847` are Normal
approximations. Exact Binomial calculations give

```text
P_.25(Y>=273) = 0.051194671302778,
P_.25(Y>=274) = 0.044096329716543,
P_.27(Y<=272) = 0.572735965453399.
```

If exact size `0.05` is required, reject for `Y>=274` and, when `Y=273`,
reject with probability

```text
gamma = (.05-P_.25(Y>=274))/P_.25(Y=273)
      = 0.831697124143108.
```

This is the equality-set randomization required by the exact discrete claim.
For this introductory page, the simpler derivative may instead retain the
source method and label the cutoff, size, and beta calculation explicitly as
Normal approximations.

## Examples 9.4 and 9.5 — p-values and tails

For `128/150`, the rounded one-proportion statistic `Z=-1.92` is consistent
with the displayed inputs. The left-tail critical decisions at alpha `0.05`
and `0.01` are correct. `P(Z<-1.92)=0.0274` is also correct to four decimals.

For the two-sided version, `2(0.0274)=0.0548`, reported as `0.055`, and the
failure to reject at alpha `0.05` are correct. The prose immediately before
`|Z|>=1.96`, however, reads “reject ... or reject ...” without either tail
condition. The complete equivalent rule must be written in text as
`Z<=-1.96` or `Z>=1.96`.

## Example 9.6 — one mean, variance known

For an iid Normal sample with known population standard deviation,

```text
Z=(Xbar-mu_0)/(sigma/sqrt(n))
```

has the exact standard Normal null law. The arithmetic

```text
(80.94-85)/(11.6/sqrt(25)) = -1.75
```

and the left-tail critical decision at `-1.645` are correct.

The claim that `n=25` is necessarily “large enough” for the Central Limit
Theorem regardless of the weight distribution is false. No universal finite
sample size guarantees an adequate Normal approximation for every population
distribution. Without the iid Normal model, the use of `Z` must be labelled an
approximation and supported by distributional conditions or diagnostics.

The next line gives the correct p-value `0.0401`; the final line changes it to
`0.401` and asserts the false inequality `0.401<0.05`. The corrected statement
is `0.0401<0.05`.

## Example 9.7 — one mean, variance unknown

The statistic

```text
T=(Xbar-mu_0)/(S/sqrt(n))
```

has the exact `t_(n-1)` null distribution for an iid Normal random sample. The
source mentions Normal data and `n-1` degrees of freedom but omits the iid
random-sample condition. The observed value `4.762` is arithmetically correct.

The two critical-value symbols are contradictory: the same
`t_(.025,99)` is set equal to both `+1.9842` and `-1.9842`. Under an
upper-tail convention, write

```text
T >= t_(.025,99)=1.9842  or  T <= -t_(.025,99)=-1.9842.
```

Alternatively, define both lower-tail quantiles explicitly.

The displayed tail comparison proves only `p<0.05`. The next assertion
`p<=0.01` is true but does not follow from that display. Independent evaluation
gives the two-sided value `0.000006560183365621494`; include that calculation
or retain only the proved bound `p<0.05`.

## Figures, tables, assets, rights, and reproducibility

All ten direct same-origin assets were fetched from their official resolved
URLs without redirects, frozen byte-for-byte, and validated. The nine PNGs
pass chunk-boundary, CRC, dimension, trailing-byte, and embedded-rights-marker
checks. The SVG is valid UTF-8 XML with the expected view box, no script or
foreign object, no event handlers, no external references, and no embedded
rights/creator marker. Total frozen asset bytes are `4259848`.

Visual inspection confirms:

- the two generated plots show the observed `p-hat=.29` tail and the rejection
  region beginning at `.273`;
- the SVG shows center `.25`, cutoff `.273` / `Z=1.645`, and right-tail
  `alpha=.05`;
- `ht5`, `ht6`, `ht7`, `ht8`, `h10`, and `h11` show the stated left- or
  two-tail critical/p-value regions and numerical cut points; and
- the `h10` and `h11` source alt strings are wrong: both say “two-tail,” while
  the pixels show left-tail regions at `-1.645`/`-1.75`.

`ht5.png` has no alt text. The eight figure captions contain only figure
numbers, and the two generated plots have no figure caption. All derivative
descriptions must name the distribution, cutoff(s), shaded tail probability,
and decision meaning without relying on color.

Six native ids occur twice because each is attached to both a figure wrapper
and its image: `fig-h10`, `fig-h11`, `fig-ht6`, `fig-ht7`, `fig-ht8`, and
`fig-rttailcritical1645`. The normalized source preserves that topology; the
reader derivative must mint unique DOM ids while retaining catalogue bindings.

All three decision tables lack captions. The first two use ordinary `td` cells
for headers; the third has `th` cells without `scope`. Add captions and semantic
row/column headers in the reader without changing cell content.

The two paths under `Lesson09_files/figure-html/` are generated plot outputs,
but the lesson publishes no generating code, input data, package/runtime lock,
or random-state surface. Exact output bytes are reproducible from the freeze;
source-level plot regeneration is not. No executable claim should be made.

The page footer states CC BY-NC 4.0 except where otherwise noted. Every asset
is same-origin, and no per-asset exception appears in the instructional main.
The exact URLs, headers, bytes, hashes, dimensions/view box, rights disposition,
alt state, and visual witnesses are closed by
`authority/LESSON09_ASSET_MANIFEST.csv` and
`working/lesson09_asset_closure.json`.

## High-confidence correction register

The 19 stable findings are `L09-D001`–`L09-D019`:

1. qualify beta and power as functions of the true alternative parameter;
2. qualify the alpha/beta tradeoff by fixed design and alternative;
3. define the critical-boundary equality decision and randomization when exact
   discrete size requires it;
4. define p-values with “at least as extreme” and use a complete boundary rule;
5. replace the false rounded equivalence by `p-hat>=.273` / `Y>=273`;
6. label the one-proportion size and beta calculations approximate, or supply
   the exact randomized boundary rule;
7. do not turn rejection into certainty that the alternative is true;
8. restore both conditions in the two-tailed rejection sentence;
9. remove the universal `n=25` CLT claim;
10. correct `0.401` to `0.0401`;
11. correct the signed t critical-value notation;
12. prove the asserted `p<=.01` or retain only the displayed `p<.05` bound;
13. state the iid Normal condition for the exact one-sample t law;
14. restore the missing hypothesis in the summary Type II sentence;
15. replace missing/incorrect alts and label-only captions;
16. repair duplicate figure/image DOM ids additively;
17. add complete semantic table captions and headers;
18. correct the five unambiguous grammar/quotation defects; and
19. describe the generated plots as frozen outputs, not source-reproducible
   computations.

## Translation traps

- Use **gagal menolak hipotesis nol**, never “menerima hipotesis nol.”
- Keep `H_0`, `H_a`, `alpha`, `beta`, `Z`, `T`, and observed lowercase `z`/`t`
  distinctions intact.
- Translate p-value as **nilai-p** and define it with **sekurang-kurangnya sama
  ekstrem**.
- Distinguish **nilai kritis** from **daerah penolakan/daerah kritis**.
- State whether a critical subscript denotes an upper-tail or lower-tail
  probability.
- Label the one-proportion Normal calculations and the non-Normal `n=25` mean
  calculation as approximations.
- Preserve `beta(theta)` and **kuasa uji** as parameter-dependent quantities.
- Do not silently remove a discrete equality set; specify the deterministic or
  randomized boundary action.
