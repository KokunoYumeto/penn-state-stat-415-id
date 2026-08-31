# Kandidat data capstone C5 — bukti primer sebelum freeze

Status: rekam seleksi historis, diperbarui 2026-08-31. Gate byte, metadata,
kamus, hak tingkat-aset, privasi, dan replay transformasi sudah lulus.
Kandidat utama CP01 dan CP02 di bawah telah diterima dan dibekukan; alternatif
serta kondisi pembaliknya dipertahankan sebagai jejak keputusan, bukan sebagai
status produksi yang masih terbuka.

## CP01 — kandidat utama regresi matriks

Kandidat utama adalah UCI *Concrete Compressive Strength*:

- record/DOI: `https://archive.ics.uci.edu/dataset/165/concrete` dan
  `https://doi.org/10.24432/C5PK67`;
- CSV: `https://archive.ics.uci.edu/static/public/165/data.csv`;
- arsip asli: `https://archive.ics.uci.edu/static/public/165/concrete%2Bcompressive%2Bstrength.zip`;
- metadata/kamus: `https://archive.ics.uci.edu/api/dataset?id=165`;
- penerbit UCI, depositor I-Cheng Yeh, donasi 2007-08-02;
- 1.030 baris, delapan prediktor kuantitatif, satu respons strength kontinu,
  tanpa nilai hilang menurut metadata penerbit;
- landing dataset menyatakan CC BY 4.0 dan mengizinkan berbagi/adaptasi dengan
  atribusi; legal code: `https://creativecommons.org/licenses/by/4.0/legalcode`.

Kandidat ini kecil, tidak memuat manusia, dan cukup kaya untuk rank,
conditioning, OLS, kontras, diagnostik, transformasi, serta interaksi. Gate
freeze harus membandingkan XLS asli dengan CSV generatif, membekukan header
dan unit, serta mencatat bahwa hubungan strength sangat nonlinear sehingga
model aditif adalah aproksimasi yang wajib diaudit.

Alternatif utama adalah UCI *Combined Cycle Power Plant*:
`https://archive.ics.uci.edu/dataset/294/combined%2Bcycle%2Bpower%2Bplant`,
DOI `https://doi.org/10.24432/C5002N`, CSV
`https://archive.ics.uci.edu/static/public/294/data.csv`, dan metadata
`https://archive.ics.uci.edu/api/dataset?id=294`. Haknya juga CC BY 4.0.
Balik ke kandidat ini bila ukuran sampel besar dan empat prediktor lebih sesuai
daripada diagnostik nonlinear Concrete. Jangan menggabungkan lima shuffle
worksheet pada arsipnya, dan bekukan perbedaan nama target `PE`/`EP`.

## CP02 — kandidat utama perbandingan Bayesian–frequentist

Kandidat utama adalah agregat *Greater sage-grouse nesting propensity* Dryad:

- dataset/DOI: `https://datadryad.org/dataset/doi%3A10.5061/dryad.573n5tbf3`
  dan `https://doi.org/10.5061/dryad.573n5tbf3`;
- versi 3 / version ID `268230`, 2023-12-08;
- CSV `nest_propensity.csv`, file ID `2765112`:
  `https://datadryad.org/api/v2/files/2765112/download`, 285 byte, publisher
  SHA-256 `8790b4dfa29a5b39228e758e40e02cbb48612c38b8440020aa108c85ca0673c4`;
- README file ID `2765118`:
  `https://datadryad.org/api/v2/files/2765118/download`, 4.139 byte, publisher
  SHA-256 `43a53f9a451a4030b8d3edb2a7517c48863d8ef23d7ae4986d15c20d7f8f5459`;
- metadata versi `https://datadryad.org/api/v2/versions/268230` dan inventory
  `https://datadryad.org/api/v2/versions/268230/files`;
- metadata menyatakan CC0-1.0; panduan reuse Dryad
  `https://datadryad.org/help/guides/reuse` dan legal code
  `https://creativecommons.org/publicdomain/zero/1.0/legalcode`;
- data adalah hitungan agregat satwa liar: sukses `No_nests`, trial salah satu
  dari dua denominator yang harus dipilih sebelum analisis, group tipe
  transmitter, dan waktu tahun.

Gate freeze harus menyelesaikan perbedaan README “enam kolom” versus lima nama
yang dijelaskan, memilih denominator primer sebelum melihat hasil, memakai
denominator kedua hanya untuk sensitivitas, dan menguji identifiability model
dispersion pada jumlah sel yang kecil. Tidak ada microdata individual yang
boleh diimpor dari deposit yang sama.

Alternatif utama adalah agregat *Wood duck population sex ratios* Dryad,
dataset `https://datadryad.org/dataset/doi%3A10.5061/dryad.rbnzs7hkf`, version
ID `285121`, workbook file ID `3021876`, dan README file ID `3021880`; hak
CC0-1.0. Balik ke kandidat ini bila CP02 memerlukan covariate tingkat situs
atau total trial lebih besar dan pipeline dapat membekukan worksheet/range,
tipe, blank, serta konversi XLSX secara deterministik.

## Gate penerimaan

Sebelum freeze, bukti primer harus berlaku pada aset persis dan membolehkan
unduh, redistribusi, serta derivatif. Catat versi, URL, atribusi, waktu ambil,
MIME/encoding, byte, dan SHA-256; simpan raw byte serta kamus tanpa mutasi;
hasilkan CSV bersih hanya lewat skrip deterministik dan ledger transformasi.
Tolak kandidat bila hak, privasi, schema, identifiability, atau reproduksi
offline gagal. Hak dataset selalu tetap terpisah dari CC BY-SA 4.0 pendamping.
