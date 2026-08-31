# Checkpoint sumber C5 — CA02 lengkap

Tanggal: 2026-08-29

`O006-C140-CMP-CA02.md` adalah asesmen kumulatif fondasi inferensi sampel
hingga. Sumber final mempunyai 50.036 byte dan SHA-256
`159628fdccdcb6f315bbfb1c5e96e423072566630817fbe20bdfdabc520fafda`.
Ia berbahasa `id-ID`, berlisensi CC BY-SA 4.0, dan memakai provenans persis
`OpenAI Codex gpt-5.6-sol, Ultra`.

Struktur final adalah sepuluh masalah bernilai sepuluh poin, 20 petunjuk,
sepuluh jawaban singkat, sepuluh solusi lengkap, `RUB00`–`RUB10`, 62 anchor
unik, sepuluh `PROBLEM_META` valid, dan 15 referensi internal yang semuanya
terselesaikan. Total masalah dan rubrik masing-masing tepat 100 poin. Berkas
UTF-8 tanpa BOM, hanya LF, tanpa karakter kontrol, dan tanpa command TeX yang
kehilangan backslash.

CA02 mencakup sampling tanpa pengembalian; transformasi serta minimum/maksimum;
kuantil distribution-free dan endpoint; konsistensi versus konvergensi momen;
sufficiency, minimality, completeness, ancillary dan Basu; MoM versus MLE
global pada batas Pareto; informasi/CRLB/pivot/Wald; delta/bootstrap/coverage;
size, p-value, power, ukuran sampel dan inversi; serta audit terpadu model
geometrik. Ia tidak mengulang bukti NP/UMP, contoh delta berturunan nol, atau
derivasi Rao–Blackwell/Lehmann–Scheffé dari `CA01`.

Audit independen memeriksa seluruh masalah, petunjuk, jawaban, solusi dan
rubrik. Koreksi yang ditutup adalah tujuh command spacing TeX; pembulatan
endpoint Wald; pemisahan kuantil Normal eksak dari pendekatan 1,96; penggunaan
kuantil chi-square simbolik eksak; dan pembedaan MLE model terbuka dari
estimator closure pada kejadian geometrik `S=5`. Audit akhir menghitung ulang
interval chi-square `[0,8305, 9,6982]`, interval Wald
`[-0,2632, 4,2632]`, minimum ukuran sampel 43, p-value geometrik
`0,3668967424`, serta batas bawah `0,2224411`, lalu melaporkan PASS tanpa cacat
definitif tersisa.

Belum ada build atau publikasi C5 pada checkpoint sumber ini. C4 tetap
boundary publik terakhir. Tindakan berikutnya: selesaikan/audit `CA03` dan
`CA04`, perbarui indeks serta build/backend/QA secara kumulatif untuk ketiga
asesmen, lalu lanjutkan dua capstone sesuai kontrak C5. Larangan browser dan
kontak upstream tetap berlaku.
