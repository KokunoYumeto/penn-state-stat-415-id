# Checkpoint C4 publik lengkap — penutupan set penguasaan

Tanggal: 2026-08-29

C4 mempertahankan seluruh C3 secara byte-identik dan menambahkan tepat tujuh
set penguasaan orisinal `MS00`–`MS06`. Batas kumulatif adalah `D001`–`D013`,
`SIM001`–`SIM006`, `MS00`–`MS12`, `CA01`, dan indeks: 34 dokumen sumber /
683.211 byte, 114 masalah terselesaikan, 64 berkas pembaca / 3.024.784 byte,
1.113 entitas backend, dan 1.424 relasi. Audit matematika atas seluruh 56
masalah C4 dan build/QA statis lulus. Receipt build dan QA mempunyai SHA-256
`c21aecda780cf8e56eb82a41d19b9b0a112e81caf583f38041a5d9fd4ffc0ac1`
dan `dfadcc6338ad44d9dadd13fa2f7ef19d9b9e19e428f25f3fe7607852bfa8e2e7`.

Paket preservasi deterministik memuat 57 berkas / 93.850.993 byte. Seluruh 49
berkas C3 / 92.476.057 byte cocok byte demi byte; delapan berkas C4 /
1.374.936 byte ditambahkan pada urutan 50–57. Receipt paket 34.142 byte
mempunyai SHA-256
`45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f`.

## GitHub dan Pages

Commit isi publik adalah
`9b10b3e04b451232b1233d0b35cf31c3860d63db`. Pembacaan kembali immutable raw
commit mencocokkan 62 berkas berubah / 1.997.776 byte. Workflow Pages
`33264397424` lulus; dua pemeriksaan statis tanpa kredensial mencocokkan
188/188 berkas / 22.437.587 byte. Receipt Pages 69.790 byte mempunyai SHA-256
`5e002a9f7926def73034a6d18686d36a257b7dd9daaf6fa6aa12db9fe764a012`.

Rilis GitHub `379047752` memakai tag
`v2026.08.29.c140-companion-c4`, objek tag beranotasi
`1dd397eeb0d717046e4f31a5d65abe97c3c9567b`, dan mengarah tepat ke commit
isi C4. Publisher idempoten dan verifier langsung tanpa API/kredensial
mencocokkan 57/57 aset / 93.850.993 byte. Receipt transaksi, pembacaan anonim,
dan pembacaan langsung mempunyai SHA-256
`6dd0611b227940b2a63c1fc5652c4d7d585e1f522f3a07215ac7f39348e649c8`,
`efd537d327dcd6d4a02a74c1194696c860f8f1273b88cbd6db920c81faa9598c`,
dan `53235cdaf793eb5600256519eedd4becab85867e3a4a94377c39871a7708ea2f`.

Rilis publik:
`https://github.com/KokunoYumeto/penn-state-stat-415-id/releases/tag/v2026.08.29.c140-companion-c4`.

## Zenodo

Versi publik berada pada record `22164344`, DOI
`10.5281/zenodo.22164344`, di dalam concept record `22077422` / concept DOI
`10.5281/zenodo.22077422`. Hak komponen tetap terpisah dan akses tetap publik
`other-open`. Pembacaan anonim dan verifier langsung mencocokkan seluruh 57
berkas / 93.850.993 byte. Receipt publikasi, pembacaan publik, pembacaan
langsung, dan audit lineage mempunyai SHA-256
`573f155ec965e6849ed0fff0deb9a04b6ab90c38f6e34deccf0999f0fd4cf30a`,
`fe92ec27c63d8af29ea30bf46977fd8694e6febcdc3375db29f8bf2db60acf8d`,
`a8c01aa346b27d49468a41be230289c8c761b8fa94d041c92ab1467c640969d1`,
dan `c02a40387634f79f0f784ed4c8e4ec4b849f5e6e88ec995fbe851914f877effb`.
Audit akhir menemukan tepat satu versi C4 publik yang cocok dan nol draf.

Versi publik: `https://doi.org/10.5281/zenodo.22164344`.

Tidak ada Chrome, Chromium, Playwright, Puppeteer, Electron, WebView, browser
lain, atau kontak upstream selama build, publikasi, maupun readback. Provenans
tetap `OpenAI Codex gpt-5.6-sol, Ultra`.

C4 selesai. C140 belum selesai. Batas aktif berikutnya adalah C5 pada
`C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md`: `CA02`, `CA03`, `CA04`, `CP01`,
dan `CP02`, diikuti build/QA/publikasi final.
