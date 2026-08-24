# Catatan penerjemahan bagian C

## Terminologi

- `random variable` diterjemahkan sebagai **peubah acak**, mengikuti bagian terdahulu.
- `probability density function`, `probability mass function`, dan `cumulative distribution function` diterjemahkan sebagai **fungsi kepadatan peluang (pdf)**, **fungsi massa peluang (pmf)**, dan **fungsi distribusi kumulatif (cdf)**.
- `mean` untuk peubah acak diterjemahkan sebagai **nilai harapan**; `standard deviation` sebagai **simpangan baku**; dan `standard error` sebagai **galat baku**.
- `estimator` diterjemahkan sebagai **penaksir**, sedangkan `point estimation` dan `interval estimation` tetap **estimasi titik** dan **estimasi interval**, selaras dengan navigasi yang sudah diterjemahkan.
- `hypothesis testing` diterjemahkan sebagai **uji hipotesis** dan `data-generating process` sebagai **proses pembangkitan data**.

## Cacat atau kejanggalan sumber yang teridentifikasi

- S0359 memuat salah ketik `thougth`; terjemahan memakai makna yang dimaksud, “diperkirakan”.
- Pada Contoh 1, rumus setelah kata `and` hanya menampilkan `P(P′|C′)` tanpa `=0.9`, padahal angka 90% dinyatakan dalam soal dan diperlukan untuk menyimpulkan `P(P|C′)=0.1`. Nilai yang hilang berada dalam matematika sumber dan tidak diubah oleh berkas pemetaan ini.
- S0368 memuat tanda kutip penutup yang tidak berpasangan setelah `get`; terjemahan menormalkannya menjadi titik dua.
- S0370 mengandung tata bahasa Inggris yang rusak (`the actual amount of coffee is dispensed is ...`). Selain itu, satuan varians ditulis `oz`, bukan `oz²`; terjemahan mempertahankan nilai dan satuan sumber sambil mencatat masalah dimensinya di sini.
- Pada Contoh 3, rumus mendefinisikan `f(w)` tetapi cabang-cabangnya menggunakan `x`. Dalam penyelesaian nilai harapan, batas evaluasi juga ditulis `x^3|_0^4`, sedangkan hasilnya sesuai dengan batas atas 2. Keduanya berada dalam matematika sumber dan tidak diubah.
- S0398 menyebut `pdf` untuk peubah acak diskret, sedangkan butir solusi dengan benar menyebut `pmf`. Terjemahan menggunakan **pmf** sebagai perbaikan terminologis berkeyakinan tinggi.
- Blok solusi Contoh 5 merender kata `Therefore,` sebagai blok kode; teks tersebut tidak termasuk dalam rentang segmen yang ditugaskan.
- S0422 membocorkan penanda komentar sumber `%Imagine that`; terjemahan menghapus `%` dan mempertahankan kalimat yang dimaksud.
- Rumus persentil memuat akhiran ordinal Inggris `30^{th}`. Rumus dipertahankan tanpa perubahan; teks di sekelilingnya disusun sebagai “persentil [rumus] dari …”.
