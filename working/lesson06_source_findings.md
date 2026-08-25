# Penn State STAT 415 Lesson 06 — mechanically proved source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson06.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson06`
- bytes: `77034`
- SHA-256:
  `abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06`
- expected normalized document identity: `O006-PSU-007`
- corroborating audit: `working/lesson06_math_audit.md`

Only defects directly demonstrated by the frozen source, elementary
probability/algebra, the displayed numerical values, or deterministic
DOM/asset inspection are registered. Preferences are explicitly excluded.

## L06-D001 — estimator and point estimate are conflated

- location: line 537
- source: “finding an estimator, or point estimate” treats the two objects as
  synonyms.
- proved correction: a point estimator is a statistic `T(X)`; `T(x)` after
  observing data is its point estimate. Translate as **penduga titik** versus
  **nilai dugaan titik**.

## L06-D002 — confidence-probability equality sign is missing

- location: line 600
- source ends the probability expression with `]1-alpha`.
- proved correction: it must end with `]=1-alpha`.

## L06-D003 — Figure 6.1 confuses random variable and critical value

- location: `#fig-standardnormal`, source line 567; official image pixels
- source image labels its cut points `-Z_(alpha/2)` and `Z_(alpha/2)` while
  lines 557–562 correctly define fixed critical values with lowercase `z`.
- proved correction: label the cut points `-z_(alpha/2)` and
  `z_(alpha/2)`, or add an adjacent derivative note that states the corrected
  notation.

## L06-D004 — chi-square quantile convention silently changes

- locations: lines 557–562 and 644–651
- source explicitly defines `z_p` by upper-tail probability, then uses
  `chi-square_p(4)` as a lower-tail quantile without defining the switch. The
  numbers prove that `chi-square_.05(4)=0.7107` and
  `chi-square_.95(4)=9.4877` are intended.
- proved correction: define `q_p=F^(-1)_(chi-square(4))(p)` and write
  `P(q_.05 <= 2Y/theta <= q_.95)=.90` and
  `[2Y/q_.95,2Y/q_.05]`. The source's numerical endpoints are correct.

## L06-D005 — large-sample conditions are overstrong and incomplete

- locations: lines 658–665
- source says the estimator “needs to be unbiased” and the standard error need
  only be “known or can be found.”
- proved correction: the interval requires
  `(hat(theta)-theta)/hat(se) ->d N(0,1)`. Exact unbiasedness is not necessary;
  asymptotically negligible bias suffices. If standard error is estimated, its
  consistency or an equivalent studentization result must be stated.

## L06-D006 — Example 6.2 standard error is dimensionally and numerically wrong

- location: line 673
- source gives sample variance `s^2=256`, but writes a squared-standard-error
  symbol equal to `s/sqrt(64)=256`.
- proved correction: `s=16` and
  `estimated SE(xbar)=s/sqrt(64)=16/8=2`. The following line uses 2 and the
  reported approximate interval `(29.71,36.29)` is correct.

## L06-D007 — unknown-variance t interval omits its assumptions and df

- location: line 688
- source writes `t_(alpha/2,df)` without defining `df` or stating the model.
- proved correction: for an iid Normal sample,
  `xbar +/- t_(alpha/2,n-1) S/sqrt(n)` is exact. Outside that model it needs an
  explicit approximation/robustness qualification.

## L06-D008 — Figure 6.1 has incomplete alternative text and no caption

- locations: lines 564–571
- source alt text mentions only the centered `1-alpha` area; the visible
  caption is only “Fig 6.1,” and the lightbox title has no description.
- correction: describe both `alpha/2` tails and the corrected critical values
  `+/-z_(alpha/2)` in alt or adjacent prose; do not rely on color alone.

## L06-D009 — unambiguous surface defects

- line 582: plural sample variables take “are,” not “is”;
- line 629: duplicated `a`;
- line 630: `poses two characteristics` should be “has/possesses”;
- line 636: missing `to` before “get the distribution”;
- line 642: `lets` should be `let's`;
- line 645: malformed comma splice; and
- line 687: `ror` should be `for`.

## L06-D010 — proof role is not encoded semantically

- location: Section `#proof`
- source: the complete proof is present under a generic section and `Proof:`
  heading but there is no semantic `.proof` container
- additive correction: preserve every proof byte and bind the section to the
  proof role in downstream metadata; do not delete or rewrite it merely to
  imitate an upstream source format that was not published

## Correct calculations that must not be “fixed”

- Strict `L < theta < U` in the introductory schematic is a legitimate open
  interval and is not a mathematical defect.
- The known-variance Normal interval, its standardization, and the inequality
  manipulation through line 598 are correct.
- The Gamma MGF transformation, `2Y/theta ~ chi-square(4)`, and the numerical
  interval `[0.2659,3.5502]` are correct once the lower-tail quantile convention
  is made explicit.
- “Expect 950 of 1,000” is an expectation, not a guarantee, and is acceptable
  as written.
- Example 6.2's final arithmetic is correct; only the preceding standard-error
  identity/value is wrong. Label the result approximate.

## Asset, rights, and assessment disposition

The lesson has one direct instructional asset and no code or external media:

- URL: `https://online.stat.psu.edu/stat415/assets/ci_1.png`
- current official read-only identity checked 2026-08-25: 67,496 bytes,
  1334 by 640 PNG, SHA-256
  `2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f`,
  `Last-Modified: Thu, 27 Jun 2024 10:27:13 GMT`
- local state: exact bytes frozen at
  `authority/assets/stat415/lesson06/assets/ci_1.png`, closed by
  `authority/LESSON06_ASSET_MANIFEST.csv` and
  `working/lesson06_asset_closure.json`
- rights witness: the page footer says CC BY-NC 4.0 except where otherwise
  noted; the image is same-origin and no per-image exception is visible
- redistribution state: exact asset frozen and validated; URL, headers, hash,
  dimensions, alt decision, rights, and attribution are recorded

The public lesson contains two worked examples but no independent exercise or
hint. Line 653 delegates practice to homework that is absent from the public
corpus. Treat this as an assessment-closure gap for the original mastery
companion, not as permission to reconstruct private assignments.
