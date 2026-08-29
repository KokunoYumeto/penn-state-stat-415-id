# C5 contract — asesmen akhir dan capstone data terbuka

Status: in production, 2026-08-29

C5 menutup seluruh pekerjaan pembelajaran mandiri yang masih tersisa pada
pendamping orisinal O006/C140. Batasnya tepat lima dokumen baru berbahasa
`id-ID`: tiga asesmen kumulatif `CA02`–`CA04` dan dua capstone data terbuka
`CP01`–`CP02`. C1–C4, byte otoritas Penn State, donor *Random*, aset simulasi,
dan receipt historis tidak diubah kecuali ada cacat baru yang terbukti.

Semua prosa, masalah, solusi, rubrik, skrip analisis, dan lapisan editorial C5
adalah materi orisinal CC BY-SA 4.0 dengan provenans persis
`OpenAI Codex gpt-5.6-sol, Ultra`. Hak dataset tetap terpisah dan tidak pernah
disamakan dengan lisensi materi pendamping.

## Batas asesmen

Setiap asesmen bernilai 100 poin, mempunyai tepat sepuluh masalah bernilai
sepuluh poin, serta mematuhi kontrak metadata, dua petunjuk bertahap, jawaban
singkat, solusi lengkap, dan `RUB00` serta `RUB01`–`RUB10`. Setiap rubrik
menamai asumsi atau mekanisme kegagalan yang material. Jawaban numerik tanpa
derivasi tidak menerima kredit derivasi; keluaran perangkat lunak tidak boleh
menggantikan argumen matematika.

1. `CA02` menilai fondasi sampel-hingga yang belum diduplikasi oleh `CA01`:
   peluang bersyarat dan harapan; transformasi dan order statistics;
   endpoint/quantile; bias, varians, MSE, risk dan konsistensi; faktorisasi,
   minimal sufficiency, completeness, ancillary dan Basu; MoM dan MLE termasuk
   batas/nonexistence; informasi dan pivot; interval eksak, Wald, delta dan
   bootstrap; size, p-value, power, ukuran sampel dan inversi uji; lalu satu
   audit terpadu. Prasyarat dan relasi asesmennya adalah `MS00`–`MS06`.
2. `CA03` menilai model linear matriks: ruang kolom, proyeksi, rank dan
   estimability; pseudoinvers dan nilai suaian unik; OLS versus MLE;
   Gauss–Markov dan batas BLUE; hukum Gaussian eksak serta uji t; hipotesis
   linear umum, uji F dan ANOVA; interval mean versus prediksi serta inferensi
   simultan; leverage, penghapusan-satu dan Cook distance; omitted-variable
   bias, heteroskedastisitas/HC3 dan pascaseleksi; serta audit numerik `SIM005`.
   Prasyaratnya `D008`–`D011`, `SIM005`, dan `MS12`.
3. `CA04` menilai perbandingan Bayesian–frequentist: hukum bersama, prior,
   posterior, bukti marginal dan prediktif; pembaruan Normal dan Beta–binomial;
   tindakan Bayes di bawah loss kuadratik, absolut dan nol-satu diskret;
   frequentist risk, prior-predictive risk, Bayes risk dan batas admissibility;
   propriety prior improper; credible versus confidence dan cakupan
   parameter-tetap versus rata-prior; pemeriksaan prediktif versus p-value;
   keputusan Bayes versus kendala Neyman–Pearson; sensitivitas Bayes factor dan
   optional stopping; serta audit baru atas `SIM006`. Prasyaratnya `D012`,
   `D013`, `SIM006`, dan `MS11`.

`CA02` tidak mengulang bukti NP/UMP atau delta-method berturunan nol dari
`CA01`. `CA03` memisahkan geometri proyeksi dari konsekuensi inferensi F/ANOVA.
`CA04` menuntut perhitungan dan sintesis baru, bukan parafrasa tabel `SIM006`.

## Batas capstone

`CP01` adalah capstone regresi data terbuka setelah `CA02` dan `CA03`;
`CP02` adalah capstone perbandingan Bayesian–frequentist setelah `CA02` dan
`CA04`. Masing-masing berupa satu masalah koheren 100 poin dengan metadata,
sedikitnya dua petunjuk, jawaban ringkas, solusi lengkap, dan rubrik:
15 poin hak/provenans/identitas byte; 10 pertanyaan, populasi, estimand dan
loss; 10 ingestion/pembersihan deterministik; 20 derivasi dan analisis utama;
15 analisis ketidakpastian/pembanding; 15 diagnostik dan sensitivitas; 10
replay luring dan keluaran statis aksesibel; 5 kesimpulan terkalibrasi.

Dataset hanya boleh diterima setelah bukti primer tingkat-aset membolehkan
unduh, redistribusi dan analisis turunan. Prioritaskan public domain/CC0 atau
CC BY yang jelas; tolak ND, NC yang tidak kompatibel, syarat klik yang tidak
terbekukan, hak basis data yang tidak terselesaikan, pengenal langsung,
microdata sensitif, atau risiko reidentifikasi yang masuk akal. `CP01`
memerlukan respons kontinu dan sedikitnya dua kovariat terdokumentasi;
`CP02` memerlukan hitungan agregat sukses/percobaan menurut kelompok atau
waktu. Data agregat lebih disukai daripada microdata per orang.

Untuk setiap capstone, bekukan byte mentah, kamus/schema, bukti hak primer,
URL kanonis, penerbit, versi/tanggal dataset, waktu pengambilan, MIME/encoding,
ukuran dan SHA-256. Simpan di `data/capstones/CP01/` atau `CP02/` bersama
`RIGHTS_EVIDENCE`, `DATASET_PROVENANCE.json`, CSV bersih, skrip transformasi,
dan manifest baris/kolom. Build/check-only tidak pernah mengunduh data; seluruh
analisis, assertion, tabel, SVG/teks alternatif dan replay memakai byte lokal.

## Urutan, gate, dan kondisi terminal

Produksi berurutan adalah `CA02`, `CA03`, `CA04`, seleksi/freeze dataset
`CP01`, penulisan `CP01`, seleksi/freeze dataset `CP02`, lalu `CP02`. Setelah
setiap dokumen, jalankan audit matematika terbatas; setelah lima dokumen,
perluas build/QA agar menerima tipe `capstone`, empat asesmen total, dua
capstone, dataset/rights/provenans, dan rubrik 100 poin. Batas akhir yang
diharapkan adalah 39 dokumen sumber, 13 set penguasaan, empat asesmen, dua
capstone, enam simulasi, dan 146 masalah terselesaikan; hitung anchor, byte,
entitas dan relasi dari artefak, bukan dari perkiraan ini.

Gate akhir adalah build HTML/backend deterministik, replay transformasi data,
ID/referensi, matematika, struktur masalah/rubrik, hak, privasi, aksesibilitas,
aset dan manifest lulus tanpa jaringan atau browser. Larangan permanen tetap
berlaku: tidak ada Chrome, Chromium, Playwright, Puppeteer, Electron, WebView,
DAISY Ace, atau proses browser lain. Setelah gate lulus, publikasikan checkpoint
reader-first di lineage GitHub/Zenodo yang sama dan baca balik seluruh byte
publik secara anonim tanpa meminta konfirmasi. C5 selesai hanya bila semua lima
dokumen, data dan bukti haknya, backend/build/QA, kontrol hidup, publikasi, dan
readback lengkap; O006/C140 tetap aktif sampai komponen Penn, donor, dan
pendamping semuanya tidak mempunyai pekerjaan tersisa.
