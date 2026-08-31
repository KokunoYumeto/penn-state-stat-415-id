---
{"id":"O006-C140-CMP-INDEX","type":"index","title":"Pendamping Orisinal Statistika Matematis","locale":"id-ID","license":"CC-BY-SA-4.0","provenance":"OpenAI Codex gpt-5.6-sol, Ultra","prerequisites":["B40","B90","B95","C10"],"objectives":["Menutup ketelitian teori, simulasi, regresi matriks, dan penguasaan C140"],"relations":[{"predicate":"supplements","target":"O006-PSU-000"},{"predicate":"uses-donor","target":"O006-016-00-0001"}],"status":"complete"}
---

<a id="O006-C140-CMP-INDEX-SEC001"></a>
# Pendamping Orisinal Statistika Matematis

Komponen ini melengkapi alur utama Penn State STAT 415 serta sumber pelengkap
*Random* tentang statistik cukup dan lengkap. Materinya orisinal, berlisensi
CC BY-SA 4.0, dan tidak
dinisbatkan kepada kedua sumber eksternal tersebut.
Referensi eksternal `O006-PSU-000` dan `O006-016-00-0001` dipertahankan sebagai
relasi eksternal dan dipetakan dalam katalog serta lapisan mesin komponen.

Tahap pertama menghubungkan Pelajaran 07–10 dengan teori fungsi kemungkinan reguler
yang dirumuskan secara eksplisit, contoh nonreguler, teori uji optimal,
risiko dan efisiensi, simulasi yang dapat direproduksi, paket latihan penguasaan
lengkap, serta asesmen kumulatif.

Tahap kedua memperluas Pelajaran 12 menjadi model linear Gaussian dengan
desain tetap dalam notasi matriks. Komponen ini memisahkan geometri OLS,
teorema Gauss–Markov, fungsi kemungkinan Gaussian, inferensi eksak, dan diagnostik
berdasarkan asumsi yang tepat. Hasil tersebut kemudian diuji melalui simulasi
dengan benih acak tetap dan satu paket latihan penguasaan lengkap.

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

Semua laboratorium menggunakan benih acak yang dinyatakan secara eksplisit,
lingkungan komputasi terkunci, keluaran CSV dan SVG statis, serta pemeriksaan numerik. Tidak ada lingkungan
eksekusi yang bergantung pada jaringan atau peramban.

<a id="O006-C140-CMP-INDEX-SEC004"></a>
## Latihan penguasaan dan asesmen

- [ref:O006-C140-CMP-MS00] mendiagnosis probabilitas, distribusi, dan
  ekspektasi yang diperlukan sebelum inferensi;
- [ref:O006-C140-CMP-MS01] menurunkan distribusi statistik urutan serta
  melakukan inferensi kuantil;
- [ref:O006-C140-CMP-MS02] menguji bias, MSE, dan sifat penduga;
- [ref:O006-C140-CMP-MS03] menguji kecukupan, faktorisasi, dan kelengkapan;
- [ref:O006-C140-CMP-MS04] menguji metode momen dan fungsi kemungkinan;
- [ref:O006-C140-CMP-MS05] menguji informasi Fisher, selang, bootstrap, dan
  metode delta;
- [ref:O006-C140-CMP-MS06] menguji prosedur eksak, daya uji, nilai-p, dan
  hubungan antara prosedur Wald, skor, dan rasio fungsi kemungkinan;
- [ref:O006-C140-CMP-MS07]
- [ref:O006-C140-CMP-MS08]
- [ref:O006-C140-CMP-MS09]
- [ref:O006-C140-CMP-MS10]
- [ref:O006-C140-CMP-CA01]

Setiap masalah memiliki prasyarat, tujuan, tingkat kesulitan, label miskonsepsi,
petunjuk bertahap, jawaban singkat, dan solusi lengkap. C1 menandai tonggak
pemeriksaan substantif, bukan akhir pendamping. C2 melengkapi model linear
matriks, sedangkan C3 melengkapi perbandingan Bayesian–frekuentis. C4 dan C5
kemudian melengkapi seluruh paket latihan penguasaan, asesmen, dan proyek akhir
dalam cakupan final pendamping.

<a id="O006-C140-CMP-INDEX-SEC005"></a>
## Model linear matriks C2

1. [ref:O006-C140-CMP-D008] — ruang kolom, proyeksi, peringkat, dan keterestimasi;
2. [ref:O006-C140-CMP-D009] — OLS, MLE Gaussian, dan Gauss–Markov;
3. [ref:O006-C140-CMP-D010] — hukum eksak, uji t/F, ANOVA, selang, dan prediksi;
4. [ref:O006-C140-CMP-D011] — sisaan, leverage, pengaruh, salah spesifikasi,
   heteroskedastisitas, dan batas inferensi pascaseleksi.

<a id="O006-C140-CMP-INDEX-SEC006"></a>
## Laboratorium dan penguasaan C2

- [ref:O006-C140-CMP-SIM005] menguji cakupan Gaussian eksak, kegagalan galat
  baku klasik di bawah heteroskedastisitas, perbaikan HC3, dan pengaruh titik
  dengan leverage tinggi.
- [ref:O006-C140-CMP-MS12] menyediakan delapan masalah tak sepele dengan
  petunjuk bertahap, jawaban singkat, dan solusi lengkap.

C2 menuntaskan cakupan regresi matriks yang ditetapkan untuk pendamping. Pada
tonggak pemeriksaan C2, perbandingan Bayesian–frekuentis masih belum lengkap;
bagian C3 di bawah melengkapinya. C2 kini menjadi bagian dari cakupan final
pendamping.

<a id="O006-C140-CMP-INDEX-SEC007"></a>
## Pemutakhiran, keputusan, dan kalibrasi C3

1. [ref:O006-C140-CMP-D012] membangun distribusi posterior dan prediktif
   berdasarkan distribusi gabungan, lalu mengaitkan tindakan, kerugian, risiko
   frekuentis, dan risiko Bayes dengan syarat yang dinyatakan secara tepat bagi
   prior ternormalisasi maupun tak ternormalisasi.
2. [ref:O006-C140-CMP-D013] membandingkan selang kredibel dengan selang
   kepercayaan, keputusan Bayesian dengan taraf dan daya uji, faktor Bayes
   dengan pengujian hipotesis, serta pemeriksaan prediktif posterior dengan
   nilai-p tanpa menyamakan jaminannya.
3. [ref:O006-C140-CMP-SIM006] membedakan cakupan pada parameter tetap dari
   kalibrasi rataan terhadap prior dalam eksperimen beta–binomial
   deterministik.
4. [ref:O006-C140-CMP-MS11] menguji derivasi, keputusan, sensitivitas prior,
   penghentian opsional, dan interpretasi hasil kalibrasi melalui delapan masalah
   dengan solusi lengkap.

C3 menuntaskan cakupan teori perbandingan Bayesian–frekuentis yang ditetapkan
untuk pendamping. C4 dan C5 selanjutnya melengkapi paket latihan penguasaan,
asesmen kumulatif, dan proyek akhir; seluruhnya kini terintegrasi dalam cakupan
final.

Paket latihan penguasaan `MS00`–`MS06` membentuk kelompok C4 untuk melengkapi latihan mandiri.
Kelompok ini tidak mengubah teks Penn State;
masing-masing dokumen adalah karya pendamping orisinal yang memuat delapan soal
beserta solusi lengkap dan ID lapisan mesin yang dapat digunakan lintas bahasa.

<a id="O006-C140-CMP-INDEX-C5"></a>
## C5 — asesmen kumulatif dan proyek akhir data terbuka

C5 melengkapi jalur evaluasi pendamping dengan tiga asesmen kumulatif baru dan dua
proyek akhir data terbuka. Bersama [ref:O006-C140-CMP-CA01], rangkaian ini
mencakup empat asesmen kumulatif, dari [ref:O006-C140-CMP-CA01] sampai
[ref:O006-C140-CMP-CA04], serta dua proyek akhir,
[ref:O006-C140-CMP-CP01] dan [ref:O006-C140-CMP-CP02].

Setelah C5 selesai, pendamping ini mencakup 39 dokumen: 13 teori, 6
laboratorium simulasi, 13 paket latihan penguasaan, 4 asesmen kumulatif, 2 proyek akhir, dan
indeks ini. Kelima dokumen C5 (`CA02`–`CA04`, `CP01`, dan `CP02`) kini berstatus
`complete`. Urutan pembacaannya adalah:

1. [ref:O006-C140-CMP-CA02] — asesmen kumulatif fondasi inferensi
   sampel berhingga;
2. [ref:O006-C140-CMP-CA03] — asesmen kumulatif model linear dalam bentuk
   matriks;
3. [ref:O006-C140-CMP-CA04] — asesmen kumulatif perbandingan Bayesian dan
   frekuentis;
4. [ref:O006-C140-CMP-CP01] — proyek akhir regresi berbasis data terbuka;
5. [ref:O006-C140-CMP-CP02] — proyek akhir perbandingan Bayesian–frekuentis pada
   hitungan agregat terbuka.

Setiap proyek akhir mengaitkan analisis dengan aset, versi, skema, provenans, dan
identitas byte yang tercatat. Hak dan lisensi kumpulan data tetap mengikuti bukti
pada tingkat asetnya sendiri; lisensi materi pendamping tidak melisensikan
ulang data sumber.

Pembaca C5 menyajikan HTML, tabel, SVG, dan teks alternatif yang telah dibangun.
Seluruh tahap—penyiapan masukan, analisis, pembangunan, dan pemutaran ulang—hanya
menggunakan byte lokal yang telah dibekukan. Prosesnya berjalan secara deterministik
dan luring serta tidak memerlukan jaringan, peramban, atau proses peramban.

Bagian ini menandai tonggak akhir C5. Tonggak tersebut tercapai setelah
[ref:O006-C140-CMP-CA02], [ref:O006-C140-CMP-CA03],
[ref:O006-C140-CMP-CA04], [ref:O006-C140-CMP-CP01], dan
[ref:O006-C140-CMP-CP02] terintegrasi, data serta bukti hak dan lisensi kedua
proyek akhir ditautkan secara eksplisit, serta pembangunan, manifes,
aksesibilitas, dan pemutaran ulang luring seluruh keluaran
lulus secara deterministik. Setelah pemeriksaan tersebut lulus, tidak ada asesmen atau
proyek akhir C5 tambahan di luar empat asesmen kumulatif dan dua proyek akhir tersebut.
