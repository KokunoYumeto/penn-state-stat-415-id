# Pendamping orisinal O006/C140 — Statistika Matematis

Komponen ini menutup celah rigor, simulasi, regresi matriks, dan pembelajaran
mandiri yang sengaja tidak dinisbatkan kepada Penn State STAT 415 atau Kyle
Siegrist. Seluruh prosa, soal, solusi, kode simulasi, dan lapisan editorial di
sini adalah materi orisinal berlisensi CC BY-SA 4.0.

Status saat ini: pendamping C5 lengkap; rilis GitHub dan preservasi Zenodo C5
sudah terbit serta terverifikasi secara anonim. Audit pascatranslasi,
build kumulatif, QA statis, dan pemeriksaan ulang deterministik telah lulus
tanpa browser atau akses jaringan. Pages C5 juga telah lulus CI, terdeploy,
dan dibaca kembali secara anonim. C5 selesai pada seluruh tujuan publikasi dan
tidak menyisakan pekerjaan tertunda. C1 mencakup
model parametrik reguler, konsistensi dan normalitas asimtotik MLE, prosedur
Wald/score/rasio likelihood, kasus nonreguler, Neyman–Pearson, MP versus UMP,
risiko/efisiensi, empat simulasi deterministik, empat set penguasaan, dan satu
asesmen kumulatif. C2 menambahkan geometri proyeksi, keterestimasi, OLS/MLE,
Gauss–Markov, hukum sampling eksak, uji t/F, ANOVA, interval
kepercayaan/prediksi, diagnostik, heteroskedastisitas, satu simulasi seeded,
dan set penguasaan MS12.

C3 menambahkan pembaruan Bayesian dari hukum bersama, prediktif, keputusan di
bawah loss, risk frequentist/Bayes, prior improper, interval kredibel versus
kepercayaan, size/power, faktor Bayes, pemeriksaan prediktif, optional
stopping, kalibrasi Beta–binomial, dan set penguasaan MS11.

C4 menambahkan tujuh set penguasaan `MS00`–`MS06`, masing-masing dengan
delapan masalah lengkap. C5 menuntaskan tiga asesmen `CA02`–`CA04` dan dua
capstone `CP01`–`CP02`. Cakupan kumulatif C5 adalah:

- 39 dokumen / 1.145.637 byte sumber;
- 146 soal terpecahkan, 292 petunjuk bertahap, 146 jawaban singkat, dan
  146 solusi penuh;
- 1.349 anchor stabil / 379 referensi isi yang terselesaikan;
- pembaca HTML luring: 135 berkas / 15.757.728 byte;
- backend modular: 1.523 entitas / 1.949 relasi;
- 13 set penguasaan, empat asesmen kumulatif, dua capstone, dan enam simulasi
  deterministik.

Pembaca lokal tersedia di `build/html-id/index.html`. Identitas sumber dan
hasil build tercatat dalam [`C5_BUILD_RECEIPT.json`](build/C5_BUILD_RECEIPT.json),
hasil QA dalam [`C5_QA_RECEIPT.json`](build/C5_QA_RECEIPT.json), dan status
lengkap lokal dalam
[`CHECKPOINT_2026-08-31_C5_LOCAL_COMPLETE.md`](00_control/CHECKPOINT_2026-08-31_C5_LOCAL_COMPLETE.md).
Build/QA dalam mode `--write` dan `--check-only` telah lulus. Checkpoint
tersebut mencatat penyelesaian lokal; status publik terkini dirinci berikut.

## Rilis C5 terverifikasi di GitHub, Zenodo, dan Pages

[Rilis GitHub kumulatif C5](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.31.c140-companion-c5)
dan [preservasi Zenodo C5](https://doi.org/10.5281/zenodo.22208527) dalam
[konsep preservasi](https://doi.org/10.5281/zenodo.22077422) masing-masing
memuat 65 berkas / 134.904.267 byte. Seluruh 65 berkas pada kedua tujuan telah
diunduh kembali secara anonim dan cocok jumlah byte serta SHA-256. Seluruh
57 berkas warisan C4 dipertahankan byte-identik. Bukti tercatat dalam
[receipt GitHub C5](../../00_control/GITHUB_RELEASE_RECEIPT_2026-08-31_C140_COMPANION_C5.json)
dan [receipt Zenodo C5](../../00_control/ZENODO_PUBLIC_READBACK_2026-08-31_C140_COMPANION_C5.json).

Pages C5 terverifikasi pada run `33405870018`, deployment
`903d54c0971d3c14ec8f6fa0961136b881a73b82`: 259 berkas / 35.170.536 byte,
terdiri atas Penn 106 / 17.614.553 byte, donor 18 / 1.798.255 byte, dan
pendamping 135 / 15.757.728 byte. Seluruh berkas dibaca kembali secara anonim
dan cocok dengan byte serta SHA-256 yang dipatok. Bukti tersimpan dalam
[receipt Pages C5](../../00_control/GITHUB_PAGES_RECEIPT_2026-08-31_C140_COMPANION_C5.json)
(103.239 byte; SHA-256
`2230f83f946c83d5a9633cdc3f4b1c5af72069634ff72586768a4f8f08a3eae6`).
[Pembaca web utama](https://kokunoyumeto.github.io/penn-state-stat-415-id/)
dan [pembaca web pendamping](https://kokunoyumeto.github.io/penn-state-stat-415-id/components/c140-companion/)
keduanya terverifikasi untuk C5; tidak ada pekerjaan C5 yang masih tertunda.

[Rilis GitHub kumulatif C4](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.29.c140-companion-c4)
dan [preservasi Zenodo C4](https://doi.org/10.5281/zenodo.22164344) merupakan
versi historis yang diwarisi C5. Paket C4 memuat 57 berkas / 93.850.993 byte dan
mempertahankan seluruh 49 berkas C3 secara byte-identik. Pada publikasi C4,
seluruh 188 berkas Pages dan 57 berkas rilis GitHub/Zenodo telah dibaca kembali
secara anonim dan cocok byte demi byte serta SHA-256.

## Reproduksi lokal C5

Jalankan dari akar repositori dengan Python 3.13 dan dependensi yang dipatok
dalam `requirements.txt`:

```text
python -B scripts/hydrate_cp02_coverage.py --write
python -B scripts/hydrate_cp02_coverage.py --check-only
python -B components/c140-companion/scripts/build_companion.py --check-only --c5
python -B components/c140-companion/scripts/qa_companion.py --check-only --c5
python -B scripts/assemble_pages_collection.py --check-only
python -B scripts/package_c140_companion_c5_release.py --check-only
```

Hidrasi memulihkan CSV cakupan CP02 yang tidak dilacak Git dari gzip lokal
yang identitasnya dipatok. Perintah `--write` hanya membuat CSV bila belum ada;
berkas yang sudah ada harus cocok jumlah byte dan SHA-256, bukan ditimpa.
Build, QA, dan pengemasan lokal tidak melakukan publikasi.

Syarat reproduksi membedakan identitas data dan artefak pembaca—jumlah byte
dan SHA-256 harus cocok secara eksak—dari perbandingan sertifikat numerik CI
lintas platform yang dibatasi toleransi eksplisit per besaran. Ini bukan
klaim bahwa seluruh keluaran BLAS lintas platform byte-identik; toleransi
numerik tidak menggantikan pemeriksaan hash data atau pembaca.

Hak konten Penn State, donor *Random*, dan pendamping orisinal tetap terpisah.
Materi orisinal pendamping memakai CC BY-SA 4.0; data CP01 memakai CC BY 4.0,
sedangkan data CP02 memakai CC0-1.0. Rincian hak dan kredit tetap tercatat dalam
[`LICENSE.md`](LICENSE.md).

Provenans produksi: `OpenAI Codex gpt-5.6-sol, Ultra`.
