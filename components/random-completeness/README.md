# Donor kelengkapan Random untuk O006/C140

Komponen ini adalah tepat satu halaman eksternal yang dipilih untuk menutup
permukaan kecukupan dan kelengkapan pada kursus O006/C140:
Kyle Siegrist, *Random*, “Sufficient, Complete, and Ancillary Statistics”.
Komponen ini terpisah dari tulang punggung Penn State STAT 415 dan dari
pendamping orisinal C140. Edisi lengkap *Random* 29 halaman juga tetap berada
di repositori publiknya sendiri; berkas di sini adalah impor satu halaman yang
terikat ke identitas edisi itu, bukan fork kedua dari seluruh buku.

**Status: lengkap dan lulus QA statis.** Pembaca luring donor berisi 18 berkas
/ 1.798.255 byte. Receipt build mempunyai SHA-256
`4b72a36653305ab36f6b1863ecd0fd04e416888c83dff58bff20632e83aebd06`;
receipt QA mempunyai SHA-256
`a4265feb621ec79c4bb2870f03e69f8b73659e6bea3d4e4d905cda3be97fc5c7`.
Keduanya diputar ulang dengan hasil identik tanpa proses peramban.

## Batas dan identitas

- sumber resmi: 57.507 byte / SHA-256
  `4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4`;
- target id-ID kanonis: 60.900 byte / SHA-256
  `18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197`;
- struktur: 436 elemen sumber, 804 rentang TeX terbatas, 39 unit, dan 26
  rincian/derivasi;
- backend donor: 325 entitas dan 474 relasi dengan ID stabil yang sama seperti
  edisi lengkap;
- entitas dokumen: `O006-016-00-0001`;
- jangkar semantik halaman: `o006.random.point.sufficient.page`.

Materi mencakup statistik cukup, kecukupan minimal, teorema faktorisasi,
statistik lengkap dan ancillary, Rao–Blackwell, Lehmann–Scheffé, Basu, serta
contoh Bernoulli, Poisson, normal, gamma, beta, Pareto, seragam,
hipergeometrik, dan keluarga eksponensial. Koreksi matematis target tetap
terikat pada 19 catatan donor yang diimpor; byte sumber resmi tidak berubah.

## Provenans dan hubungan sumber

Target kanonis, backend, dan catatan koreksi diimpor secara deterministik dari
edisi lengkap `KokunoYumeto/mathematical-statistics-id`. Commit
`f2aab7b9a0578dd76624e183fc47e3c1faa664e8` tetap menjadi saksi publik dasar;
target kini memuat satu penyempurnaan istilah pembaca pada 2026-08-31,
`bersupport tetap` menjadi `dengan dukungan tetap` (+5 byte), tanpa perubahan
pada makna matematis atau byte otoritas. Edisi lengkap dapat dibaca di:

- https://kokunoyumeto.github.io/mathematical-statistics-id/random/point/Sufficient.html
- https://github.com/KokunoYumeto/mathematical-statistics-id/releases/tag/v2026.08.24.29
- https://doi.org/10.5281/zenodo.22076539

`IMPORT_RECEIPT.json` mengikat setiap byte impor tanpa menyimpan jalur lokal.
Salinan target kanonis tidak diubah. Build komponen menurunkan salinan
integrasi secara deterministik, mempertahankan aset lokal, dan mengarahkan
tautan ke halaman *Random* lain ke edisi lengkap agar tidak menjadi tautan
lokal yang rusak.

Pembaca hasil build berada di `build/html-id/index.html`. Tujuh SVG kecil yang
jelas diberi label `original-build-only-css-fallback` menutup referensi
dekoratif lama di `Screen.css` yang tidak termasuk dalam subset otoritas satu
halaman; berkas itu bukan aset sumber dan tidak mengubah byte otoritas atau
target kanonis.

Provenans terjemahan dan rekayasa edisi:
`OpenAI Codex gpt-5.6-sol, Ultra`. Seluruh kredit penulis sumber dan
kontributor manusia dipertahankan.

## Reproduksi tanpa peramban

Impor dapat diputar ulang dari clone edisi lengkap yang berdampingan:

```text
python -B scripts/import_random_completeness_donor.py --sibling-root <clone-edisi-random> --check-only
python -B scripts/build_random_completeness_donor.py --check-only
python -B scripts/qa_random_completeness_donor.py --check-only
```

Build dan QA komponen ini hanya memakai pemeriksaan statis/paket. Tidak ada
Chrome, Chromium, Playwright, Puppeteer, Electron, WebView, Ace, atau proses
peramban lain yang diperlukan atau diizinkan.

Lihat `LICENSE_AND_ATTRIBUTION.md` untuk hak komponen dan perbedaan saksi
lisensi sumber.
