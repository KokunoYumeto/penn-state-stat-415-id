# Checkpoint C5 publik lengkap — penutupan O006/C140

Tanggal: 2026-08-31

## Batas isi dan build final

Pendamping C140 selesai sebagai 39 dokumen sumber id-ID / 1.145.637 byte,
dengan 146 masalah yang masing-masing memiliki petunjuk bertahap, jawaban
singkat, dan solusi lengkap. Pembaca HTML memuat 135 berkas / 15.757.728 byte.
Backend memuat 117 berkas / 13.568.809 byte, 1.523 entitas, dan 1.949 relasi.
Receipt build dan QA final mempunyai SHA-256
`cc9e6002edcbb5adbe5a348233fb73f5588728a4fbc330a93061c1f18807f372`
dan `aef36e757fca2d3ad1593087af12a5102120697f16715acf210248d94d296bfd`.

Identitas sumber, paket preservasi, dan rekonstruksi bersih telah dicocokkan
secara eksak. Paket sumber/backend/data/hak
`release/16_C140_COMPANION_C5_SOURCE_BACKEND_DATA_RIGHTS.zip` mempunyai
SHA-256 `4de938596957e2116d6292f4a5e493a98212e7f9d1c49de32ae6e57c5b746deb`;
receipt paket final mempunyai SHA-256
`4fe5a6686d6c78e8320edc00d274089a9f3419ac175b8647706763ca77d49a02`.
Reproduksi dari paket sumber yang baru diekstrak lulus hidrasi, build, dan QA
statis dengan identitas final yang sama; buktinya tercatat di
`00_control/C5_CLEAN_SOURCE_RECONSTRUCTION_2026-08-31.json`.

## Linux CI dan Pages

Replay Linux untuk CP01 dan CP02 menjalankan kembali seluruh asersi ilmiah
produsen asli. Pemeriksaan portabilitas membatasi toleransi hanya pada nilai
numerik floating-point yang terdampak pustaka numerik; token diskret, struktur,
jumlah baris, header, identitas sumber/data, dan binding manifest tetap eksak.
Kedua replay numerik lulus, sebagaimana dicatat dalam
`00_control/C5_LINUX_NUMERICAL_REPLAY_2026-08-31_SUCCESS.json`.

Workflow Pages [`33405870018`](https://github.com/KokunoYumeto/penn-state-stat-415-id/actions/runs/33405870018)
lulus pada commit deployment
`903d54c0971d3c14ec8f6fa0961136b881a73b82`. Koleksi Pages kumulatif memuat
259 berkas / 35.170.536 byte dengan SHA-256 manifest
`43fad46f62f6925e39f5c24a7d0182a26b2e96e884f5e2b0d7f79be28cf64249`.
Pembacaan kembali anonim mencocokkan seluruh 259 berkas. Receipt Pages
`00_control/GITHUB_PAGES_RECEIPT_2026-08-31_C140_COMPANION_C5.json` berukuran
103.239 byte dan mempunyai SHA-256
`2230f83f946c83d5a9633cdc3f4b1c5af72069634ff72586768a4f8f08a3eae6`.

Pembaca publik: https://kokunoyumeto.github.io/penn-state-stat-415-id/.

## Preservasi publik

Rilis GitHub
[`v2026.08.31.c140-companion-c5`](https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.31.c140-companion-c5)
dan versi Zenodo [`10.5281/zenodo.22208527`](https://doi.org/10.5281/zenodo.22208527)
masing-masing memuat 65 berkas / 134.904.267 byte. Seluruh aset pada kedua
tujuan telah dibaca kembali secara anonim dan cocok byte/SHA-256; 57 aset yang
diwarisi dari C4 tetap byte-identik.

Target donor *Random* terkini berukuran 60.900 byte dengan SHA-256
`18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197`
dan juga telah dicocokkan melalui pembacaan publik, tercatat dalam
`00_control/RANDOM_DONOR_REFINEMENT_PUBLIC_READBACK_2026-08-31.json`.

## Kondisi terminal

Komponen Penn STAT 415, donor kelengkapan *Random*, dan pendamping asli C140
semuanya lengkap, terbangun, terindeks, dan terpublikasi. Tidak ada proses
browser yang digunakan. Tidak ada pesan upstream yang dikirim; keputusan
`tidak ada laporan baru` tercatat dalam
`00_control/UPSTREAM_REPORT_DISPOSITION_2026-08-31.md`. Tidak ada pekerjaan
O006/C140 yang tersisa pada batas ini.
