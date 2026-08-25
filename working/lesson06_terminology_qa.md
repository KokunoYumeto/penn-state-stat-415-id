# Lesson 06 terminology QA — confidence intervals

Checked: 2026-08-25

## Authority and evidence

The bounded census used the complete frozen instructional main in
`authority/upstream/stat415/Lesson06.html` (77,034 bytes; SHA-256
`abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06`),
including all 102 math surfaces, the theorem/proof, both examples, the solution,
the summary, and the figure context.

Existing component decisions remain controlling:

- `confidence interval` -> **selang kepercayaan** (`O006-TERM-0022`);
- `estimator` / `estimate` / `estimation` -> **penduga** / **nilai dugaan** /
  **pendugaan** (`O006-TERM-0018`–`0020`);
- `point estimator` / `point estimate` -> **penduga titik** / **nilai dugaan
  titik** (`O006-TERM-0031`–`0032`);
- `standard error` -> **galat baku** (`O006-TERM-0021`);
- `variance` / `standard deviation` -> **varians** / **simpangan baku**
  (`O006-TERM-0036`, `O006-TERM-0079`);
- `quantile` -> **kuantil** (`O006-TERM-0083`);
- `degrees of freedom` / `chi-square` -> **derajat kebebasan** /
  **khi-kuadrat** (`O006-TERM-0028`–`0029`); and
- `Central Limit Theorem` -> **Teorema Limit Pusat** (`O006-TERM-0027`).

The representative Indonesian mathematical-statistics evidence already used
for Lessons 01–05 continues to support **peubah acak**, **sampel acak**,
**rataan**, **nilai harapan**, **penduga**, and **varians**. A bounded
exact-topic check adds the following evidence for the new Lesson 06 terms:

1. The Universitas Mulawarman statistics journal article at
   `https://fmipa.unmul.ac.id/files/docs/1.%20Haeruddin.pdf` uses
   **penaksiran selang**, **interval konfidensi**, **koefisien konfidensi**, and
   **kuantitas pivotal** in a mathematical bootstrap-confidence-interval
   derivation. These are attested variants, not a reason to replace the
   component's established `selang kepercayaan`.
2. The Universitas Kristen Indonesia textbook
   `https://repository.uki.ac.id/8820/1/DasarDasarStatistikaInferensi.pdf`
   repeatedly uses **selang kepercayaan**, **koefisien kepercayaan**, and
   **batas selang kepercayaan**, and distinguishes a random interval generated
   by the sample from its realized endpoints.
3. The exact-topic *Jurnal Matematika Integratif* article
   `https://jurnal.unpad.ac.id/jmi/article/download/58428/pdf` uses **besaran
   pivot**, gives **kuantitas pivotal** as a documented synonym, and defines it
   as a function of data and parameter whose distribution is parameter-free.
4. The Universitas Ahmad Dahlan mathematical-statistics text
   `https://eprints.uad.ac.id/29156/1/BUKU_Stat_Mat2.pdf` uses **Estimator
   Interval**, **Interval Kepercayaan**, and **Metode Kuantitas Pivotal**.
   These show genuine field variation; reader consistency still favors the
   existing Indonesian terms below.

## Stable reader decisions

- Keep **selang kepercayaan** for `confidence interval`. `Interval
  konfidensi` is a documented variant, but alternating the two within this
  component would add no value.
- Use **koefisien kepercayaan** for the proportion `1-alpha` and **tingkat
  kepercayaan** for `(1-alpha)100%`. Keep **tingkat signifikansi** for `alpha`;
  it is not a synonym for confidence level.
- Use **pendugaan selang** for the process `interval estimation` and **penduga
  selang** for a random interval-valued rule. For the interval computed from
  observed data, ordinary prose may simply say **selang kepercayaan yang
  diperoleh**. Do not collapse `penduga` into `nilai dugaan`.
- Use **besaran pivot (pivotal quantity)** on first occurrence and **besaran
  pivot** thereafter. **Kuantitas pivotal** is an attested synonym and may be
  indexed as an alias, but should not alternate in reader prose.
- Use **batas bawah** and **batas atas selang kepercayaan** for lower and upper
  bounds, **peluang cakupan** for `coverage probability`, and **tingkat
  cakupan nominal** for a nominal coverage level.
- Use **nilai kritis** for `critical value` and **kuantil** for a distribution
  quantile. Because the source switches silently between upper-tail and
  lower-tail subscripts, write **kuantil bawah ke-p** or define the CDF inverse
  explicitly whenever needed.
- Use **selang-Z untuk rataan** and **selang-t untuk rataan**. Preserve capital
  `Z` for the random variable and lowercase `z_(alpha/2)` for its fixed
  critical value.
- Use **distribusi normal baku**, **fungsi pembangkit momen (MGF)**,
  **distribusi Gamma**, and **distribusi khi-kuadrat dengan empat derajat
  kebebasan**.
- Use **selang kepercayaan sampel besar** and label its result **hampiran**
  when it relies on asymptotic normality and an estimated standard error.
  Reserve **eksak** for results justified by the stated finite-sample model.
- Use **frekuentis** for `frequentist`. Explain the interpretation through a
  procedure's repeated-sampling **peluang cakupan**, not by assigning a
  post-data probability to the fixed parameter.
- Keep **rataan populasi**, **rataan sampel**, **proporsi populasi**, and
  **proporsi sampel**. Do not introduce `mean`, `average`, or `rata-rata` as
  alternating core terms inside formulas and theorem prose.

## Admitted glossary additions

The production controller checked the cumulative allocation and admitted these
ten non-overlapping rows in `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`.

| Term ID | en-US | id-ID | Decision |
|---|---|---|---|
| O006-TERM-0085 | confidence coefficient | koefisien kepercayaan | proportion `1-alpha` |
| O006-TERM-0086 | confidence level | tingkat kepercayaan | percentage `(1-alpha)100%` |
| O006-TERM-0087 | interval estimation | pendugaan selang | process |
| O006-TERM-0088 | interval estimator | penduga selang | random interval-valued rule |
| O006-TERM-0089 | pivotal quantity | besaran pivot | introduce English alias once |
| O006-TERM-0090 | coverage probability | peluang cakupan | repeated-sampling probability |
| O006-TERM-0091 | critical value | nilai kritis | fixed distribution quantile |
| O006-TERM-0092 | confidence bounds | batas selang kepercayaan | use lower/upper qualifiers |
| O006-TERM-0093 | moment-generating function | fungsi pembangkit momen (MGF) | retain MGF |
| O006-TERM-0094 | Z-interval | selang-Z | retain `Z` label |

## Translation traps and mandatory clarifications

- Correct the source's line-537 conflation: **penduga titik** is not a
  realized **nilai dugaan titik**.
- In the pre-sample statement, the interval endpoints are random. After data
  are observed, the interval is fixed and either covers the parameter or does
  not. Preserve this distinction without turning the lesson into a Bayesian
  posterior claim.
- State which tail a quantile subscript denotes. For Example 6.1, a locale-
  neutral expression using `q_p=F^(-1)(p)` is safer than copying the source's
  undefined chi-square subscript convention.
- Do not translate capital `Z` and lowercase `z` as if they were the same
  mathematical object.
- In Example 6.2, translate the corrected quantity as **taksiran galat baku
  rataan sampel**, equal to `s/sqrt(n)=2`; do not repeat the squared-SE symbol
  or the value 256.
- Distinguish **varians sampel** `s^2=256`, **simpangan baku sampel** `s=16`,
  and **taksiran galat baku** `s/sqrt(64)=2`.
- The summary's unknown-variance formula is an exact **selang-t** only for the
  specified iid Normal model with `n-1` degrees of freedom. The large-sample
  example is an approximation.
- Preserve the Gamma parameterization: `theta` is a **parameter skala**, not a
  rate, and `2Y/theta` has a parameter-free distribution.
