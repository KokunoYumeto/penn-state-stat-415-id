# Tujuan dan alur kerja tahan-kompaksi — pendamping orisinal O006/C140

## Tujuan, otoritas, dan batas tulis

Tulis, bangun, uji, dan publikasikan pendamping Bahasa Indonesia yang menutup
batas kurikulum O006/C140 tanpa menyamarkan prosa orisinal sebagai Penn State
atau Siegrist. Batas tulis hanya `components/c140-companion/`, skrip integrasi
yang secara eksplisit menambahkan komponen ini, serta kontrol/receipt repositori
yang diperlukan untuk checkpoint dan publikasi. Jangan mengubah byte otoritas,
target Penn 14-dokumen, donor *Random*, atau repositori edisi *Random* 29 laman.
Semua materi pendamping adalah CC BY-SA 4.0, menggunakan provenans persis
`OpenAI Codex gpt-5.6-sol, Ultra`, dan mempertahankan seluruh kredit sumber dan
kontributor manusia.

## Batas isi hingga selesai

1. Model parametrik reguler: dominasi, identifiabilitas, support bersama,
   diferensiabilitas, pertukaran limit/integral, identitas score, informasi
   Fisher, konsistensi MLE, ekspansi likelihood lokal, normalitas asimtotik,
   delta method, Wald/score/rasio likelihood, dan limit tipe Wilks.
2. Kontraeksempel nonreguler: support bergantung parameter, parameter batas,
   informasi singular, dan kegagalan identifiabilitas; setiap contoh menyebut
   hipotesis teorema yang gagal dan kesimpulan yang tidak lagi sah.
3. Optimalitas: Neyman–Pearson termasuk randomisasi pada himpunan kesamaan, MP
   versus UMP, monotone likelihood ratio, risiko, efisiensi, Rao–Blackwell, dan
   Lehmann–Scheffé dengan tautan ID ke donor, bukan duplikasi prosa donor.
4. Model linear Gaussian fixed-design dalam bentuk matriks: proyeksi, OLS/MLE,
   Gauss–Markov, hukum sampling eksak, estimasi varians, standard error, uji
   t/F, interval kepercayaan/prediksi, ANOVA, simple dan multiple regression,
   serta pemeriksaan model.
5. Perbandingan Bayesian–frequentist: prior, posterior, keputusan, loss/risk,
   interval credible versus confidence, dan kalibrasi; gunakan LLN/CLT/Slutsky
   sebagai alat tanpa mengambil alih materi teori probabilitas D30.
6. Simulasi seeded dan offline untuk konvergensi sampling, bias/varians/risiko,
   coverage, size/power, bootstrap/delta, likelihood reguler/nonreguler,
   kalibrasi Bayesian, serta regresi simple/multiple. Setiap simulasi memiliki
   lingkungan terkunci, output CSV/SVG/teks deterministik, assertion numerik,
   deskripsi aksesibel, dan tautan ke teorema yang diuji.
7. Tiga belas set penguasaan, masing-masing sedikitnya delapan soal nontrivial;
   empat asesmen kumulatif; dua capstone data terbuka. Setiap soal mempunyai
   prasyarat, tujuan, tingkat kesulitan, tag miskonsepsi, petunjuk bertahap,
   jawaban singkat, solusi lengkap, dan—untuk asesmen/capstone—rubrik.

## Urutan produksi

Batch C1 adalah `D001`–`D007`, `SIM001`–`SIM004`, `MS07`–`MS10`, dan `CA01`.
Setelah C1 lulus, produksi batch model linear; lalu perbandingan Bayesian dan
simulasi sisanya; lalu seluruh set penguasaan/asesmen/capstone yang tersisa.
Tulis materi pembaca terlebih dahulu; backend dan QA adalah lapisan aditif dan
gate, bukan pengganti produksi. Gunakan Bahasa Indonesia id-ID yang alami,
pertahankan notasi matematika, dan jangan menyebut klaim sebagai teorema tanpa
hipotesis serta bukti atau rujukan internal yang lengkap.

Setiap dokumen dimulai dengan metadata JSON satu baris di antara dua baris
`---`, memakai ID netral-lokal. Setiap heading substantif didahului anchor HTML
unik. Referensi silang memakai `[ref:ID]`. Soal mengikuti kontrak di
`CONTENT_CONTRACT.md`. Bangun HTML offline, indeks, backend JSONL/CSV, dan
manifest secara deterministik. Jalankan pemeriksaan ID/referensi, formula,
struktur soal/solusi, hak, privasi, bahasa, aksesibilitas statis, output
simulasi, link lokal, serta replay byte-identik. Perbaiki temuan material sekali
dan maju; jangan mengubah QA menjadi loop.

## Larangan browser dan publikasi

Tidak satu langkah pun boleh meluncurkan Chrome, Chromium, Playwright,
Puppeteer, Electron, WebView, DAISY Ace, atau proses browser lain. Jangan
menyentuh browser pengguna. Gunakan hanya parser HTML/XML/CSS, validator paket,
Poppler bila kelak ada PDF, serta alat offscreen non-browser yang tidak memulai
Chromium. Pada boundary substansial yang lulus, commit/push dan publikasikan ke
lineage GitHub/Zenodo yang sudah ada tanpa meminta konfirmasi ulang, lalu baca
balik byte publik secara anonim. Jangan membuat konsep DOI saingan. Jangan
menghubungi upstream selama produksi.

## Durabilitas dan kondisi terminal

Perbarui `CURRENT_STATE.md`, `CURRENT_CURSOR.md`, ledger, backend, manifest,
hash, dan receipt pada setiap keputusan/batch material. Setelah kehilangan
konteks, pulihkan hanya dari file ini, `CONTENT_CONTRACT.md`, state/cursor,
ledger/backend, sumber pembaca, output simulasi, build/QA receipt, dan receipt
publikasi terbaru. Jangan memakai ringkasan percakapan sebagai state dan jangan
melakukan scan workspace atau Git yang luas.

Pendamping selesai hanya ketika seluruh lima batas teori/terapan, seluruh
keluarga simulasi, 13 set penguasaan, 4 asesmen, 2 capstone, backend, HTML,
hak, QA/replay, dan publikasi/readback lengkap. O006/C140 baru boleh ditutup
setelah komponen Penn, donor, dan pendamping semuanya lengkap serta tidak ada
pekerjaan tersisa pada kontrol hidup.
