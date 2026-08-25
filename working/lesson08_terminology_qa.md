# Lesson 08 terminology QA — asymptotic likelihood, bootstrap, and delta method

Checked: 2026-08-25

## Authority and bounded evidence

The census used the complete frozen instructional main in
`authority/upstream/stat415/Lesson08.html` (135,460 bytes; SHA-256
`7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`),
including all 156 math surfaces, 49 code nodes, 28 preformatted blocks, fixed R
outputs, four figures, the two code-tab templates, the Pareto example, and the
summary.

Existing component decisions remain controlling:

- `estimator` / `estimate` / `estimation` -> **penduga** / **nilai dugaan** /
  **pendugaan** (`O006-TERM-0018`–`0020`);
- `confidence interval` -> **selang kepercayaan** (`O006-TERM-0022`);
- `likelihood`, `maximum likelihood estimator`, `maximum likelihood estimate`,
  and `log-likelihood` -> **fungsi kemungkinan**, **penduga kemungkinan
  maksimum (MLE)**, **nilai dugaan kemungkinan maksimum**, and **fungsi
  log-kemungkinan** (`O006-TERM-0025`, `0058`–`0060`);
- `empirical distribution` -> **distribusi empiris** (`O006-TERM-0055`);
- `parameter-dependent support` -> **himpunan dukungan yang bergantung pada
  parameter** (`O006-TERM-0062`);
- `numerical optimization`, `objective function`, `convergence criterion`, and
  `function evaluation` -> **optimisasi numerik**, **fungsi objektif**,
  **kriteria konvergensi**, and **evaluasi fungsi** (`O006-TERM-0065`,
  `0072`, `0076`, `0075`);
- `variance`, `standard deviation`, `standard error`, and `quantile` ->
  **varians**, **simpangan baku**, **galat baku**, and **kuantil**
  (`O006-TERM-0036`, `0079`, `0021`, `0083`); and
- `confidence level` / `confidence bounds` -> **tingkat kepercayaan** /
  **batas selang kepercayaan** (`O006-TERM-0086`, `0092`).

A bounded exact-topic Indonesian check used three primary university/journal
sources, not a general web-frequency vote:

1. An Institut Teknologi Bandung mathematics thesis chapter,
   [`Teorema Limit Pusat dan Metode Delta`](https://digilib.itb.ac.id/assets/files/disk1/440/jbptitbpp-gdl-nizlaafria-21964-3-2013ta-2.pdf),
   uses **Metode Delta**, **penaksir asimtotik normal**, **distribusi
   probabilitas aproksimasi**, and an explicit convergence-in-distribution
   formula. This supports **metode delta**, while the component's existing
   **penduga** remains preferable to its attested variant *penaksir*.
2. The Universitas Islam Bandung statistics article
   [`Pendugaan Selang Kepercayaan Persentil Bootstrap Nonparametrik`](https://ejournal.unisba.ac.id/index.php/statistika/article/viewFile/1005/599)
   uses **selang kepercayaan bootstrap nonparametrik persentil**, **sampel
   bootstrap**, **nilai dugaan**, **batas bawah**, **batas atas**, and
   **perulangan**. It also distinguishes the resampled data from the resulting
   sequence of parameter estimates.
3. The Universitas Islam Bandung proceedings inventory includes the exact
   title
   [`Selang Kepercayaan Bootstrap Parametrik`](https://proceedings.unisba.ac.id/index.php/BCSS/issue/view/100),
   corroborating **bootstrap parametrik** alongside **bootstrap
   nonparametrik** in source 2.

The direct Indonesian sources vary between *penaksir* and *penduga* and
between *aproksimasi* and *hampiran*. The cumulative component glossary has
already chosen **penduga** and **hampiran**; Lesson08 must not alternate merely
because a documented variant exists.

## Stable reader decisions

- Use **bootstrap** unchanged as the method name. Use **bootstrap parametrik**
  and **bootstrap nonparametrik** for the two procedures.
- Use **sampel bootstrap** only for a resampled/simulated data set. Use **nilai
  dugaan bootstrap** for `hat(theta)^(m)` and **replikasi bootstrap** when the
  emphasis is one repeated statistic computation. Do not call every estimate
  a *sampel data*.
- Use **pengambilan sampel ulang (resampling)** at first occurrence and
  **pengambilan sampel ulang** thereafter. Translate `with replacement` as
  **dengan pengembalian**.
- Use **selang kepercayaan bootstrap persentil** for `percentile bootstrap
  confidence interval`; add **parametrik** or **nonparametrik** in the same
  order when the method must be distinguished.
- Use **distribusi asimtotik** and **normalitas asimtotik**. Render `->d` as
  **konvergen dalam distribusi**, not as equality or finite-sample exact
  distribution.
- Use **informasi Fisher harapan** for expected information and **informasi
  teramati** for observed information. Introduce **matriks Hessian (Hessian)**
  when needed, and never translate an observed NLL Hessian as expected Fisher
  information.
- Use **metode delta**. Translate `smooth/differentiable` as **mulus/dapat
  didiferensialkan** according to context. Do not use **dapat dibalik** as a
  delta-method requirement.
- Use **syarat keteraturan** for `regularity conditions`, with
  **syarat regularitas** allowed parenthetically once as a search alias.
- Use **transformasi parameter**, **fungsi transformasi**, and **turunan** for
  `parameter transformation`, `transformation function`, and `derivative`.
- Use **parameter bentuk** and **parameter lokasi** for Pareto `a` and `L`, and
  **distribusi Pareto** for the model. Preserve the support bracket
  `[L,infinity)`.
- Use **parameter derajat kebebasan** for the Student-t `df`; preserve the
  executable identifier `df` and `df.hat` inside code.
- Use **benih pembangkit bilangan acak** in explanatory prose. Preserve the R
  identifiers `set.seed`, `RNGversion`, and `.Random.seed` exactly.
- Use **diagnostik konvergensi**, **kendala parameter**, **batas bawah**, and
  **batas atas** in executable-method notes.
- Use **ekor kanan panjang** for the visible long right tail in Figures 8.2–8.4;
  do not translate it as a right-tailed hypothesis test.

## Candidate glossary additions — not allocated in this task

The shared glossary remains unchanged. The production controller may allocate
non-overlapping IDs after `O006-TERM-0094` for the following high-value entries:

| en-US | Proposed id-ID | Decision |
|---|---|---|
| bootstrap | bootstrap | method name retained |
| parametric bootstrap | bootstrap parametrik | fitted parametric family |
| nonparametric bootstrap | bootstrap nonparametrik | empirical resampling |
| bootstrap sample | sampel bootstrap | resampled/simulated data set |
| bootstrap replicate | replikasi bootstrap | one repeated statistic result |
| percentile bootstrap confidence interval | selang kepercayaan bootstrap persentil | empirical endpoint quantiles |
| resampling | pengambilan sampel ulang (resampling) | introduce English alias once |
| sampling with replacement | pengambilan sampel dengan pengembalian | index-resampling rule |
| asymptotic distribution | distribusi asimtotik | limiting distribution |
| Fisher information | informasi Fisher | qualify expected/observed |
| observed information | informasi teramati | negative observed log-likelihood Hessian |
| delta method | metode delta | transformation limit theorem |
| regularity conditions | syarat keteraturan | `syarat regularitas` search alias |
| shape parameter | parameter bentuk | Pareto `a` |
| location parameter | parameter lokasi | Pareto endpoint `L` |

These are candidates, not admitted rows, and this QA file is not authority for
term IDs.

## Mandatory translation clarifications

- Correct the source notation: `theta` is the parameter, `hat(theta)` is its
  estimator/realized estimate by context, and `hat(theta)^(m)` is the `m`th
  bootstrap estimate. Preserve `M` versus `m` versus `n`.
- Correct the empirical PMF to count duplicate multiplicity.
- Repair the malformed brace in the percentile interval without altering its
  fragment boundary or empirical-quantile meaning.
- Distinguish expected Fisher information, observed information, and the
  numerical NLL Hessian returned by `optim`.
- State asymptotic results with convergence/approximation language and the
  applicable assumptions. Do not silently turn a plug-in variance into the
  exact variance of a finite-sample Normal law.
- State differentiability, not invertibility, for the first-order delta method.
- Do not repeat “bootstrap has no restrictions.” Say it avoids an inverse
  transformation and can handle many functions, while inferential validity
  remains method- and statistic-dependent.
- In the Pareto example, use `[L,infinity)` and explicitly flag the ordinary
  nonparametric percentile interval for `L` as invalid. Do not present
  `(5.06,5.28)` as a valid 95% confidence interval.
- Preserve executable R identifiers, capitalization, dots, and dollar signs.
  Translate comments only in a later correction/code-localization layer that
  can rerun and bind the result.
- Do not normalize the three prose interval pairs to either stale set of
  numbers until a seeded execution is selected and its entire output chain is
  regenerated.
- Supply full Indonesian figure alternatives; the source alts are not adequate
  translation targets.

## Translation allocation recommendation

The normalized lesson contains 291 segments,
`O006-PSU-009-S0001`–`O006-PSU-009-S0291`. The first non-overlapping tranche
should be `O006-PSU-009-S0001`–`O006-PSU-009-S0060`; subsequent 60-segment
tranches end at `S0120`, `S0180`, and `S0240`, with a final 51-segment tranche
`S0241`–`S0291`.
