# Lesson 07 terminology QA — asymptotic distribution of MLEs

Checked: 2026-08-25

## Authority and scope

The bounded census used the complete frozen instructional main in
`authority/upstream/stat415/Lesson07.html` (105,026 bytes; SHA-256
`2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`),
including all 148 math surfaces, 47 code nodes, six worked examples, 12 frozen
console outputs, and both figures.

This file records Lesson07 decisions only. It does not allocate term IDs and
does not mutate `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`. Candidate terms
remain proposals for the production controller.

## Controlling existing glossary decisions

The cumulative glossary remains authoritative:

- `random variable` -> **peubah acak** (`O006-TERM-0005`);
- `random sample` -> **sampel acak** (`O006-TERM-0006`);
- `support` -> **himpunan dukungan** (`O006-TERM-0009`);
- `probability mass function` / `probability density function` -> **fungsi
  massa peluang (PMF)** / **fungsi kepadatan peluang (PDF)**
  (`O006-TERM-0010`–`0011`);
- `expectation` / `mean` -> **nilai harapan** / **rataan**
  (`O006-TERM-0013`–`0014`);
- `estimator` / `estimate` / `estimation` -> **penduga** / **nilai dugaan** /
  **pendugaan** (`O006-TERM-0018`–`0020`);
- `standard error` -> **galat baku** (`O006-TERM-0021`);
- `confidence interval` -> **selang kepercayaan** (`O006-TERM-0022`);
- `likelihood` / `maximum likelihood estimation` -> **fungsi kemungkinan** /
  **pendugaan kemungkinan maksimum (MLE)** (`O006-TERM-0025`–`0026`);
- `parameter space` -> **ruang parameter** (`O006-TERM-0033`);
- `consistency` -> **konsistensi** (`O006-TERM-0038`);
- `maximum likelihood estimator` / `maximum likelihood estimate` ->
  **penduga kemungkinan maksimum (MLE)** / **nilai dugaan kemungkinan
  maksimum** (`O006-TERM-0058`–`0059`);
- `log-likelihood function` -> **fungsi log-kemungkinan**
  (`O006-TERM-0060`);
- `single-parameter model` / `multiparameter model` -> **model berparameter
  tunggal** / **model multiparameter** (`O006-TERM-0063`–`0064`);
- `numerical optimization` / `objective function` / `starting value` ->
  **optimisasi numerik** / **fungsi objektif** / **nilai awal**
  (`O006-TERM-0065`, `0072`–`0073`);
- `rate parameter` / `scale parameter` -> **parameter laju** / **parameter
  skala** (`O006-TERM-0077`–`0078`); and
- `confidence level` / `critical value` -> **tingkat kepercayaan** / **nilai
  kritis** (`O006-TERM-0086`, `0091`).

These decisions take precedence over variant wording in individual Indonesian
sources.

## Bounded representative Indonesian evidence

The evidence search was restricted to Indonesian university, journal, and
official academic pages relevant to the new concepts.

1. The Universitas Gadjah Mada thesis record on MLE asymptotics uses
   **konsistensi** and **normalitas asimtotik** for maximum-likelihood
   estimators:
   <https://etd.repository.ugm.ac.id/penelitian/detail/60045>.
2. The Universitas Halu Oleo mathematics journal writes **secara asimtotik
   berdistribusi normal**, **penduga MLE**, and **matriks informasi Fisher** in
   the same inferential setting:
   <https://jmks.uho.ac.id/index.php/journal/article/download/104/103/1028>.
3. A Universitas Mulawarman mathematical-statistics thesis uses **matriks
   Hessian** and **matriks Informasi Fisher** and displays the negative-
   expected-Hessian relationship:
   <https://repository.unmul.ac.id/bitstream/handle/123456789/4784/FATMA_1607015002.pdf?sequence=1>.
4. A mathematical-statistics proceedings article from Universitas PGRI
   Mahadewa attests the adjective **ekuivarian** in `estimator ekuivarian`:
   <https://ojs.mahadewa.ac.id/index.php/senama/article/download/350/272/601>.
5. Universitas Negeri Makassar's probability article uses **kekonvergenan
   dalam peluang**, **kekonvergenan dalam distribusi**, and **kekonvergenan
   dalam rata-rata** for random-variable sequences:
   <https://ojs.unm.ac.id/JMathCoS/article/view/33882/0>.
6. ITB's official mathematical-statistics course description independently
   uses **konvergen dalam peluang** and **konvergen dalam distribusi**:
   <https://six.itb.ac.id/pub/kur2024/matakuliah/53243>.

The bounded official Indonesian sample did not establish a dominant localized
form for `uniform integrability` or `observed information`. Because both are
needed for proved corrections, introduce the precise Indonesian form together
with its English term once rather than pretending that an unattested variant
is universally standard.

## Stable Lesson07 reader decisions

- Use **distribusi asimtotik** for `asymptotic distribution` and **normalitas
  asimtotik** for the noun `asymptotic normality`. In explanatory sentences,
  **secara asimtotik berdistribusi Normal** is often clearer than turning every
  occurrence into a noun phrase.
- Use **penduga konsisten** and **konsistensi**. Express
  `hat(theta)_n ->p theta` as **konvergen dalam peluang menuju theta**. Do not
  translate consistency as accuracy, unbiasedness, or expectation convergence.
- Use **sifat ekuivarian** and **penduga ekuivarian**. Retain the source's
  mathematical direction: the MLE of a transformation is the corresponding
  transformation of the MLE under the stated conditions.
- Use **syarat keteraturan** for `regularity conditions`. Preserve the explicit
  statement that the full list and proofs are omitted. Do not silently turn
  the source's two informal bullets into a complete theorem.
- Use **informasi Fisher** and **matriks informasi Fisher**. Capitalize
  `Fisher`, preserve `I(theta)`, and state whether `I` is per observation or
  for the full sample.
- Use **matriks Hessian** for `Hessian matrix`. Keep the executable R names
  `hessian`, `out$hessian`, `solve`, and `diag` byte-identical inside code.
- Distinguish **informasi Fisher (nilai harapan negatif Hessian)** from
  **informasi teramati (observed information; negatif Hessian pada data yang
  diamati)**. On first occurrence, the parenthetical English term prevents an
  unproved claim that the short Indonesian form is uniquely standardized.
- Use **selang kepercayaan asimtotik** for `asymptotic confidence interval`
  and **selang Wald asimtotik** when the construction itself needs a concise
  name. Its target is a parameter: write **selang kepercayaan untuk parameter
  p berdasarkan MLE**, never “selang kepercayaan untuk MLE p.”
- Use **galat baku asimtotik** or **taksiran galat baku asimtotik** according
  to whether the quantity is theoretical or evaluated at an estimate.
- Use **integrabilitas seragam (uniform integrability)** on first occurrence
  and **integrabilitas seragam** thereafter. It is an additional condition
  that can upgrade convergence in probability to `L1` convergence; it is not
  a synonym for consistency.
- Use **konvergensi dalam L1** and retain `L1` in mathematical prose. Explain
  it once as `E|hat(theta)_n-theta| -> 0`.
- Use **titik interior ruang parameter** for `interior point of the parameter
  space`. Keep **himpunan dukungan** for possible data values. The two sets
  must never be conflated.
- Use **rasio odds (OR)** for `odds ratio`, retaining `OR` because the formula
  and estimator notation use it.
- Preserve the exponential parameterization as **parameter skala**: here
  `E(X)=theta`. Do not rewrite `theta` as a rate.
- Translate the continuous exponential `f` as **fungsi kepadatan peluang
  (PDF)** and state `x>=0`, `theta>0`. Do not copy the source's erroneous PMF
  label.
- Use **bootstrap parametrik**, **bootstrap nonparametrik**, and **metode
  Delta** only in the correction that labels the overview/summary as stale
  scope. Do not imply that Lesson07 actually teaches those methods.

## Candidate additions for controller review — no IDs claimed

| en-US concept | Proposed id-ID | Decision |
|---|---|---|
| asymptotic distribution | distribusi asimtotik | general limiting distribution |
| asymptotic normality | normalitas asimtotik | noun; use `secara asimtotik berdistribusi Normal` in prose |
| consistent estimator | penduga konsisten | consistency is convergence in probability here |
| equivariance / equivariant | sifat ekuivarian / ekuivarian | estimator transformation property |
| regularity conditions | syarat keteraturan | preserve incomplete-list disclaimer |
| Fisher information | informasi Fisher | specify per-observation versus total-sample convention |
| Fisher information matrix | matriks informasi Fisher | multiparameter form |
| Hessian matrix | matriks Hessian | preserve code identifiers |
| observed information | informasi teramati (observed information) | negative observed Hessian; bilingual first use |
| asymptotic confidence interval | selang kepercayaan asimtotik | parameter-targeted Wald interval |
| convergence in probability | konvergensi dalam peluang | estimator consistency mode |
| uniform integrability | integrabilitas seragam (uniform integrability) | bilingual first use; expectation-convergence condition |
| asymptotic standard error | galat baku asimtotik | distinguish from standard deviation |
| odds ratio | rasio odds (OR) | retain OR |

No cumulative ID is reserved here. Admission and ID allocation belong to the
shared terminology controller, outside the Lesson07 write boundary.

## Mandatory mathematical distinctions

### Consistency versus convergence of expectations

Translate the source correction as:

> Konsistensi saja tidak menjamin bahwa nilai harapan penduga konvergen menuju
> parameter. Implikasi tersebut memerlukan syarat tambahan, misalnya keluarga
> penduganya memiliki integrabilitas seragam.

The counterexample in `working/lesson07_math_audit.md` is controlling. Do not
soften this into “usually true” or omit the extra condition.

### Expected versus observed information

Use notation and prose consistently:

```text
I_n(theta) = -E_theta[ell_n''(theta)]      informasi Fisher sampel penuh
J_n(hat(theta)) = -ell_n''(hat(theta))     informasi teramati
```

When `optim` minimizes a negative log-likelihood, its returned Hessian is the
observed curvature of that objective. It may estimate the covariance through
its inverse under regularity; it is not automatically the expectation above.

### Information scaling

Earlier Wald formulas use total-sample information `I_n`, so no additional
`sqrt(n)` appears. The final display `M0146` uses per-observation information
`I_1(theta)`, so `sqrt(n)` is explicit. Add **per pengamatan** or **untuk
seluruh sampel** wherever necessary; do not let the same bare `I` appear to
have both scales in one explanation.

### Estimator versus realized output

Use **penduga MLE** for random `hat(theta)(X)`. The numbers returned by
`optim`, such as `-6.564774`, are **nilai dugaan MLE**. The confidence interval
targets `theta`, not either the estimator or its realized value.

## Translation-boundary and code traps

- Preserve every segment's leading and trailing whitespace exactly; many
  prose fragments surround protected math or inline-code nodes.
- Do not translate executable identifiers or R syntax: `optim`, `hessian`,
  `out$par`, `out$hessian`, `sqrt(diag(solve(I)))`, `dgeom`, `dnorm`, and
  `set.seed` remain unchanged.
- Correct the comment semantics adjacent to `U0353`, but do not replace the
  correct executing expression with the source comment's reciprocal error.
- Keep uppercase `MLE`, capitalized `Fisher` and `Hessian`, and the distinctions
  between parameter `p`, probability operator `P`, information matrix `I`, and
  identity-free prose.
- Keep the source's small-`n` caution for the Bernoulli Wald interval.
- Correct `M0088` by retaining `1.96` in the middle term while leaving the
  correct numeric endpoints unchanged.
- Correct `M0104` to `xbar +/- 1.96 xbar/sqrt(n)`; do not carry over
  `sqrt(n^3/xbar^2)`.
- In the two figure descriptions, say what is visible: the geometric histogram
  is strongly right-skewed with mass near zero; the seeded Normal histogram is
  roughly bell-shaped around `-7`. The generic source alt strings are not
  sufficient on their own.

## Ready translation range

The normalized segment inventory is contiguous from
`O006-PSU-008-S0001` through `O006-PSU-008-S0237`. A four-part production
split that preserves order and avoids overlap is:

1. `S0001`–`S0060` (60 segments),
2. `S0061`–`S0120` (60 segments),
3. `S0121`–`S0180` (60 segments), and
4. `S0181`–`S0237` (57 segments).

The immediate next translation range is
`O006-PSU-008-S0001`–`O006-PSU-008-S0060`.
