# Catatan penerjemahan bagian B — Lesson 00

## Batas

- Segmen: `O006-PSU-001-S0193`–`O006-PSU-001-S0355` (163 segmen).
- Bagian: distribusi bivariat, distribusi bersyarat, distribusi jumlah beberapa peubah acak, dan fungsi acak yang berkaitan dengan distribusi normal.
- Semua rumus, simbol, dan pengenal berada di luar fragmen teks yang ditugaskan dan tidak diubah.

## Terminologi

- *probability* → **peluang**; *distribution* → **distribusi**.
- *random variable* → **peubah acak**; *support* → **himpunan dukungan**.
- *joint / marginal / conditional* → **bersama / marginal / bersyarat**.
- PMF/PDF → **fungsi massa peluang / fungsi kepadatan peluang**, dengan singkatan sumber dipertahankan sebagai PMF/PDF.
- *independent / dependent* → **saling bebas / saling bergantung**.
- *mean / variance* → **rataan / varians**; *sample mean / sample variance* → **rata-rata sampel / varians sampel**.
- *corollary* → **akibat**; *degrees of freedom* → **derajat kebebasan**.
- *Chi-square distribution* → **distribusi khi-kuadrat**; *Central Limit Theorem* → **Teorema Limit Pusat**.
- *approximately normally distributed* → **mengikuti distribusi normal secara hampiran**.

## Cacat sumber yang tidak boleh diperbaiki diam-diam pada rumus

1. Definisi 11 memuat salah ketik “random variabled”; terjemahan menggunakan bentuk semantis yang benar, **peubah acak diskret**. Rumus normalisasi PMF bersama pada sumber juga memiliki tanda penjumlahan ganda yang janggal.
2. Definisi 12 menyatakan syarat kepadatan sebagai ketaksamaan ketat; kepadatan semestinya boleh bernilai nol. Formula sumber harus tetap dibekukan dan koreksi derivatif dicatat terpisah.
3. Definisi 13 dan 14 menggunakan pengenal HTML sumber yang sama, `def-margpmf`. Edisi turunan memerlukan ID target unik dengan relasi alias ke kedua kemunculan sumber.
4. Segmen S0253 memperbaiki salah ketik “denstiy” hanya pada prosa terjemahan.
5. S0285 mengandung pengulangan rusak (“helpful There are some helpful”); terjemahan merapikan kalimat tanpa mengubah isi matematis.
6. Teorema 3, 4, dan 6 menyebut “random sample” tetapi sekaligus menggunakan parameter berindeks yang dapat berbeda. Terjemahan mempertahankan klaim sumber sebagai **sampel acak**; perbaikan matematis menjadi “peubah-peubah acak yang saling bebas” harus diperlakukan sebagai koreksi derivatif eksplisit.
7. Teorema 7 menyebut rataan `mu_i`, tetapi rumus distribusi kombinasi linear memakai `mu` tanpa indeks. Rumus tidak disentuh di berkas terjemahan ini.
8. Teorema 8 menulis penyebut varians sampel sebagai `n_1`, sedangkan hasil khi-kuadrat berikutnya memakai `n-1`; rumus tidak disentuh di sini.
9. Definisi distribusi t memuat “follows at”; terjemahan memperbaiki tata bahasa menjadi **mengikuti distribusi t** tanpa mengubah formula.

