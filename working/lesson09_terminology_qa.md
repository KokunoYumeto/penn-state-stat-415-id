# Lesson 09 terminology QA — hypothesis tests

Checked: 2026-08-25

## Authority and bounded evidence

The census covers the complete frozen instructional main in
`authority/upstream/stat415/Lesson09.html` (114,901 bytes; SHA-256
`87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319`),
including all 219 math surfaces, five definitions, seven examples, nine
solutions, three tables, and ten image contexts.

The shared component glossary was read but not changed. Its controlling entries
include:

- `hypothesis testing` -> **pengujian hipotesis** (`O006-TERM-0024`);
- `standard error` -> **galat baku** (`O006-TERM-0021`);
- `Central Limit Theorem` -> **Teorema Limit Pusat** (`O006-TERM-0027`);
- `degrees of freedom` -> **derajat kebebasan** (`O006-TERM-0028`);
- `critical value` -> **nilai kritis** (`O006-TERM-0091`); and
- `confidence level` -> **tingkat kepercayaan** (`O006-TERM-0086`), which must
  remain distinct from significance level.

A bounded exact-topic check used four Indonesian university sources:

1. [UGM Menara Ilmu Metode Statistika — Inferensi Statistik](https://metstat.mipa.ugm.ac.id/teori/inferensi-statistik/)
   uses **uji hipotesis**, **hipotesis alternatif**, **kesalahan tipe I**,
   **daerah penolakan (daerah kritik)**, **tingkat signifikansi**, and
   **statistik penguji/statistik uji**.
2. [Universitas Indonesia — Metode-Metode Pengujian untuk Hipotesis](https://lib.ui.ac.id/file?file=digital%2Fold23%2F20181982-030-09-Metode-Metode+pengujian.pdf)
   defines **daerah kritis**, **power function/power pengujian**, **tingkat
   signifikansi**, and **nilai probabilitas (p-value)** in mathematical-testing
   context.
3. [IPB Xplore Journal of Statistics, Vol. 11 No. 3](https://journal-stats.ipb.ac.id/index.php/xplore/article/download/1018/398/3706)
   uses **statistik uji**, **taraf nyata**, **penolakan H0**, and **kuasa uji**,
   explicitly defining power as the probability of rejecting a false null.
4. [Universitas Multimedia Nusantara thesis chapter](https://kc.umn.ac.id/id/eprint/40366/4/BAB_III.pdf)
   states the p-value event as a statistic **yang sama ekstremnya, atau lebih
   ekstrem** than observed under the null. This directly supports the equality
   correction required for Lesson 09.

These sources document genuine variants. Reader consistency and mathematical
precision, not majority counting, control the decisions below.

## Stable reader decisions

| en-US | id-ID decision | Note |
|---|---|---|
| hypothesis test | uji hipotesis | Procedure; use **pengujian hipotesis** for the process/framework. |
| null hypothesis | hipotesis nol | Preserve `H_0`. |
| alternative hypothesis | hipotesis alternatif | Preserve `H_a`/`H_1`; **hipotesis tandingan** is an attested alias, not the reader default. |
| significance level | tingkat signifikansi | Keep distinct from **tingkat kepercayaan**; **taraf nyata/taraf signifikansi** are attested variants. |
| test statistic | statistik uji | **Statistik penguji** is attested, but do not alternate inside the lesson. |
| rejection region / critical region | daerah penolakan (daerah kritis) | Introduce the parenthetical alias once; do not use *daerah penerimaan* to imply accepting `H_0`. |
| critical value | nilai kritis | Existing `O006-TERM-0091`. |
| reject the null hypothesis | menolak hipotesis nol | Decision language, not proof that `H_a` is certainly true. |
| fail to reject the null hypothesis | gagal menolak hipotesis nol | Never translate as **menerima hipotesis nol**. |
| Type I error | galat tipe I | **Kesalahan tipe I** is attested; component preference keeps `galat` aligned with **galat baku** and MSE terminology. |
| Type II error | galat tipe II | Always state the conditioning alternative/value where needed. |
| p-value | nilai-p | Use a hyphen and lowercase `p` in prose; preserve executable/source notation exactly in protected math. |
| power / power of a test | kuasa uji | Write `kuasa uji pada theta` when parameter dependence matters. |
| one-tailed test | uji satu sisi | Add **ekor kanan** or **ekor kiri** for the distribution tail. |
| two-tailed test | uji dua sisi | The two rejection tails each receive the stated alpha allocation. |
| right-/left-tailed test | uji sisi kanan / uji sisi kiri | In figure prose, **ekor kanan/kiri** describes the shaded tail itself. |
| at least as extreme | sekurang-kurangnya sama ekstrem | Mandatory in the p-value definition; do not translate as merely **lebih ekstrem**. |
| size of a test | ukuran uji | Explain as the null rejection probability; do not confuse with sample size. |
| randomized test | uji teracak | On first use, explain the probability of rejection at the boundary equality set. |
| equality set | himpunan kesamaan | Here: outcomes exactly on the critical boundary. |

No new shared-glossary rows were admitted in this bounded lane. The production
controller may later allocate non-overlapping IDs for the new decisions above;
this file does not mutate the shared glossary.

## Formula and decision-language rules

- Preserve the distinction among the random statistic `Z` or `T`, its observed
  value `z` or `t`, a fixed **nilai kritis**, and a **daerah penolakan**.
- Translate `P(Type I error)=alpha` with its condition visible in nearby prose:
  the probability of rejecting `H_0` **when `H_0` is true**.
- Translate `beta` and power as functions of the specified true alternative
  when the alternative is composite.
- Use **hampiran normal** for the one-proportion cutoff/size and for any mean
  calculation justified only asymptotically. Reserve **eksak** for the stated
  iid sampling model.
- If exact Binomial size 0.05 is claimed, state the randomized decision at
  `Y=273`; otherwise call the source calculation approximate.
- For the p-value, write **peluang memperoleh statistik uji yang
  sekurang-kurangnya sama ekstrem dengan yang diamati, dengan menganggap
  hipotesis nol benar**.
- Use **bukti yang cukup untuk mendukung hipotesis alternatif**, not a claim
  that rejection proves the alternative true.
- For two-sided tests, name both tails and keep the equality signs consistent
  with the declared p-value/critical-region convention.
- Define t critical-value subscripts by upper- or lower-tail probability before
  attaching a sign; never assign one symbol both `+1.9842` and `-1.9842`.

## Accessibility terminology

- Use **teks alternatif** for `alt text`, **keterangan gambar** for a substantive
  caption, and **tajuk baris/tajuk kolom** for semantic table headers.
- Alternative text must state the curve/distribution, center, cutoff(s), shaded
  probability, and tail/decision meaning without depending on red/blue color.
- Describe the two `Lesson09_files/figure-html/` images as **keluaran plot yang
  dibekukan**. Because code and inputs are absent, do not call them plots that
  readers can reproduce from the lesson source.
