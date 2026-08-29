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

- [ref:O006-C140-CMP-MS00] mendiagnosis probabilitas, distribusi, dan
  ekspektasi yang diperlukan sebelum inferensi;
- [ref:O006-C140-CMP-MS01] menurunkan distribusi statistik urutan dan
  inferensi kuantil;
- [ref:O006-C140-CMP-MS02] menguji bias, MSE, dan sifat estimator;
- [ref:O006-C140-CMP-MS03] menguji kecukupan, faktorisasi, dan kelengkapan;
- [ref:O006-C140-CMP-MS04] menguji method of moments dan likelihood;
- [ref:O006-C140-CMP-MS05] menguji informasi Fisher, interval, bootstrap, dan
  delta method;
- [ref:O006-C140-CMP-MS06] menguji pengujian eksak, power, *p*-value, dan
  jembatan Wald/score/LR;
- [ref:O006-C140-CMP-MS07]
- [ref:O006-C140-CMP-MS08]
- [ref:O006-C140-CMP-MS09]
- [ref:O006-C140-CMP-MS10]
- [ref:O006-C140-CMP-CA01]

Setiap masalah memiliki prasyarat, tujuan, tingkat kesulitan, tag miskonsepsi,
petunjuk bertahap, jawaban singkat, dan solusi lengkap. C1 adalah checkpoint
substansial, bukan akhir pendamping. C2 di bawah menutup model linear matriks;
pada checkpoint historis itu perbandingan Bayesian–frequentist masih terbuka.
C3 di bawah sekarang menutup perbandingan tersebut; set penguasaan serta
asesmen sisanya dan dua capstone masih mengikuti urutan pada kontrol hidup.

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

C2 menutup batas regresi matriks yang ditetapkan untuk pendamping. Pada akhir
checkpoint C2, perbandingan Bayesian–frequentist masih terbuka; bagian C3 di
bawah menutupnya. Pendamping tetap berstatus produksi sampai set penguasaan
yang tersisa, tiga asesmen kumulatif, dan dua capstone selesai.

<a id="O006-C140-CMP-INDEX-SEC007"></a>
## Pembaruan, keputusan, dan kalibrasi C3

1. [ref:O006-C140-CMP-D012] membangun posterior dan prediktif dari hukum
   bersama, lalu menghubungkan tindakan, loss, risk frequentist, dan risk
   Bayes dengan syarat prior proper atau improper yang dinyatakan tepat.
2. [ref:O006-C140-CMP-D013] membandingkan interval credible dengan confidence,
   keputusan Bayesian dengan size/power, Bayes factor dengan uji, serta
   pemeriksaan prediktif posterior dengan *p*-value tanpa menyamakan jaminannya.
3. [ref:O006-C140-CMP-SIM006] memisahkan cakupan pada parameter tetap dari
   kalibrasi rata-rata-prior pada eksperimen beta–binomial deterministik.
4. [ref:O006-C140-CMP-MS11] menguji derivasi, keputusan, sensitivitas prior,
   optional stopping, dan interpretasi hasil kalibrasi melalui delapan masalah
   dengan solusi penuh.

C3 menutup batas teori perbandingan Bayesian–frequentist yang ditetapkan untuk
pendamping, tetapi bukan keseluruhan C140. Set penguasaan, asesmen kumulatif,
dan capstone yang belum dijadwalkan tetap mengikuti kontrol hidup.

Set penguasaan `MS00`–`MS06` membentuk batch C4 untuk menutup latihan mandiri
yang sebelumnya belum tersedia. Batch ini tidak mengubah teks Penn State;
masing-masing dokumen adalah karya pendamping orisinal dengan delapan soal
bersolusi penuh dan ID backend yang dapat dipindahkan lintas bahasa.
