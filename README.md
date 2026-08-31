# STAT 415 — edisi Bahasa Indonesia

Rekonstruksi semantik dan terjemahan Bahasa Indonesia (`id-ID`) dari rangkaian
publik Penn State STAT 415, *Introduction to Mathematical Statistics*, untuk
komponen O006/C140.

## Status

**Tulang punggung Penn State lengkap dan terbit — seluruh 14 dari 14 dokumen
sudah diterjemahkan, dibangun, lulus QA, dan dibaca kembali dari repositori
publik.** Laman utama serta Pelajaran 00–12 membentuk satu pembaca luring
lengkap. GitHub/Pages, rilis GitHub, dan versi preservasi Zenodo yang mengikat
perbaikan reproduksibilitas LF semuanya sudah publik dan terverifikasi secara
anonim. Pendamping orisinal C140 telah lengkap dan lulus build/QA C5;
preservasi C5 di Zenodo dan rilis GitHub C5 sudah terbit serta terverifikasi.
Pages C5 juga sudah terdeploy dan dibaca kembali secara anonim. Dengan demikian,
edisi C5 lengkap pada seluruh tujuan publikasi dan tidak menyisakan pekerjaan
tertunda.

- 4.932 segmen terjemahan di dalam pembaca lengkap;
- 6.510 unit struktural sumber dengan ID stabil dan 6.498 unit turunan;
- 3.156 permukaan matematika sumber terlindungi terverifikasi; Pelajaran 12 juga
  memuat 20 permukaan MathJax target-native/aditif yang tercatat;
- 242 koreksi atau disposisi turunan terverifikasi; byte sumber resmi tidak
  diubah;
- pembaca HTML luring: 106 berkas / 17.614.553 byte;
- pembaca PDF lengkap: 219 halaman / 20.170.549 byte, dengan replay byte-identik;
- pembaca EPUB lengkap: 12.301.415 byte / 111 entri, 3.159 simpul MathML,
  17 fallback SVG, dan 125 kawasan rumus berisiko lebar yang dapat difokuskan;
- QA visual: 15 rute pada 1.280 × 720 dan 390 × 844, 67 kejadian gambar,
  14 tabel, tiga padanan video luring, tanpa luapan halaman atau galat MathJax.

Pembaca lokal tersedia di `build/html-id/index.html`. Riwayat sumber,
identitas SHA-256, hak komponen, koreksi, backend modular, hasil build, dan
bukti QA disimpan bersama edisi.

- Repositori publik: https://github.com/KokunoYumeto/penn-state-stat-415-id
- Pembaca web: https://kokunoyumeto.github.io/penn-state-stat-415-id/
- Rilis publik PDF/EPUB lengkap 14-dari-14:
  https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.28.14of14-pdf-epub
- Konsep preservasi: https://doi.org/10.5281/zenodo.22077422
- Preservasi publik PDF/EPUB lengkap 14-dari-14:
  https://doi.org/10.5281/zenodo.22142292
- Paket preservasi reader-first terbaru memuat 17 berkas / 87.848.426 byte.
  PDF menjadi berkas utama, disusul EPUB reflowable, pembaca HTML luring,
  source/backend, hak komponen, dan bukti QA ringkas. Seluruh 17 berkas pada
  GitHub dan Zenodo sudah diunduh kembali secara anonim dan cocok byte demi
  byte serta SHA-256; audit konsep Zenodo menemukan nol draf yang belum
  dikirim.

## Komponen donor kelengkapan C140

Donor *Random* satu halaman untuk kecukupan, kelengkapan, ancillary,
Rao–Blackwell, Lehmann–Scheffé, dan Basu sekarang lengkap dalam jalur komponen
terpisah. Target id-ID kanonis diwarisi dari halaman pada edisi *Random*
lengkap, dengan satu penyempurnaan istilah pembaca sebesar lima byte yang
dicatat dalam [README donor](components/random-completeness/README.md).
Salinan integrasi menambahkan identitas komponen dan mengarahkan tautan
lintas-halaman ke edisi lengkap; byte sumber resmi tidak diubah.

- pembaca donor saat ini: 18 berkas / 1.798.255 byte;
- struktur: 804 rentang TeX, 39 unit, dan 26 rincian/derivasi;
- backend: 325 entitas / 474 relasi;
- QA statis dan replay deterministik: lulus;
- pembaca publik:
  https://kokunoyumeto.github.io/penn-state-stat-415-id/components/random-completeness/;
- rilis GitHub kumulatif:
  https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.28.c140-random-completeness;
- preservasi Zenodo kumulatif:
  https://doi.org/10.5281/zenodo.22143454;
- sumber, backend, hak, dan receipt:
  `components/random-completeness/`.

Rilis kumulatif memuat 25 berkas / 89.238.225 byte. Seluruh 17 artefak Penn
sebelumnya dipertahankan byte demi byte, lalu delapan berkas donor/kontrol
ditambahkan. Semua byte publik GitHub dan Zenodo sudah diverifikasi; audit
konsep Zenodo menemukan nol draf yang belum dikirim.

Hak donor tetap terpisah dari CC BY-NC 4.0 Penn State. Saksi laman utama
*Random* menyatakan CC BY 2.0, sedangkan `Credits.html` menautkan CC BY 1.0;
keduanya dipertahankan dan tidak disamakan secara diam-diam.

## Pendamping orisinal C140 — C5 terverifikasi di GitHub, Zenodo, dan Pages

Pendamping orisinal CC BY-SA 4.0 telah lengkap sampai C5. Audit
pascatranslasi, build kumulatif, QA statis, dan pemeriksaan ulang deterministik
telah lulus tanpa proses browser. Rilis kumulatif C5 di GitHub dan Zenodo sudah
terbit dan seluruh berkas pada kedua tujuan telah diverifikasi secara anonim.
Pages C5 juga telah lulus CI, terdeploy, dan terverifikasi melalui pembacaan
kembali anonim. Edisi C5 lengkap pada seluruh tujuan publikasi.

C1 memuat fondasi fungsi kemungkinan, optimalitas, risiko, empat simulasi,
empat set penguasaan, dan asesmen `CA01`. C2 menambahkan empat unit model linear
Gaussian matriks, simulasi regresi dengan seed tetap, dan set penguasaan `MS12`.
C3 menambahkan dua unit perbandingan Bayesian–frekuentis, simulasi kalibrasi
interval, dan set penguasaan `MS11`. C4 menambahkan tujuh set penguasaan
`MS00`–`MS06`. C5 menuntaskan tiga asesmen `CA02`–`CA04` dan dua capstone
`CP01`–`CP02`. Cakupan C5 lengkap sekarang adalah:

- 39 dokumen / 1.145.637 byte sumber;
- 146 soal terpecahkan, 292 petunjuk bertahap, 146 jawaban singkat, dan
  146 solusi penuh;
- 1.349 anchor stabil / 379 referensi isi yang terselesaikan;
- pembaca HTML luring: 135 berkas / 15.757.728 byte;
- backend modular: 1.523 entitas / 1.949 relasi;
- 13 set penguasaan, empat asesmen kumulatif, dua capstone, dan enam simulasi
  deterministik.

Pembaca lokal berada di `components/c140-companion/build/html-id/index.html`.
Identitas sumber dan hasil build tercatat dalam
[`C5_BUILD_RECEIPT.json`](components/c140-companion/build/C5_BUILD_RECEIPT.json),
hasil QA dalam
[`C5_QA_RECEIPT.json`](components/c140-companion/build/C5_QA_RECEIPT.json), dan
status lengkap lokal dalam
[`CHECKPOINT_2026-08-31_C5_LOCAL_COMPLETE.md`](components/c140-companion/00_control/CHECKPOINT_2026-08-31_C5_LOCAL_COMPLETE.md).
Checkpoint tersebut mencatat penyelesaian lokal; status publik terkini
dirinci berikut.

[Rilis GitHub kumulatif C5](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.31.c140-companion-c5)
dan [preservasi Zenodo C5](https://doi.org/10.5281/zenodo.22208527) dalam
[konsep preservasi](https://doi.org/10.5281/zenodo.22077422) masing-masing
memuat 65 berkas / 134.904.267 byte. Seluruh 65 berkas pada kedua tujuan telah
diunduh kembali secara anonim dan cocok jumlah byte serta SHA-256; seluruh
57 berkas warisan C4 tetap byte-identik. Bukti tercatat dalam
[receipt GitHub C5](00_control/GITHUB_RELEASE_RECEIPT_2026-08-31_C140_COMPANION_C5.json)
dan [receipt Zenodo C5](00_control/ZENODO_PUBLIC_READBACK_2026-08-31_C140_COMPANION_C5.json).

Pages C5 terverifikasi pada run `33405870018`, deployment
`903d54c0971d3c14ec8f6fa0961136b881a73b82`: 259 berkas / 35.170.536 byte,
terdiri atas Penn 106 / 17.614.553 byte, donor 18 / 1.798.255 byte, dan
pendamping 135 / 15.757.728 byte. Seluruh berkas dibaca kembali secara anonim
dan cocok dengan byte serta SHA-256 yang dipatok. Bukti tersimpan dalam
[receipt Pages C5](00_control/GITHUB_PAGES_RECEIPT_2026-08-31_C140_COMPANION_C5.json)
(103.239 byte; SHA-256
`2230f83f946c83d5a9633cdc3f4b1c5af72069634ff72586768a4f8f08a3eae6`).
Tidak ada pekerjaan C5 yang masih tertunda.

- [pembaca web utama](https://kokunoyumeto.github.io/penn-state-stat-415-id/)
  — terverifikasi untuk C5;
- [pembaca web pendamping](https://kokunoyumeto.github.io/penn-state-stat-415-id/components/c140-companion/)
  — terverifikasi untuk C5;
- [rilis GitHub kumulatif C4](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.29.c140-companion-c4)
  — versi historis yang diwarisi C5;
- [preservasi Zenodo C4](https://doi.org/10.5281/zenodo.22164344)
  — versi historis yang diwarisi C5.

Paket C4 memuat 57 berkas / 93.850.993 byte dan mewarisi seluruh 49 berkas C3
secara byte-identik. Pada publikasi C4, seluruh 188 berkas Pages dan 57 berkas
rilis GitHub/Zenodo cocok pada pembacaan kembali anonim. Hak Penn, donor
*Random*, pendamping orisinal, serta dataset kedua capstone tetap dipisahkan.

## Reproduksi

Gunakan Python 3.13 dan dependensi yang dipatok di `requirements.txt`, lalu
jalankan:

```text
python -B scripts/freeze_stat415.py --check-only
python -B scripts/freeze_first_unit_assets.py --check-only
python -B scripts/freeze_lesson01_assets.py --check-only
python -B scripts/freeze_lesson02_assets.py --check-only
python -B scripts/freeze_lesson04_assets.py --check-only
python -B scripts/freeze_lesson11_asset.py --check-only
python -B scripts/freeze_lesson12_assets.py --check-only
python -B scripts/freeze_mathjax.py --check-only
python -B scripts/normalize_first_unit.py --check-only
python -B scripts/merge_first_unit_translations.py --check-only
python -B scripts/normalize_lesson01.py --check-only
python -B scripts/merge_lesson01_translations.py --check-only
python -B scripts/normalize_lesson02.py --check-only
python -B scripts/merge_lesson02_translations.py --check-only
python -B scripts/normalize_lesson03.py --check-only
python -B scripts/merge_lesson03_translations.py --check-only
python -B scripts/normalize_lesson04.py --check-only
python -B scripts/merge_lesson04_translations.py --check-only
python -B scripts/normalize_lesson05.py --check-only
python -B scripts/merge_lesson05_translations.py --check-only
python -B scripts/normalize_lesson06.py --check-only
python -B scripts/merge_lesson06_translations.py --check-only
python -B scripts/normalize_lesson07.py --check-only
python -B scripts/merge_lesson07_translations.py --check-only
python -B scripts/normalize_lesson08.py --check-only
python -B scripts/merge_lesson08_translations.py --check-only
python -B scripts/normalize_lesson09.py --check-only
python -B scripts/merge_lesson09_translations.py --check-only
python -B scripts/normalize_lesson10.py --check-only
python -B scripts/merge_lesson10_translations.py --check-only
python -B scripts/normalize_lesson11.py --check-only
python -B scripts/merge_lesson11_translations.py --check-only
python -B scripts/normalize_lesson12.py --check-only
python -B scripts/merge_lesson12_translations.py --check-only
python -B scripts/materialize_lesson12_translation.py --check-only
python -B scripts/build_through_lesson12.py --check-only
python -B scripts/qa_through_lesson12.py --check-only
python -B scripts/normalize_consolidated_book.py --check-only
python -B scripts/audit_consolidated_pdf.py --check-only
python -B scripts/write_consolidated_pdf_visual_receipt.py --check-only
python -B scripts/audit_consolidated_epub.py --check-only
python -B scripts/audit_consolidated_epub_static_reflow.py --check-only
python -B scripts/package_consolidated_readers_release.py --check-only
python -B components/c140-companion/simulations/run_c1_simulations.py --check-only
python -B components/c140-companion/simulations/run_c2_simulations.py --check-only
python -B components/c140-companion/simulations/run_c3_simulations.py --check-only
python -B scripts/hydrate_cp02_coverage.py --write
python -B scripts/hydrate_cp02_coverage.py --check-only
python -B components/c140-companion/scripts/build_companion.py --check-only --c5
python -B components/c140-companion/scripts/qa_companion.py --check-only --c5
python -B scripts/assemble_pages_collection.py --check-only
python -B scripts/package_c140_companion_c5_release.py --check-only
python -B scripts/publish_github_consolidated_readers_release.py --local-preflight
python -B scripts/publish_zenodo_consolidated_readers.py --local-preflight
```

Hidrasi CP02 memulihkan CSV cakupan yang tidak dilacak Git dari gzip lokal
yang identitasnya dipatok. Perintah `--write` hanya membuat CSV bila belum ada;
berkas yang sudah ada harus cocok jumlah byte dan SHA-256, bukan ditimpa.

Syarat reproduksi membedakan identitas data dan artefak pembaca—jumlah byte
dan SHA-256 harus cocok secara eksak—dari perbandingan sertifikat numerik CI
lintas platform yang dibatasi toleransi eksplisit per besaran. Ini bukan
klaim bahwa seluruh keluaran BLAS lintas platform byte-identik; toleransi
numerik tidak menggantikan pemeriksaan hash data atau pembaca.

Untuk membaca secara lokal, layani `build/html-id` dengan peladen HTTP statis;
misalnya `python -m http.server` dari direktori tersebut.

QA EPUB final menggunakan EPUBCheck dan audit XML/CSS/paket deterministik.
Laporan Ace yang disertakan adalah bukti historis untuk hash kandidat yang
disebutkan secara eksplisit, bukan validasi hash EPUB final. Sesuai kendala
eksekusi edisi ini, rangkaian final tidak meluncurkan proses peramban.

## Sumber, perubahan, dan lisensi

Distribusi resmi yang terbukti adalah HTML semantik hasil Quarto. Repositori
ini tidak mengklaim sebagai fork sumber QMD Penn State dan tidak mengarang
konfigurasi, tag, commit, atau arsip authoring yang tidak tersedia.

Konten Penn State dan adaptasi Bahasa Indonesianya tetap berada di bawah
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) kecuali
dinyatakan lain. MathJax 3.1.2 berada di bawah Apache-2.0. Lapisan asli
repositori memiliki identitas lisensi terpisah sebagaimana dijelaskan dalam
`LICENSE.md`; keseluruhan koleksi tidak direlisensi secara seragam. Tidak ada
dukungan atau pengesahan oleh Penn State yang tersirat.

Provenans terjemahan: **OpenAI Codex gpt-5.6-sol, Ultra**. Seluruh kredit karya
sumber dan kontributor manusia dipertahankan.
