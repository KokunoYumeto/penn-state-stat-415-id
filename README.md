# STAT 415: terjemahan Bahasa Indonesia *Introduction to Mathematical Statistics* (Penn State)

Rekonstruksi semantik dan terjemahan Bahasa Indonesia yang lengkap dari catatan kuliah publik Penn State STAT 415,
*Introduction to Mathematical Statistics*: laman utama dan Pelajaran 00–12 (14 dari 14 dokumen) sebagai pembaca HTML,
PDF (219 halaman), dan EPUB. Repositori ini juga memuat satu halaman donor dari *Random* karya Kyle Siegrist tentang
statistik cukup, lengkap, dan ancillary (Rao–Blackwell, Lehmann–Scheffé, Basu) dan pendamping orisinal dengan 146 soal
terpecahkan, 13 set penguasaan, empat asesmen kumulatif, dua capstone, dan enam simulasi deterministik.

[Baca daring](https://kokunoyumeto.github.io/penn-state-stat-415-id/) · [PDF](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/download/v2026.08.31.c140-companion-c5/00_00_stat415-pengantar-statistika-matematis-id.pdf) ·
[EPUB](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/download/v2026.08.31.c140-companion-c5/00_01_stat415-pengantar-statistika-matematis-id.epub) ·
[Pendamping](https://kokunoyumeto.github.io/penn-state-stat-415-id/components/c140-companion/)

## Cara pembuatan

Rekonstruksi, terjemahan, dan pendamping orisinal dikerjakan oleh AI: OpenAI Codex gpt-5.6-sol, Ultra. Sumbernya
adalah HTML semantik resmi (keluaran Quarto) kursus Penn State; byte sumber resmi tidak diubah, dan 242 koreksi atau
disposisi turunan dicatat. Sebanyak 3.156 permukaan matematika sumber yang dilindungi diverifikasi; PDF dibangun ulang
dengan hasil byte-identik; EPUB diperiksa dengan EPUBCheck dan audit paket deterministik; pemeriksaan visual mencakup 15
rute pada ukuran desktop dan telepon tanpa luapan halaman atau galat MathJax.

## Status

Lengkap: seluruh 14 dokumen Penn State, halaman donor *Random*, dan pendamping orisinal sampai tahap C5 (39 dokumen;
146 soal dengan 292 petunjuk bertahap, 146 jawaban singkat, dan 146 solusi penuh). Masih mungkin ada kesalahan.

## Isi

- [Rilis kumulatif v2026.08.31.c140-companion-c5](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.31.c140-companion-c5): PDF, EPUB, pembaca luring, serta paket sumber dan backend untuk kursus utama,
  donor, dan pendamping C1–C5; rilis tahap sebelumnya tetap tersedia di [rilis GitHub](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases).
- `build/html-id/`: pembaca lokal (layani dengan peladen HTTP statis, misalnya `python -m http.server`).
- `components/random-completeness/`: komponen donor *Random*; `components/c140-companion/`: pendamping orisinal.
- `source/`, `backend/`, `authority/`, `00_control/`, `scripts/`: sumber semantik, backend modular (ID stabil), sumber
  resmi yang dibekukan, catatan kendali, dan skrip.

Reproduksi dengan Python 3.13 dan dependensi di `requirements.txt`:

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
```

## Sumber dan atribusi

- Penn State Department of Statistics, [*STAT 415: Introduction to Mathematical Statistics*](https://online.stat.psu.edu/stat415/).
  Edisi ini adalah terjemahan dan rekonstruksi tidak resmi; Penn State tidak mendukung atau mengesahkannya.
- Kyle Siegrist, *Random*, [“Sufficient, Complete, and Ancillary Statistics”](https://www.randomservices.org/random/point/Sufficient.html);
  rincian di `components/random-completeness/LICENSE_AND_ATTRIBUTION.md`.
- MathJax 3.1.2 (Apache-2.0).

## Lisensi

Konten Penn State dan adaptasi Bahasa Indonesianya tersedia menurut CC BY-NC 4.0 kecuali dinyatakan lain. Halaman donor
*Random* mempertahankan kedua saksi lisensi resminya (CC BY 2.0 dan CC BY 1.0); pendamping orisinal CC BY-SA 4.0;
MathJax Apache-2.0. Koleksi ini tidak berlisensi seragam; lihat [LICENSE.md](LICENSE.md).
