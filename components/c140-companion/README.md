# Pendamping orisinal O006/C140 — Statistika Matematis

Komponen ini menutup celah rigor, simulasi, regresi matriks, dan pembelajaran
mandiri yang sengaja tidak dinisbatkan kepada Penn State STAT 415 atau Kyle
Siegrist. Seluruh prosa, soal, solusi, kode simulasi, dan lapisan editorial di
sini adalah materi orisinal berlisensi CC BY-SA 4.0.

Status saat ini: pendamping C5 lengkap secara lokal. Audit pascatranslasi,
build kumulatif, QA statis, dan pemeriksaan ulang deterministik telah lulus
tanpa browser atau akses jaringan. Publikasi kumulatif C5 sedang berlangsung;
C4 tetap menjadi rilis publik terakhir yang lengkap, terbit, dan telah dibaca
kembali secara anonim. C1 mencakup
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
capstone `CP01`–`CP02`. Cakupan kumulatif lokal C5 adalah:

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
Build/QA dalam mode `--write` dan `--check-only` telah lulus. Status lokal ini
belum merupakan klaim bahwa C5 telah terbit; pengemasan, publikasi, dan
pembacaan kembali byte publik C5 sedang berlangsung.

## Rilis publik terakhir: C4

[Pembaca web pendamping](https://kokunoyumeto.github.io/penn-state-stat-415-id/components/c140-companion/),
[rilis GitHub kumulatif C4](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.29.c140-companion-c4),
dan [preservasi Zenodo C4](https://doi.org/10.5281/zenodo.22164344) tetap menjadi
rujukan publik yang sudah terverifikasi, dalam
[konsep preservasi](https://doi.org/10.5281/zenodo.22077422).
Paket C4 memuat 57 berkas / 93.850.993 byte dan mempertahankan seluruh 49
berkas C3 secara byte-identik. Pada publikasi C4, seluruh 188 berkas Pages dan
57 berkas rilis GitHub/Zenodo telah dibaca kembali secara anonim dan cocok
byte demi byte serta SHA-256.

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

Hak konten Penn State, donor *Random*, dan pendamping orisinal tetap terpisah.
Materi orisinal pendamping memakai CC BY-SA 4.0; data CP01 memakai CC BY 4.0,
sedangkan data CP02 memakai CC0-1.0. Rincian hak dan kredit tetap tercatat dalam
[`LICENSE.md`](LICENSE.md).

Provenans produksi: `OpenAI Codex gpt-5.6-sol, Ultra`.
