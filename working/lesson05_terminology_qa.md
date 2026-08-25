# Lesson 05 terminology QA — numerical MLE and R

Checked: 2026-08-25

## Authority and bounded census

The terminology census used the frozen official Penn State authority
`authority/upstream/stat415/Lesson05.html` (190,308 bytes; SHA-256
`dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d`).
The complete reader-facing body under `main#quarto-document-content` contains
about 5,010 English word-like tokens. It covers all 22 instructional sections,
both structured examples, the 97 visible R source-code blocks, 79 output
blocks, and the numerical-MLE sequence.

Exact case-insensitive phrase-family matches in the complete body show the
recurring terminology pressure:

- `optim`: 31;
- `vector(s)`: 34;
- numeric/numerical MLE wording: 24;
- `starting value` or `initial value`: 19;
- iteration/iterative wording: 14;
- `negative log-likelihood` variants: 12;
- `Newton's Method`: 12 and `Newton-Raphson`: 4;
- convergence wording: 10;
- simulation wording: 9;
- `grid search`: 8;
- `numerical optimization`: 6;
- root/root-finding wording: 6;
- `data frame(s)`: 4;
- `standard deviation`: 4;
- `quantile(s)`: 3; and
- `scalar(s)`: 2.

These are literal phrase-family counts, not counts of independent semantic
units. `score function`, `function evaluation`, and `objective function` are
absent or mislabeled in the source prose but are required by the mathematical
audit to state the algorithms and `optim` output correctly.

## Indonesian field evidence

1. The official IPB University repository record
   `https://repository.ipb.ac.id/handle/123456789/160852?show=full` uses
   **algoritma optimisasi Nelder-Mead**, `optim` in R, and a negative
   log-likelihood objective in one statistical-modeling context.
2. The ITS Department of Statistics journal article at
   `https://iptek.its.ac.id/index.php/inferensi/article/download/15558/7413`
   repeatedly uses **pencarian grid** for `grid search`. This established
   technical form is preferred over the intelligible but weakly attested
   literal alternative `pencarian kisi`.
3. The IPB repository record
   `https://repository.ipb.ac.id/handle/123456789/109921` uses **fungsi skor**
   in statistical estimation. The UIN Suska mathematics article at
   `https://ejournal.uin-suska.ac.id/index.php/SNTIKI/article/download/2932/1840`
   distinguishes **iterasi** from **evaluasi fungsi** in a numerical-method
   efficiency calculation.
4. The Universitas Jember repository source
   `https://repository.unej.ac.id/bitstream/handle/123456789/72712/1/Jefri`
   uses **kerangka data** for R's `data.frame`; current Indonesian R teaching
   also commonly retains `data frame`. The reader therefore introduces
   **kerangka data (data frame)** while preserving the executable identifier
   `data.frame` unchanged.
5. The Universitas Andalas R teaching material
   `https://matematika.fmipa.unand.ac.id/images/bahan-seminar/pakyudi.pdf`
   uses **vektor** and **kuantil** while explaining R's `r`/`d`/`p`/`q`
   distribution-family convention.
6. Indonesian university sources attest both **parameter laju** and
   **parameter skala** for exponential-family parameterizations, including
   `https://classroom.itats.ac.id/storage/materi/412104150073/11-2024/1731069243_Probabilitas%20dan%20Variabel%20Acak_5_Distribusi%20Probabilitas%20Kontinu.pdf`
   and `https://repo-dosen.ulm.ac.id/bitstream/handle/123456789/22875/Hidayah%20Ansori%20dkk%20Buku%20Teori%20Peluang_compressed.pdf`.

## Stable decisions and variants

- Use **pendugaan kemungkinan maksimum secara numerik** for the process and
  **hampiran numerik terhadap nilai dugaan kemungkinan maksimum** when an
  algorithm returns a tolerance- or grid-dependent approximation. Do not call
  the value `8.9` from a finite grid the exact MLE.
- Use **pencarian grid (grid search)** and **optimisasi numerik**. `Pencarian
  kisi` and `optimasi numerik` are documented variants, but alternating within
  one component would reduce continuity.
- Use **metode Newton–Raphson** for the update applied to the **fungsi skor**,
  and **pencarian akar** for its task. The score is the derivative of the
  log-likelihood. The tangent is taken to that score, not to the log-likelihood
  itself, and a score root still requires domain and maximum checks.
- Use **negatif fungsi log-kemungkinan (NLL)** for the quantity minimized by
  `optim`. This ordering makes the negation of the whole log-likelihood
  explicit; `fungsi kemungkinan negatif` is rejected because it names a
  different and generally meaningless object.
- Use **fungsi objektif** for the function supplied to an optimizer,
  **nilai awal** for an initial guess, **iterasi** for one algorithmic update,
  **evaluasi fungsi** for one objective/gradient call, and **kriteria
  konvergensi** for a stopping rule. A positive initial guess is not a domain
  constraint; `$counts` must not be translated as an iteration count; and
  convergence code zero is not proof of a valid global optimum.
- Keep **parameter laju** and **parameter skala** distinct. In the Lesson 05
  exponential code, `dexp(..., rate=1/theta)` makes `theta` the rataan/skala
  and `1/theta` the laju. Calling `theta` a rate would reverse the
  parameterization.
- Use **simpangan baku**, not `galat baku`, for standard deviation. The latter
  remains reserved for standard error. Use **skalar**, **vektor**, **kerangka
  data (data frame)**, **kuantil**, and **statistik ringkasan** in prose.
  Preserve `data.frame`, `rnorm`, `dnorm`, `pnorm`, `qnorm`, argument names,
  operators, output keys, decimal points, and other executable R syntax.

## Source terminology traps

- A `dXXX` function returns a density value for a continuous distribution or a
  probability-mass value for a discrete distribution. It becomes a likelihood
  factor only after the observation is fixed and the parameter is treated as
  variable. Do not translate density, mass, joint density/mass, likelihood,
  log-likelihood, and NLL as interchangeable quantities.
- Translate `draw/simulate a random variable` as **membangkitkan atau
  mensimulasikan peubah acak**, not as the literal visual verb `menggambar`.
  Exact simulated outputs require a recorded seed or frozen vector.
- `optim()` without a method argument uses Nelder–Mead; it is not the
  hand-coded Newton–Raphson update. The source's instruction to ignore most
  warnings must be replaced by domain enforcement and warning diagnosis.
- Preserve the distinction between an exact analytic MLE, a finite-grid
  approximation, and a tolerance-dependent optimizer result. Also preserve
  estimator versus observed estimate and uppercase random variables versus
  lowercase realizations.
- The source says character values need “parentheses”; it means quotation
  marks. It also says “interactively” where the numerical algorithm requires
  **iteratively**. Translate the intended meanings rather than those surface
  slips.
- `log` in the statistical R prose denotes the natural logarithm. Function
  names and frozen code strings remain untranslated even when explanatory
  prose is localized.

The twenty genuinely new stable decisions are encoded as
`O006-TERM-0065`–`O006-TERM-0084` in
`00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`. No Lesson 05 source, normalized
document, translation segment, build artifact, or other control was altered by
this terminology-only task.
