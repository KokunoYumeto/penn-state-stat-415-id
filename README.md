# STAT 415 — edisi Bahasa Indonesia

Rekonstruksi semantik dan terjemahan Bahasa Indonesia (`id-ID`) dari rangkaian
publik Penn State STAT 415, *Introduction to Mathematical Statistics*, untuk
komponen O006/C140.

## Status

**Lengkap secara lokal — seluruh 14 dari 14 dokumen sudah diterjemahkan,
dibangun, dan lulus QA.** Laman utama serta Pelajaran 00–12 kini membentuk satu
pembaca luring lengkap. Batas publik terakhir masih 13-dari-14 sampai transaksi
rilis lengkap dan pembacaan balik byte publik selesai.

- 4.932 segmen terjemahan di dalam pembaca lengkap;
- 6.510 unit struktural sumber dengan ID stabil dan 6.498 unit turunan;
- 3.156 permukaan matematika sumber terlindungi terverifikasi; Pelajaran 12 juga
  memuat 20 permukaan MathJax target-native/aditif yang tercatat;
- 242 koreksi atau disposisi turunan terverifikasi; byte sumber resmi tidak
  diubah;
- pembaca HTML luring: 106 berkas / 17.614.553 byte;
- QA visual: 15 rute pada 1.280 × 720 dan 390 × 844, 67 kejadian gambar,
  14 tabel, tiga padanan video luring, tanpa luapan halaman atau galat MathJax.

Pembaca lokal tersedia di `build/html-id/index.html`. Riwayat sumber,
identitas SHA-256, hak komponen, koreksi, backend modular, hasil build, dan
bukti QA disimpan bersama edisi.

- Repositori publik: https://github.com/KokunoYumeto/penn-state-stat-415-id
- Pembaca web: https://kokunoyumeto.github.io/penn-state-stat-415-id/
- Rilis publik terbaru: https://github.com/KokunoYumeto/penn-state-stat-415-id/releases
- Konsep preservasi: https://doi.org/10.5281/zenodo.22077422
- Preservasi publik terverifikasi saat ini, hingga Pelajaran 11:
  https://doi.org/10.5281/zenodo.22104871
- Paket preservasi reader-first 13-dari-14 (51.832.274 byte, sembilan berkas)
  telah diterbitkan pada konsep DOI yang sama dan seluruh byte publiknya telah
  dibaca kembali secara anonim. Commit, Pages, tag/rilis, berkas Zenodo, dan
  garis keturunan konsepnya cocok dengan bukti lokal; tidak ada draf Zenodo
  yang tersisa untuk versi ini.

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
```

Untuk membaca secara lokal, layani `build/html-id` dengan peladen HTTP statis;
misalnya `python -m http.server` dari direktori tersebut.

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
