# Penn State STAT 415 Lesson 06 — mathematical and source audit

Audited the complete instructional `main#quarto-document-content` in
`authority/upstream/stat415/Lesson06.html` without changing the authority.

- official URL: `https://online.stat.psu.edu/stat415/Lesson06`
- frozen bytes: `77034`
- frozen SHA-256:
  `abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06`
- expected normalized document identity: `O006-PSU-007`
- instructional-main extent: 22,853 UTF-8 bytes
- mathematics: 80 inline and 22 display surfaces (102 total)
- structured instruction: one theorem with proof, two worked examples, one
  explicit `Solution` surface, and one instructional figure
- executable material: zero code blocks, zero outputs, zero iframes, and zero
  video elements
- independent practice: zero public exercises and zero hint surfaces

## Formula-by-formula result

### Section 6.1 — interval terminology

The confidence coefficient `1-alpha`, confidence level
`(1-alpha)100%`, and generic endpoints `L < theta < U` are mathematically
legitimate. Open rather than closed endpoints in this first schematic display
are not, by themselves, an error.

The prose at line 537 is erroneous, however: it identifies an **estimator**
with a **point estimate**. A point estimator is a random statistic such as
`hat(theta)=T(X)`; after data `x` are observed, `T(x)` is the realized point
estimate. This distinction is already controlling in the component glossary.

### Section 6.2 — known-variance Normal mean

The definitions

```text
P(Z >= z_(alpha/2)) = alpha/2,
P(Z <= -z_(alpha/2)) = alpha/2
```

are correct under the source's explicit upper-tail convention. The theorem

```text
xbar +/- z_(alpha/2) sigma/sqrt(n)
```

is the exact equal-tail interval for an iid Normal sample with unknown mean
and known variance. The standardization and the inequality manipulation on
lines 589–598 are also correct.

Line 600 drops the equality sign. It must be

```text
P[Xbar - z_(alpha/2) sigma/sqrt(n) <= mu
  <= Xbar + z_(alpha/2) sigma/sqrt(n)] = 1-alpha.
```

The figure itself labels the two critical points with capital `Z`, whereas the
body correctly reserves capital `Z` for the random variable and lowercase
`z_(alpha/2)` for its quantile. The derivative should use
`-z_(alpha/2)` and `z_(alpha/2)` in the figure or an adjacent correction note.

### Section 6.3 — interpretation and Gamma pivot

The repeated-sampling interpretation is materially correct: before sampling,
the endpoints are random and the procedure covers fixed `mu` with probability
`1-alpha`; after observing the sample, the realized interval either covers
`mu` or it does not. Saying that 950 of 1,000 95% intervals are **expected**
to cover is correct; it does not guarantee exactly 950 realized successes.

For Example 6.1, with `Y ~ Gamma(shape=2, scale=theta)`, the calculations are
correct:

```text
M_Y(t) = (1-theta*t)^(-2),
U = 2Y/theta ~ Gamma(shape=2, scale=2) = chi-square(4).
```

The displayed numerical endpoints are also correct:

```text
2(1.261552)/9.4877 = 0.265934...,
2(1.261552)/0.7107 = 3.550167....
```

There is nevertheless a high-risk notation ambiguity. Lines 557–562 define
`z_p` by **upper-tail** probability, but lines 644–651 silently use the
chi-square subscripts as **lower-tail cumulative probabilities**, as the
values 0.7107 and 9.4877 prove. Avoid transferring the ambiguity. Define

```text
q_p = F^(-1)_(chi-square(4))(p)
```

and write

```text
P[q_.05 <= 2Y/theta <= q_.95] = .90,
CI(theta) = [2Y/q_.95, 2Y/q_.05].
```

This preserves the correct source calculation while making the quantile
convention explicit.

### Section 6.4 — large-sample interval

The decisive condition for the stated interval is studentized convergence,

```text
(hat(theta)-theta)/hat(se)(hat(theta)) ->d N(0,1).
```

Lines 658–665 instead say that exact unbiasedness is necessary and that the
standard error need only be “known or can be found.” Exact unbiasedness is not
necessary: bias that is negligible relative to the standard error is enough.
When the standard error is estimated, consistency or another theorem that
justifies the studentization is required. The translation should state the
actual convergence condition and may present the source list as a simple
sufficient special case, not as necessary conditions.

Example 6.2 contains a proved formula/value error at line 673. The observed
sample variance is `s^2=256`, so `s=16` and

```text
estimated SE(xbar) = s/sqrt(64) = 16/8 = 2.
```

The source instead writes a squared-SE symbol, equates it to `s/sqrt(64)`,
and then gives the value 256. The next line uses the correct value 2, and the
reported approximate interval `(29.71, 36.29)` is arithmetically correct.
Because the population distribution and variance are not specified, this is
a large-sample approximate interval, not the exact known-variance theorem from
Section 6.2.

### Section 6.5 — summary

The general estimate-plus-critical-value-times-standard-error pattern and the
known-variance Normal formula are correct. The unknown-variance `t` formula is
incomplete as a standalone claim: `df` is never defined and the required
sampling assumptions are omitted. For an iid Normal sample it should be

```text
xbar +/- t_(alpha/2,n-1) S/sqrt(n).
```

Outside the Normal model, this can be presented only with the applicable
large-sample or robustness qualification.

## High-confidence correction register

1. Line 537: distinguish point estimator from realized point estimate.
2. Line 600: insert the missing `=` before `1-alpha`.
3. Figure 6.1: use lowercase `z` for fixed critical values, not capital `Z`.
4. Lines 644–651: define the chi-square quantile convention explicitly.
5. Lines 658–665: replace “unbiasedness is necessary” with the actual
   studentized-convergence condition and qualify estimated standard errors.
6. Line 673: replace the erroneous squared-SE/value statement with
   `estimated SE(xbar)=s/sqrt(n)=16/8=2`.
7. Line 688: supply `df=n-1` and the iid-Normal condition for the exact
   unknown-variance `t` interval.

These seven mathematical/content findings are `L06-D001`–`L06-D007`. The
figure alternative-text defect, grouped mechanical surface defects, and
additive proof-role repair below are `L06-D008`–`L06-D010`, for ten registered
derivative corrections in total.

## Figure, assets, rights, and accessibility

The only instructional image is `assets/ci_1.png`, resolved officially as
`https://online.stat.psu.edu/stat415/assets/ci_1.png`. A read-only check on
2026-08-25 returned HTTP 200, PNG dimensions 1334 by 640, 67,496 bytes,
SHA-256
`2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f`,
and `Last-Modified: Thu, 27 Jun 2024 10:27:13 GMT`. The deterministic Lesson 06
normalizer subsequently froze these exact official bytes at
`authority/assets/stat415/lesson06/assets/ci_1.png`; their identity is closed
by `authority/LESSON06_ASSET_MANIFEST.csv` and
`working/lesson06_asset_closure.json`.

The figure accurately shades the central `1-alpha` region and two
`alpha/2` tails, apart from the capital/lowercase critical-value defect above.
Its HTML alt text mentions only a centered `1-alpha` area; it omits the two
tail probabilities and critical points. The visible caption is only
“Fig 6.1,” and the lightbox title is an empty “Fig 6.1:”. Provide a fuller alt
or adjacent text such as: “Kurva normal baku dengan daerah tengah
`1-alpha` di antara `-z_(alpha/2)` dan `z_(alpha/2)` serta daerah
`alpha/2` pada setiap ekor.” Do not rely on color alone.

The page footer states CC BY-NC 4.0 except where otherwise noted. The image is
same-origin and no per-image exception appears in the frozen page. The exact
image is now frozen, integrity-checked, attributed, and entered in the
component asset and rights records. There are no external
instructional media or code dependencies in the lesson main.

## Exercises, solutions, and self-study closure

- Example 6.1 is a complete worked derivation in continuous prose.
- Example 6.2 has one explicit `Solution` section and a complete numerical
  calculation after correcting line 673.
- There are no independent exercises, staged hints, short answers, or
  mastery checks in the public lesson.
- Line 653 promises additional practice “from the homework,” but that homework
  is not part of the public frozen corpus. This is a self-study/assessment gap,
  not evidence that an omitted private item is licensed for redistribution.
- The overview promises treatment of factors affecting interval length, but
  the body provides only a summary bullet naming sample size, confidence level,
  and variability. The later original mastery companion should supply the
  derivation and exercises.

## Surface defects that should not survive translation

- line 582: plural `X_1, ..., X_n` takes “are,” not “is”;
- line 629: `a a random variable`;
- line 630: a pivotal quantity **has** or **possesses**, not “poses,” two
  characteristics;
- line 636: missing `to` in “use the moment generating function method to get”;
- line 642: `lets` should be `let's`;
- line 645: malformed “Again, we only consider ..., we get”; and
- line 687: `ror` should be `for`.

These are mechanical surface corrections, not changes to mathematical scope.

## Translation traps

- Preserve `penduga` versus observed `nilai dugaan`; never reproduce the
  source's estimator/estimate conflation.
- Preserve uppercase random endpoints/statistics and lowercase observed
  realizations.
- Keep a fixed parameter distinct from a random confidence procedure; do not
  turn a realized frequentist interval into a posterior-probability claim.
- State whether a quantile subscript denotes lower-tail or upper-tail
  probability; the lesson uses both conventions without warning.
- Distinguish exact known-variance Normal intervals, exact Normal `t`
  intervals, and large-sample approximate intervals using estimated standard
  errors.
- Keep `varians`, `simpangan baku`, and `galat baku` distinct.
- Preserve Gamma **shape** and **scale** parameterization; here `theta` is the
  scale.
