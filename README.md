# STAT 415 — edisi Bahasa Indonesia

Rekonstruksi semantik dan terjemahan Bahasa Indonesia (`id-ID`) dari rangkaian
publik Penn State STAT 415, *Introduction to Mathematical Statistics*, untuk
komponen O006/C140.

## Status

**Sebagian — 3 dari 14 dokumen lengkap.** Laman utama, seluruh Pelajaran 00,
dan seluruh Pelajaran 01 sudah diterjemahkan, dibangun, dan lulus pemeriksaan
deterministik serta visual. Pelajaran 02–12 tetap tercantum dan untuk sementara
menaut ke halaman resmi berbahasa Inggris. Batas akhir edisi ini adalah laman
utama dan Pelajaran 00–12, sebanyak 14 dokumen.

- 744 segmen terjemahan lengkap;
- 750 unit struktural sumber dengan ID stabil dan 748 unit turunan;
- 500 permukaan matematika, semuanya terikat ke ID yang netral terhadap locale;
- 20 koreksi turunan terverifikasi; byte sumber resmi tidak diubah;
- pembaca HTML luring: 28 berkas / 2.598.449 byte.

Pembaca lokal tersedia di `build/html-id/index.html`. Riwayat sumber,
identitas SHA-256, hak komponen, koreksi, backend modular, hasil build, dan
bukti QA disimpan bersama edisi.

- Repositori publik: https://github.com/KokunoYumeto/penn-state-stat-415-id
- Pembaca web: https://kokunoyumeto.github.io/penn-state-stat-415-id/
- Rilis publik terbaru: https://github.com/KokunoYumeto/penn-state-stat-415-id/releases
- Konsep preservasi: https://doi.org/10.5281/zenodo.22077422

## Reproduksi

Gunakan Python 3.13 dan dependensi yang dipatok di `requirements.txt`, lalu
jalankan:

```text
python scripts/freeze_stat415.py --check-only
python scripts/freeze_first_unit_assets.py --check-only
python scripts/freeze_lesson01_assets.py --check-only
python scripts/freeze_mathjax.py --check-only
python scripts/normalize_first_unit.py --check-only
python scripts/merge_first_unit_translations.py --check-only
python scripts/normalize_lesson01.py --check-only
python scripts/merge_lesson01_translations.py --check-only
python scripts/build_through_lesson01.py --check-only
python scripts/qa_through_lesson01.py --check-only
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
