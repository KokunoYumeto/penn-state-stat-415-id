# Catatan terjemahan Lesson 02 — bagian B

## Cakupan

- Segmen: `O006-PSU-003-S0109` sampai dengan `O006-PSU-003-S0216` (108 kunci berurutan).
- Sumber konteks: `source/normalized/en-US/Lesson02.html`.
- Berkas segmen: `working/lesson02_segments.csv`.
- Glosarium otoritatif: `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`.

## Keputusan terminologi dan konteks

- `estimator` diterjemahkan sebagai **penduga**; `estimation` sebagai **pendugaan**; dan `unbiased estimator` sebagai **penduga tak bias**. `biased estimator` diterjemahkan sebagai **penduga berbias** agar berbeda jelas dari `bias` sebagai nomina.
- `expectation`/`expected value` diterjemahkan sebagai **nilai harapan**, sedangkan `mean` sebagai **rataan**.
- `random variable` diterjemahkan sebagai **peubah acak**, `random sample` sebagai **sampel acak**, `probability density function` sebagai **fungsi kepadatan peluang**, `chi-square` sebagai **khi-kuadrat**, dan `degrees of freedom` sebagai **derajat kebebasan**.
- Fragmen `S0195`–`S0198` dan `S0201`–`S0205` disusun agar tetap gramatikal ketika simpul matematika dan penekanan terlindungi disisipkan kembali: “memang *selalu* merupakan …” dan “ternyata *bukan* penduga …”. Semua segmen tetap bernilai nonkosong.
- Tanda baca pada `S0162` dinaturalkan menjadi titik dua karena kalimat tersebut memperkenalkan persamaan tampilan.

## Cacat sumber berkeyakinan tinggi

- Pada simpul matematika `O006-PSU-003-M0062` dalam Contoh 2.5, sumber menuliskan `\hat{p}_1=X_1/n` padahal `n=3`; Contoh 2.6 dan derivasi berikutnya menggunakan `\hat{p}_1=X_1/10`. Ini merupakan ketidakkonsistenan definisi. Matematika sumber tidak diubah.
- Pada konteks `S0130`–`S0132`, simpul `O006-PSU-003-M0075` menyatakan `E(X)=p` untuk peubah acak binomial, tetapi simpul berikutnya menyatakan `Var(X)=np(1-p)` dan derivasi memakai `E(X_1)=10p`. Bentuk umum yang konsisten adalah `E(X)=np`. Matematika sumber tidak diubah.
- Pada simpul `O006-PSU-003-M0102`, ekspansi kuadrat pada baris pertama memiliki pangkat dua tambahan di luar tanda kurung dan tidak mencantumkan penjumlahan pada ekspansi tersebut; baris berikutnya juga kehilangan faktor `1/n` pada suku silang. Identitas yang hendak ditunjukkan tetap jelas dari konteks, dan matematika sumber tidak diubah.
- Kalimat sumber pada `S0172`–`S0173` berbunyi “The estimator for `\hat{\sigma}^2` …”; secara matematis `\hat{\sigma}^2` adalah penduganya, bukan parameter yang diduga. Terjemahan dinaturalkan menjadi “Penduga `\hat{\sigma}^2` merupakan …” tanpa mengubah simpul matematika.

## Status

- Parse JSON: lulus.
- Jumlah kunci: 108; jumlah yang diharapkan: 108; kunci hilang: 0; kunci tambahan: 0; nilai kosong/nonstring: 0; urutan kunci: sesuai.
- SHA-256 sumber HTML: `efb5376be5d16d085bbc8d668b31839e0270c7a37e3a2abd52cd742a1410e646`.
- SHA-256 berkas segmen: `00e1e2a63b936c214ffd8ec6613268b0704d24b2552a8f44fe3b27b841edd7ec`.
- SHA-256 glosarium: `a46f73d6ae1030e4bc9231233e1c0895f770d0f63c5195c4339d912e7af192d6`.
- SHA-256 JSON terjemahan: `bf884c010e53acc010bf33a45218004655231edc851bb890ec462bb965b476a3`.
- Tidak ada pekerjaan yang belum terselesaikan dalam cakupan bagian B.
