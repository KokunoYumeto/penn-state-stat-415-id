# Penn State STAT 415 Lesson 10 — mechanically proved source findings

Authority inspected without mutation:

- file: `authority/upstream/stat415/Lesson10.html`
- official URL: `https://online.stat.psu.edu/stat415/Lesson10`
- bytes: `152767`
- SHA-256: `0cb938a114d27b03ef3196c24a2e87b79a1a466b9dcbe370e6e6553947446bf5`
- normalized document identity: `O006-PSU-011`
- corroborating audit: `working/lesson10_math_audit.md`

Only frozen-surface, exact algebra/probability, DOM, binary, and code findings
are registered. Authority bytes are never corrected in place.

## L10-D001 — overview promises two population comparisons not present

- classification: coverage surface defect
- evidence: `"move beyond single-sample tests to compare two populations"`
- derivative disposition: The instructional main contains only one-sample/order-statistic, power, sample-size, and Wald examples; translate the actual scope without repeating the unsupported promise.

## L10-D002 — poisson test exceeds nominal point one level

- classification: outright level defect
- evidence: `{"actual_size": 0.10540810546917745, "largest_nonrandomized_size_below_point_one": 0.04461910095530105, "randomize_at_sum_eq_6": 0.911034807817211, "source_rule": "reject sum>=6"}`
- derivative disposition: Rejecting at a sum of 6 has size 0.105408..., not level 0.10. Use sum>=7 for a conservative nonrandomized test, or randomize at sum=6 with the recorded probability for exact size 0.10.

## L10-D003 — poisson tail rounded inconsistently

- classification: outright numerical defect
- evidence: `{"conclusion": "0.1055", "table_and_calculation": "0.1054"}`
- derivative disposition: Use the same rounded value, while retaining the more important exact-level correction.

## L10-D004 — confidence interval test duality boundary unspecified

- classification: boundary qualification omission
- evidence: `{"source_interval": "closed reported interval", "source_test": "reject at t>=critical or t<=-critical"}`
- derivative disposition: State a consistent equality convention: a closed 1-alpha interval corresponds to rejection when the null value lies outside it under the usual p<alpha rule; p<=alpha changes endpoint treatment.

## L10-D005 — nonzero p value written as approximately zero

- classification: precision defect
- evidence: `"p-value ... approximately 0.000"`
- derivative disposition: Report a positive bound or adequate digits; a continuous-test p-value here is not zero.

## L10-D006 — type error label truncated twice

- classification: outright mechanical defect
- evidence: `["P(Type I erro)", "P(Type II erro)"]`
- derivative disposition: Restore 'error' in both definitions.

## L10-D007 — adult population student sample mismatch

- classification: sampling frame defect
- evidence: `"X is an adult-American IQ, followed by a random sample of students"`
- derivative disposition: A student sample is not automatically a random sample of adult Americans; align the target population and sampling frame or state the limitation.

## L10-D008 — power example parenthesis and equality malformed

- classification: outright formula surface defect
- evidence: `["1.645(16/sqrt(16)=106.58)", "next aligned probability line lacks an equals sign"]`
- derivative disposition: Close the scale-factor parenthesis before '=106.58' and retain the equality at the start of the following probability line.

## L10-D009 — power function argument switches between mu and u

- classification: outright notation defect
- evidence: `["K(mu)", "K(u)", "beta(u)"]`
- derivative disposition: Use the declared parameter mu consistently.

## L10-D010 — type two error subtracts z score instead of power

- classification: outright numerical defect
- evidence: `"1-0.326=0.6278"`
- derivative disposition: The correct complement is 1-0.3722=0.6278; 0.326 is the standardized cutoff.

## L10-D011 — sample size called only way to reduce both errors

- classification: outright overgeneralization
- evidence: `"only way alpha and beta can be decreased simultaneously is increasing n"`
- derivative disposition: Within the fixed Normal-mean design increasing n does so, but better measurements, lower variance, stronger design, or a more efficient test can also improve both errors.

## L10-D012 — rounded up mean sample size does not retain beta point one

- classification: rounding qualification omission
- evidence: `{"actual_beta": 0.0869741431142243, "cutoff": 42.737445468371504, "n": 13}`
- derivative disposition: After rounding n up to 13 and recalculating the alpha-based cutoff, beta is about 0.08697 and power about 0.91303, not exactly 0.10 and 0.90.

## L10-D013 — proportion sample size results presented as exact

- classification: approximation qualification omission
- evidence: `{"exact_alpha": 0.009647335485395895, "exact_beta": 0.20343667138369453, "rule": "phat>0.5367, hence X>=538"}`
- derivative disposition: The derivation is a Normal approximation. Under Binomial sampling the displayed rule has alpha about 0.009647 and beta about 0.203437, so label the design approximate.

## L10-D014 — any mle claimed asymptotically normal

- classification: outright mathematical overclaim
- evidence: `"for any MLE, regardless of the distribution"`
- derivative disposition: MLE asymptotic normality requires regularity, identifiability, an interior true parameter, nonsingular information, consistency, and appropriate differentiation/interchange conditions; nonregular and boundary cases fail.

## L10-D015 — unstandardized wald p value not centered at null

- classification: outright mathematical defect
- evidence: `"P(|T|>=|theta-hat|) for T~N(c,se^2)"`
- derivative disposition: Use P(|T-c|>=|theta-hat-c|), or standardize first. The source expression is wrong whenever c is nonzero.

## L10-D016 — wald recipe omits p equals alpha and says accept disprove

- classification: boundary and inference defect
- evidence: `["p<alpha", "p>alpha", "accept H_A", "disprove H_0"]`
- derivative disposition: State the p=alpha action explicitly and describe rejection as evidence against H0, not proof or acceptance of HA.

## L10-D017 — bernoulli conclusion changes point two five to point zero two five

- classification: outright parameter typo
- evidence: `{"conclusion": 0.025, "tested": 0.25}`
- derivative disposition: The stated game rate must remain 0.25.

## L10-D018 — small boundary bernoulli wald test unqualified

- classification: approximation qualification omission
- evidence: `{"exact_doubled_left_tail": 0.04862524973032123, "exact_probability_ordered_two_sided": 0.038177041808921786, "wald_p": "about 0.000040"}`
- derivative disposition: With n=20, one success, and a parameter near the boundary, the Wald approximation is severely unreliable. Label it as a cautionary approximation and compare an exact or score procedure.

## L10-D019 — numeric optimizer unconstrained and hessian mislabeled

- classification: reproducibility and method defect
- evidence: `"optim(.5, ..., hessian=TRUE) without bounds; out$hessian called Fisher Information"`
- derivative disposition: Constrain p to (0,1), handle invalid likelihood values, and call the numerical Hessian observed information; expected Fisher information is a distinct expectation even though they coincide here at the Bernoulli MLE.

## L10-D020 — summary drops three mathematical symbols

- classification: outright surface defect
- evidence: `["significance level ()", "without altering .", "approximate -test"]`
- derivative disposition: Restore alpha in the first two locations and z in 'approximate z-test'.

## L10-D021 — nineteen figure image identifiers duplicated

- classification: topology accessibility defect
- evidence: `["fig-415_IQpower", "fig-415_IQpowerB", "fig-415_IQpowerC", "fig-415_IQtypeI", "fig-415_IQtypeIB", "fig-415_engineerpower", "fig-415_engineertype1", "fig-415_engineertype1-B", "fig-415_rttailengineer", "fig-STAT-415-SEC-5-02", "fig-STAT-415-SEC-5-13Version7", "fig-STAT-415-SEC-5-17", "fig-alphabeta1", "fig-alphabeta3", "fig-alphacriticalp55", "fig-powerfnkmu3", "fig-powerfunofkmu1", "fig-powerfunofkmu2", "fig-rttailcritical"]`
- derivative disposition: Preserve source topology in normalization; mint unique reader DOM ids while retaining stable catalogue bindings.

## L10-D022 — three incorrect alts and label only captions

- classification: accessibility defect
- evidence: `{"incorrect_alts": {"assets/415_engineerpower.png": "Normal curves showing the area for beta, a type II error with the z test statistic shown.", "assets/415_engineertype1.png": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.", "assets/415_rttailengineer.png": "Normal curve with center at 0 showing two-tail critical area for alpha of .05."}, "label_only_captions": 19, "uncaptioned_images": 3}`
- derivative disposition: The first two named alts call one-tailed error regions two-tailed; the power figure calls its region beta. Add correct non-color-dependent descriptions and meaningful captions.

## L10-D023 — tables lack captions and header scope

- classification: accessibility defect
- evidence: `[{"caption": false, "th": 3, "th_with_scope": 0}, {"caption": false, "th": 4, "th_with_scope": 0}]`
- derivative disposition: Add captions and explicit row/column header scope without changing values.

## L10-D024 — r code has no environment or expected output contract

- classification: reproducibility omission
- evidence: `{"inline_code_nodes": 1, "label_style_nodes": 5, "output_blocks": 3, "source_code_blocks": 5}`
- derivative disposition: Preserve code and outputs byte-for-byte in normalized source; the derivative should identify base-R/runtime assumptions and verify expected outputs.

## L10-D025 — page title contains replacement characters

- classification: encoding surface defect
- evidence: `"10� Hypothesis Tests (Part II) � STAT 415"`
- derivative disposition: Use a clean reader title while retaining the frozen source-title witness in provenance.

## L10-D026 — wald p value switches strict and nonstrict extremeness

- classification: boundary definition defect
- evidence: `["P(|Z|>|Z*|)", "P(Z<=-|Z*|)"]`
- derivative disposition: Define the p-value with outcomes at least as extreme and use a consistent boundary convention.

## L10-D027 — one sided power described by absolute distance

- classification: direction qualification omission
- evidence: `"as mu moves further away from 100, power increases"`
- derivative disposition: For this right-tailed test, power increases as mu moves to the right; moving equally far below 100 decreases power.

## L10-D028 — poisson transition is incomplete sentence

- classification: outright mechanical defect
- evidence: `"Recall that the Poisson distribution."`
- derivative disposition: Complete the sentence by stating that the distribution is discrete and may not attain the nominal size with a nonrandomized cutoff.

## Frozen production boundary

The semantic main contains 369 math surfaces, 9 code nodes, 2 tables, and 22 unique instructional assets. All 540 translatable segments have stable pending IDs.

The complete next translation range is
`O006-PSU-011-S0001` through `O006-PSU-011-S0540`.

