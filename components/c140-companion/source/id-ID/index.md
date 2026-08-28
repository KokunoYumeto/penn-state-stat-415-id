---
{"id":"O006-C140-CMP-INDEX","type":"index","title":"Pendamping Orisinal Statistika Matematis","locale":"id-ID","license":"CC-BY-SA-4.0","provenance":"OpenAI Codex gpt-5.6-sol, Ultra","prerequisites":["B40","B90","B95","C10"],"objectives":["Menutup rigor, simulasi, regresi matriks, dan mastery C140"],"relations":[{"predicate":"supplements","target":"O006-PSU-000"},{"predicate":"uses-donor","target":"O006-016-00-0001"}],"status":"in-production"}
---

<a id="O006-C140-CMP-INDEX-SEC001"></a>
# Pendamping Orisinal Statistika Matematis

Komponen ini melengkapi spine Penn State STAT 415 dan donor kelengkapan
*Random*. Materinya orisinal, berlisensi CC BY-SA 4.0, dan tidak dinisbatkan
kepada kedua sumber eksternal tersebut.

Batch pertama menghubungkan Pelajaran 07–10 ke teori likelihood reguler yang
eksplisit, contoh nonreguler, teori uji optimal, risiko/efisiensi, simulasi
reproduktif, set penguasaan lengkap, dan asesmen kumulatif.

Batch kedua mengembangkan Pelajaran 12 menjadi model linear Gaussian desain
tetap dalam bentuk matriks. Ia memisahkan geometri OLS, teorema Gauss–Markov,
likelihood Gaussian, inferensi eksak, dan diagnostik menurut asumsi yang benar,
lalu mengujinya melalui simulasi seeded dan satu set penguasaan lengkap.

<a id="O006-C140-CMP-INDEX-SEC002"></a>
## Urutan teori C1

1. [ref:O006-C140-CMP-D001]
2. [ref:O006-C140-CMP-D002]
3. [ref:O006-C140-CMP-D003]
4. [ref:O006-C140-CMP-D004]
5. [ref:O006-C140-CMP-D005]
6. [ref:O006-C140-CMP-D006]
7. [ref:O006-C140-CMP-D007]

<a id="O006-C140-CMP-INDEX-SEC003"></a>
## Laboratorium simulasi C1

- [ref:O006-C140-CMP-SIM001]
- [ref:O006-C140-CMP-SIM002]
- [ref:O006-C140-CMP-SIM003]
- [ref:O006-C140-CMP-SIM004]

Semua laboratorium memakai seed eksplisit, lingkungan terkunci, output CSV dan
SVG statis, serta assertion numerik. Tidak ada runtime jaringan atau browser.

<a id="O006-C140-CMP-INDEX-SEC004"></a>
## Latihan penguasaan dan asesmen

- [ref:O006-C140-CMP-MS07]
- [ref:O006-C140-CMP-MS08]
- [ref:O006-C140-CMP-MS09]
- [ref:O006-C140-CMP-MS10]
- [ref:O006-C140-CMP-CA01]

Setiap masalah memiliki prasyarat, tujuan, tingkat kesulitan, tag miskonsepsi,
petunjuk bertahap, jawaban singkat, dan solusi lengkap. C1 adalah checkpoint
substansial, bukan akhir pendamping. C2 di bawah menutup model linear matriks;
perbandingan Bayesian–frequentist, set penguasaan serta asesmen sisanya, dan dua
capstone masih mengikuti urutan pada kontrol hidup.

<a id="O006-C140-CMP-INDEX-SEC005"></a>
## Model linear matriks C2

1. [ref:O006-C140-CMP-D008] — ruang kolom, proyeksi, rank, dan keterestimasi;
2. [ref:O006-C140-CMP-D009] — OLS, MLE Gaussian, dan Gauss–Markov;
3. [ref:O006-C140-CMP-D010] — hukum eksak, uji t/F, ANOVA, interval, dan prediksi;
4. [ref:O006-C140-CMP-D011] — residual, leverage, pengaruh, misspesifikasi,
   heteroskedastisitas, dan batas inferensi pascaseleksi.

<a id="O006-C140-CMP-INDEX-SEC006"></a>
## Laboratorium dan penguasaan C2

- [ref:O006-C140-CMP-SIM005] menguji coverage Gaussian eksak, kegagalan galat
  baku klasik di bawah heteroskedastisitas, perbaikan HC3, dan pengaruh titik
  ber-leverage tinggi.
- [ref:O006-C140-CMP-MS12] menyediakan delapan masalah nontrivial dengan
  petunjuk bertahap, jawaban singkat, dan solusi penuh.

C2 menutup batas regresi matriks yang ditetapkan untuk pendamping. Pendamping
tetap berstatus produksi sampai perbandingan Bayesian–frequentist, set
penguasaan yang tersisa, empat asesmen kumulatif, dan dua capstone selesai.
