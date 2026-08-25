# Lesson 04 terminology QA — Indonesian mathematical statistics

Checked: 2026-08-25

## Authority and bounded census

The terminology census used the frozen official Penn State authority
`authority/upstream/stat415/Lesson04.html` (106,614 bytes; SHA-256
`9fe5790e577c6ce0b808c92683aea45442187f80f74d540b20bd4514bdefc060`).
The complete reader-facing body under `main#quarto-document-content` contains
about 5,311 English word-like tokens. Exact case-insensitive phrase matches in
that body establish the recurring vocabulary pressure:

- `likelihood function(s)`: 32;
- `log-likelihood` or `loglikelihood`: 15;
- `maximum likelihood estimator(s)`: 16;
- `maximum likelihood estimate(s)`: 15;
- `indicator function(s)`: 11;
- `support`: 8;
- single-/one-parameter wording: 9;
- multiparameter/multiple-parameter wording: 3;
- `critical point(s)`: 6;
- `second derivative`: 5; and
- `natural logarithm`: 3.

These are literal phrase counts, not counts of independent semantic units.
The inspection also covered every numbered section (4.1–4.5), all sixteen
examples and their solution surfaces, the three definitions, objectives, and
summary.

## Continuity and Indonesian field evidence

The existing glossary decisions remain controlling: `fungsi kemungkinan` for
likelihood, `penduga` versus realized `nilai dugaan`, `pendugaan` for the
process, `himpunan dukungan`, `ruang parameter`, `statistik urutan`, and
`fungsi kepadatan/massa peluang`. Lesson 02 already uses **model berparameter
tunggal**, while Lesson 03 already uses **penduga kemungkinan maksimum**.

The new choices are also supported by representative Indonesian academic
usage:

1. IPB University materials use **Penduga Kemungkinan Maksimum** and
   **metode kemungkinan maksimum**, including the official repository record
   `https://repository.ipb.ac.id/handle/123456789/73091` and the Statistics and
   Data Sciences curriculum surface
   `https://panduansupport.ipb.ac.id/ProgramStudi/Kurikulum/Detail/S2/1047`.
2. Indonesian statistics journals attest **fungsi log-kemungkinan**, including
   *Forum Statistika dan Komputasi* at
   `https://journal.ipb.ac.id/statistika/article/download/4919/3351` and
   *Statistika* at
   `https://ejournal.unisba.ac.id/index.php/statistika/article/download/993/587`.
   The unhyphenated **fungsi log kemungkinan** is also attested, for example in
   the official IPB repository record
   `https://repository.ipb.ac.id/handle/123456789/92357?show=full`.
3. The UGM repository record
   `https://etd.repository.ugm.ac.id/penelitian/detail/39103` uses **fungsi
   indikator** in a statistical survival-model context.

## Decisions and rejected variants

- Preserve the mathematical distinction between **penduga kemungkinan
  maksimum (MLE)**, a statistic, and **nilai dugaan kemungkinan maksimum**, its
  realized value. The source repeatedly alternates between *estimator* and
  *estimate*; translating both as `estimasi` would erase that distinction.
  `PKM` is a documented Indonesian abbreviation, but this component retains
  `MLE` because it is the source's notation and already appears throughout the
  course.
- Use **fungsi log-kemungkinan** for `log-likelihood function`, with
  `log-likelihood` optionally supplied parenthetically on first use. The mixed
  form `fungsi log-likelihood` is rejected because `likelihood` already has the
  stable component term `kemungkinan`. The unhyphenated **fungsi log
  kemungkinan** remains a documented orthographic variant, not a different
  concept.
- Use **fungsi indikator** for `indicator function`. Preserve
  `\(\mathbf{1}_A\)` and its event subscript; `fungsi petunjuk` is rejected as
  an unnecessary literal alternative.
- The source's phrases “support parameters” and “the parameter is in the
  support” are imprecise. The intended condition is that the distribution's
  **himpunan dukungan bergantung pada parameter**, or that the parameter
  determines a boundary of that support. Do not coin `parameter dukungan` or
  say that the parameter itself belongs to the sample-space support.
- Continue **model berparameter tunggal** for `single-parameter model`. Use
  **model multiparameter**, or the explanatory **model dengan lebih dari satu
  parameter**, when the number of unknown parameters is unrestricted.
  `Model berparameter ganda` is rejected in that general setting because it
  can imply exactly two parameters.
- The recurring calculus and linear-algebra terms remain transparent
  compositions rather than new stable glossary entities: **titik kritis**,
  **turunan pertama**, **turunan kedua**, **uji turunan kedua**, **logaritma
  natural**, **monoton naik**, **monoton turun**, **solusi analitik**, **solusi
  numerik**, **skalar**, **vektor**, and **median**.

The seven genuinely new stable decisions are encoded as
`O006-TERM-0058`–`O006-TERM-0064` in
`00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`. No Lesson 04 source or translation
segment was altered by this terminology-only task.
