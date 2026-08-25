# Lesson 02 terminology QA — Indonesian mathematical statistics

Checked: 2026-08-24

## Evidence inspected

1. Octafinnanda Ummu Fairuzdhiya, Rita Rahmawati, and Agus Rusgiyono,
   “Analisis Faktor-Faktor yang Mempengaruhi Kemiskinan di Jawa Tengah
   Menggunakan Model Galat Spasial,” *Jurnal Gaussian* 3(4), 2014, pp. 781–790,
   official Universitas Diponegoro PDF:
   `https://ejournal3.undip.ac.id/index.php/gaussian/article/download/8089/7869`.
   Page 2 uses **Rataan Kuadrat Galat** (RKG) and the paper also uses
   **penduga**, **rataan**, **varians/varian**, **galat**, and **uji Wald** in
   statistical context.
2. Nurhasanah, “Perbandingan Regresi Komponen Utama Terkoreksi dengan Regresi
   Ridge dalam Mengatasi Multikolinearitas,” IPB University Scientific
   Repository, 2006:
   `https://repository.ipb.ac.id/handle/123456789/9918`.
   The abstract uses **kuadrat tengah galat (mean square error—MSE)**,
   **ragam penduga**, **dugaan parameter**, and **bias**.
3. The exact-topic evidence already retained for Lesson 01 continues to support
   the glossary choices **peubah acak**, **sampel acak**, **nilai harapan**,
   **rataan**, **penduga**, and **pendugaan**.

## Decision

- Use **rataan kuadrat galat (MSE)** for the estimator criterion in Lesson 02.
  This is mathematically transparent—an expectation/rataan of squared
  estimation error—and directly attested by an Indonesian statistics journal.
  **Kuadrat tengah galat** remains a documented field variant, especially in
  regression/ANOVA and IPB usage, but mixing the two within one lesson would
  reduce consistency.
- Keep the established distinctions **penduga** (random statistic) versus
  **nilai dugaan** (realized estimate), and **nilai harapan** (expectation)
  versus **rataan** (mean). When the English source uses *estimate* loosely for
  a property that belongs to an estimator, the Indonesian prose uses the
  mathematically precise **penduga** and records the clarification.
- Use **varians** rather than alternating with **ragam** in this component.
  Both occur in Indonesian field writing, but `varians` is already the
  component convention and matches preceding lessons.

The resulting additions are recorded as stable terms
`O006-TERM-0031`–`O006-TERM-0041` in
`00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`.
