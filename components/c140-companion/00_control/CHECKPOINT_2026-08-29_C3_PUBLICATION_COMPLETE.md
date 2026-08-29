# Checkpoint C3 publikasi lengkap — pendamping C140

Tanggal: 2026-08-29

Checkpoint ini menutup publikasi deterministik C3 tanpa mengubah batas C1/C2.
Ruang lingkup kumulatif adalah `D001`–`D013`, `SIM001`–`SIM006`, `MS07`–`MS12`,
`CA01`, dan indeks: 27 dokumen, 528.082 byte sumber, 763 anchor, 251
referensi isi, enam simulasi, dan 58 masalah yang masing-masing memiliki
metadata, petunjuk bertahap, jawaban singkat, serta solusi lengkap.

## Bukti lokal dan hak

- HTML luring: 57 berkas / 2.713.731 byte; manifest
  `18b3ab09539eee0baa355dcb7f7edc2cec00f0960c5508a9419bf2bde7bb1273`.
- Backend: 812 entitas / 1.084 relasi / 269.101 byte; manifest
  `2c5b84d662713a037b512a6751dd9e8e7eb2504a69141d6268993db859e83d66`.
- Build, QA, dan simulasi C3 masing-masing ber-hash
  `79661673ad7f4d74eff997cebd6fca1f46d2a74cbab5930147ca109762ef37ca`,
  `6f53a1f54d3a1b3e23b874a3c13adda9726bc0a8456d2fb4a8315d11912f72d7`, dan
  `c7f176380b2e30b9931cc44bcc2e39bb541559030cf65b1c41f32045c13b1040`.
- Paket preservasi: 49 berkas / 92.476.057 byte; receipt paket 30.151 byte,
  SHA-256 `d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637`.
  Semua 41 berkas C2 dipertahankan byte-identik; `COLLECTION_LICENSE.md`
  menutup hak skrip reproduksi tingkat koleksi.
- Semua konten orisinal pendamping tetap CC BY-SA 4.0. Hak Penn State dan
  donor *Random* tetap dipisahkan. Provenans: `OpenAI Codex gpt-5.6-sol, Ultra`.

## GitHub dan Pages

Commit konten `1c8f97f02e9bccfdbe4df91dd77af969cd6e33d6` publik; 68 blob yang
berubah (1.676.888 byte) cocok dengan URL raw anonim. Pages run `33251730934`
berhasil; dua replay statis anonim cocok dengan 181 berkas / 22.126.534 byte.
Receipt Pages SHA-256 adalah
`9beb5dae3023d6549f6f5ad52ee6e472e1a001bc035d09d1cfbc4091585b1007` dan
receipt readback commit adalah
`3dfc01c54aa7812a4ea77a09bef667e3cddf72d2e2134c416e326620ca12c609`.

Rilis GitHub `378973936`, tag `v2026.08.29.c140-companion-c3`, menunjuk ke
commit tersebut. Receipt publikasi adalah
`62c58f7d5de7eb07e459fcfdf7d4d2450801cda57d68912607de21353a7cf4e4`, receipt
readback langsung tanpa API adalah
`84a09172a8a17be2a9aaa991db40b00fd2a4fdb88581277ad3e667b7e4e9043b`; seluruh
49 aset / 92.476.057 byte cocok dua kali.

## Zenodo

Versi publik pada konsep `22077422` adalah record `22161363`, DOI
`10.5281/zenodo.22161363`, versi `2026.08.29.c140-companion-c3`, akses terbuka.
Receipt publikasi ber-hash
`999dc33490eb77c4759857f7fb8ac3baf8919bde5780dc17b4959657dbfe98df`.
Replay awal dan replay langsung independen sama-sama cocok dengan seluruh 49
berkas; receipt replay langsung yang paling lengkap (metadata MD5, ukuran, dan
SHA-256) ber-hash
`55f607cc41f6a0a8ad1355d1a46aa3d22f6b7f27a9224f986fd6f3f136f29ce2`.
Replay terakhir memakai HTTPS anonim berjarak dan retry terbatas, tanpa token,
API deposisi, browser, Git, atau proxy. Audit lineage ber-hash
`a3d3c2db965d7dea065bbb849bebac521a37fbe4c2c6aeca416c6019b5163d6d` menemukan
satu versi yang dikirim dan nol draf tersisa.

Tidak ada proses Chrome/Chromium/Playwright/Puppeteer/Electron/WebView/Ace yang
dijalankan pada build, QA, atau replay ini. Tidak ada pesan upstream yang
dikirim.

## Status dan aksi berikutnya

C3 sudah selesai dan terbit, tetapi C140 belum selesai. Aksi produksi berikutnya
adalah membuat `MS00`–`MS06`, lalu `CA02`–`CA04`, kemudian dua capstone;
integrasikan setiap batch ke backend/HTML dan lakukan satu replay kumulatif pada
batas bermakna. Jangan membuka ulang C1/C2/C3 tanpa cacat yang terbukti.
