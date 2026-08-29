# Checkpoint C3 lokal lengkap — perbandingan Bayesian–frequentist

Tanggal: 2026-08-29

C3 menambahkan `D012`, `D013`, `SIM006`, dan `MS11` pada C1+C2 tanpa
mengubah receipt historisnya. Batas kumulatif sekarang memuat 27 dokumen /
528.082 byte sumber / 763 anchor / 251 referensi isi. Enam set penguasaan dan
`CA01` memuat 58 masalah; setiap masalah mempunyai metadata, sedikitnya dua
petunjuk, jawaban singkat, dan solusi lengkap.

`SIM006` membedakan cakupan parameter-tetap dari kalibrasi rata-rata-prior pada
model Beta–binomial. Lima berkas generated C3 memuat 18.273 byte; receipt
simulasi SHA-256 adalah
`c7f176380b2e30b9931cc44bcc2e39bb541559030cf65b1c41f32045c13b1040`.
Enam simulasi kumulatif sekarang menutup seluruh keluarga eksperimen minimum
pada workflow: konvergensi/bias/varians, cakupan, size/power, delta/bootstrap,
likelihood reguler/nonreguler, regresi, dan kalibrasi Bayesian.

Pembaca HTML browser-free memuat 57 berkas / 2.713.731 byte; manifest
SHA-256 `18b3ab09539eee0baa355dcb7f7edc2cec00f0960c5508a9419bf2bde7bb1273`.
Backend memuat 812 entitas / 1.084 relasi / 269.101 byte; manifest SHA-256
`2c5b84d662713a037b512a6751dd9e8e7eb2504a69141d6268993db859e83d66`.
Build receipt SHA-256 adalah
`79661673ad7f4d74eff997cebd6fca1f46d2a74cbab5930147ca109762ef37ca`;
QA receipt SHA-256 adalah
`6f53a1f54d3a1b3e23b874a3c13adda9726bc0a8456d2fb4a8315d11912f72d7`.
Mode write/check-only lulus byte-identik.

Audit matematika independen memeriksa semua derivasi D012/D013, angka
Beta–binomial/Normal/Bayes factor, semua delapan solusi MS11, dan seluruh
angka SIM006. Temuannya diperbaiki: hipotesis keterukuran kernel, definisi
lengkap titik ujung Clopper–Pearson, syarat transformasi ekor kontinu,
hipotesis filtrasi awal martingale, encoding garis nonwarna, serta terminologi
id-ID. Audit integrasi menutup direktori generated terhadap manifest,
memverifikasi ID receipt dari output nyata, dan memperkeras larangan
browser/jaringan/proses. Tidak ada temuan matematis tersisa pada MS11.

Koleksi Pages kumulatif memuat 181 berkas / 22.126.534 byte; manifest SHA-256
`205b1e3ad157d1967f26582ab22bfc0a3c73c2defaf812dbf16a66df33951b98`
dan receipt SHA-256
`b2b42257757950b0baf7240787b36d48ca06c353f35a860b0a3bcf2d8c9e82f5`.
Tidak ada Chrome, Chromium, Playwright, Puppeteer, Electron, WebView, Ace,
browser lain, atau jaringan pada build/QA ini.

Semua batas teori dan simulasi minimum pendamping kini tertutup, tetapi C140
belum lengkap. Tujuh set penguasaan `MS00`–`MS06`, tiga asesmen kumulatif
`CA02`–`CA04`, dan dua capstone masih harus diproduksi. Aksi berikutnya adalah
memublikasikan checkpoint C3 pada lineage GitHub/Zenodo yang sudah ada,
membaca balik byte publik secara anonim, lalu melanjutkan materi pembelajaran
mandiri tersebut.

Paket kumulatif final lokal memuat 49 berkas / 92.476.057 byte: seluruh 41
berkas C2 / 91.249.199 byte dipertahankan identik dan delapan berkas C3 /
1.226.858 byte ditambahkan. Receipt paket 30.151 byte memiliki SHA-256
`d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637`.
Audit independen menemukan lalu menutup satu celah lingkup lisensi pada dua
skrip reproduksi tingkat repositori: source/backend ZIP kini menyertakan
`COLLECTION_LICENSE.md` yang byte-identik dengan lisensi koleksi. Replay paket,
CRC, inventaris, hak, privasi, dan checksum lulus tanpa browser atau jaringan.
