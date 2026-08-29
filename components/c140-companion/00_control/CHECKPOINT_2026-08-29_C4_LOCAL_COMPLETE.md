# Checkpoint C4 lokal lengkap — set penguasaan studi mandiri

Tanggal: 2026-08-29

C4 menambahkan tepat tujuh set penguasaan orisinal `MS00`–`MS06` pada batas
kumulatif C3. C1, C2, dan C3 tidak diganti. Setiap dokumen berbahasa `id-ID`
dan berlisensi CC BY-SA 4.0, dengan delapan masalah `P01`–`P08`; semua masalah
memiliki metadata stabil, dua petunjuk bertahap, jawaban singkat, dan solusi
lengkap. Sumber memuat 34 dokumen / 683.211 byte, 1.113 entitas backend, 1.424
relasi, dan 114 masalah terselesaikan (13 set penguasaan x 8 ditambah 10
masalah `CA01`).

Audit awal dan audit matematis independen atas seluruh 56 masalah menemukan
delapan koreksi yang telah diterapkan dan diverifikasi ulang:

1. `MS00-P02` memakai `P(-)=0,8915` dan `P(D|-)=0,00056085`.
2. `MS00-P05` kini menyatakan bahwa sepuluh percobaan adalah sepuluh pertama
   dari barisan Bernoulli independen tak hingga, sehingga `G` boleh melebihi
   sepuluh.
3. `MS04-P08` memberi syarat MLE hingga yang tepat: dengan `k` pengamatan
   positif, MLE unik ada tepat bila `k>n/2`; untuk `k<n/2` likelihood tak
   terbatas dan untuk `k=n/2` supremum hanya dicapai pada batas tak hingga.
4. `MS05-P07` menggunakan `0,05^(-1/10)=1,34928285` dan endpoint atas
   `1,07942628` untuk `M=0,8`.
5. `MS01-P01` memakai simbol ukuran sampel `s` dan realisasi maksimum `v`,
   sehingga densitas umum adalah `s(s-1)(v-m)^(s-2)`.
6. `MS02-P03` membatasi klaim minimaks pada kelas linear `T_a=a Xbar` dan
   menjelaskan bahwa estimator terpotong memperbaiki risiko global.
7. `MS03-P02` memasukkan faktor `n^t/t!` yang diperlukan agar bagian
   ternormalisasi benar-benar merupakan massa Poisson `(n lambda)`.
8. `MS06-P02` memakai p-value dua sisi `t_15` yang benar, `0,063945`.

Audit yang sama juga memperjelas penyebab nonregularitas endpoint Bernoulli
dan menghapus satu kalimat ganda pada `MS04-P08`. Semua hasil numerik dan
aljabar lain pada 56 masalah dinyatakan lulus.

Pemeriksaan struktur terbatas terhadap tujuh sumber menemukan 42 anchor dan
delapan metadata masalah per dokumen, tanpa CRLF atau token cacat lama. Replay
deterministik luring:

```text
python -B components/c140-companion/scripts/build_companion.py --write --c4
python -B components/c140-companion/scripts/build_companion.py --check-only --c4
python -B components/c140-companion/scripts/qa_companion.py --write --c4
python -B components/c140-companion/scripts/qa_companion.py --check-only --c4
```

Keempat perintah lulus dengan `browser_processes_used=false` dan
`network_access=false`. Build receipt adalah
`build/C4_BUILD_RECEIPT.json`, 34 dokumen / 64 HTML / 3.024.784 byte,
1.113 entitas / 1.424 relasi / 359.500 byte backend; receipt SHA-256
`c21aecda780cf8e56eb82a41d19b9b0a112e81caf583f38041a5d9fd4ffc0ac1`.
Manifest HTML SHA-256 adalah
`629870245f726b01534c09f7e595e8a15cf11015a63280c0a16b056ce7cb4178` dan
manifest backend SHA-256 adalah
`86190eddcd4cc4e99ed3adfc22a3d8391934fb940f5ec1ea1572a532df6b44e3`.
QA receipt `build/C4_QA_RECEIPT.json` memiliki SHA-256
`dfadcc6338ad44d9dadd13fa2f7ef19d9b9e19e428f25f3fe7607852bfa8e2e7`.
Receipt QA mencatat 1.057 anchor HTML unik, 1.492 tautan lokal, dan 28 tautan
eksternal; semua gate struktur, ID, tautan, aset, hak, dan privasi lulus.

Hash tujuh sumber baru:

| Berkas | Byte | SHA-256 |
|---|---:|---|
| `O006-C140-CMP-MS00.md` | 20.724 | `1d6259f26774eaeb7974e23b0afbd3a9446944eb3d578bc75fe0363f675ff517` |
| `O006-C140-CMP-MS01.md` | 21.213 | `4b4b06a89bb0c102f6791986df9e03311a823a502d3894026e04916aa2889486` |
| `O006-C140-CMP-MS02.md` | 21.504 | `9df595ecf53fd185e7ca4fc80303dade053a23a5d6f0131d0db16ed6935f0c4d` |
| `O006-C140-CMP-MS03.md` | 23.912 | `aee8669c5541bec5268ad9e39cadbc339e12a12ba9776fc8a572905ac702dc36` |
| `O006-C140-CMP-MS04.md` | 24.398 | `fbedd105069bd7aba557782cef312b460a9fc82b2ec93056cf78d8f47afbb0ce` |
| `O006-C140-CMP-MS05.md` | 22.458 | `5e51d15adf9526b4ac3f748ad6a5f543ddb768ef9701b81d0d24d7c351366d9b` |
| `O006-C140-CMP-MS06.md` | 20.006 | `da59be497308fb699cf82d6ec71b56136cee7d1818be4aad5ee766f3fa7c0f64` |

Paket preservasi C4 lulus contract/write/check replay dan audit independen.
Paket memuat 57 berkas / 93.850.993 byte: seluruh 49 berkas C3 / 92.476.057
byte dipertahankan identik dan delapan berkas C4 ditambahkan pada urutan
50–57. Receipt paket 34.142 byte memiliki SHA-256
`45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f`.
Arsip pembaca, source/backend, dan bukti QA masing-masing memuat 65, 85, dan
20 entri serta lulus CRC, inventaris, hak, privasi, dan replay deterministik.

Kandidat Pages kumulatif memuat 188 berkas / 22.437.587 byte; manifest
SHA-256 `fdd057c53c7bb0a092d8ee3499b9116b9219463034c0426b5373687ba9200f90`
dan receipt SHA-256
`ef92d1871a85336890fc48798ad50d170d4de18505cc5ee8c441621fa2473d31`.

Materi C4 adalah penutupan studi mandiri parsial, bukan penyelesaian C140.
Asesmen `CA02`–`CA04` dan dua capstone belum diproduksi. Batas berikutnya
adalah memublikasikan paket pada lineage GitHub/Zenodo yang sama, membaca
balik semua byte publik secara anonim, lalu melanjutkan asesmen dan capstone.
Tidak ada
kontak upstream selama batch ini. Larangan permanen browser tetap berlaku:
tidak ada Chrome, Chromium, Playwright, Puppeteer, Electron, WebView, atau
proses browser lain yang boleh dijalankan.

Provenans produksi: `OpenAI Codex gpt-5.6-sol, Ultra`.
