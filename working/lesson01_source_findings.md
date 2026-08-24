# Temuan sumber dan keputusan istilah — Lesson 01

## Batas pemeriksaan

Pemeriksaan dibatasi pada `authority/upstream/stat415/Lesson01.html`, glosarium kanonis `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`, dan pembaca Indonesia Lesson 00 yang sudah ada untuk konsistensi label. Tidak ada berkas sumber atau kanonis yang diubah.

## Cacat sumber berkeyakinan tinggi

1. **Indeks kejadian keberhasilan berhenti pada 5 meskipun eksperimen memiliki 6 percobaan.**
   - Anchor: `#exm-orderstats`, subbagian `#solution-1`.
   - Konteks sumber: `If the event {X_i<1}, i=1, 2, ..., 5 is considered a “success,” ... Z = the number of successes in six mutually independent trials`.
   - Karena keenam pengamatan dapat menjadi keberhasilan, indeks harus mencakup `i=1,2,...,6`.
   - Cacat yang sama berulang pada `#solution-2`: `If the event {X_i<y}, i=1, 2, ..., 5 ... Z ... in six mutually independent trials`.

2. **Indeks kejadian keberhasilan pada bukti teorema berhenti pada r, bukan n.**
   - Anchor: `#proof` di bawah `#probability-density-functions`.
   - Konteks sumber: `if the event {X_i≤y}, i=1, 2, ..., r is considered a “success,” ... Z = the number of such successes in n mutually independent trials`.
   - Untuk peubah binomial yang menghitung keberhasilan dari seluruh sampel, kejadian harus didefinisikan untuk `i=1,2,...,n`.

3. **Koefisien binomial hilang dari jumlah kedua pada Persamaan 1.1.**
   - Anchor: `#eq-derivgry` di dalam `#proof`.
   - Konteks sumber, jumlah kedua: `+ sum_{k=r}^{n-1}[F(y)]^k(n-k)[1-F(y)]^{n-k-1}(-f(y))`.
   - Diferensiasi setiap suku `binom(n,k)[F(y)]^k[1-F(y)]^{n-k}` harus mempertahankan faktor `binom(n,k)` pada kedua suku aturan hasil kali. Hilangnya faktor ini membuat persamaan antara salah, meskipun rumus kepadatan akhir yang ditampilkan benar.

4. **Kurung tutup berlebih pada rumus PDF di ringkasan.**
   - Anchor: `#summary`, butir kedua `Key Takeaways`.
   - Konteks sumber: `\left[F(y)]\right]^{r-1}`.
   - Bentuk yang seimbang adalah `\left[F(y)\right]^{r-1}`.

5. **Teks alternatif Gambar 1.1 tidak berkaitan dengan contoh statistik urutan.**
   - Anchor: `#fig-stat415sec31810` di dalam `#exm-orderstats` / `#solution-1`.
   - Konteks atribut: `alt="Celsius vs Fahrenheit scatterplot"`.
   - Paragraf sebelum dan sesudah gambar membahas lima nilai pengamatan yang kurang dari 1 dan satu nilai yang tidak kurang dari 1. Label Celsius/Fahrenheit tidak memiliki hubungan semantik dengan isi atau fungsi gambar dalam contoh ini dan tidak boleh diterjemahkan secara harfiah.

6. **ID HTML terduplikasi pada Gambar 1.3.**
   - Anchor yang dimaksud: `#fig-stat415sec31812` di dalam `#exm-orderstats` / `#solution-1`.
   - Konteks sumber: elemen pembungkus `<div>` dan elemen `<img>` sama-sama memakai `id="fig-stat415sec31812"`.
   - ID dokumen harus unik; duplikasi ini membuat target fragmen dan hubungan aksesibilitas ambigu.

## Ambiguitas lokalisasi yang perlu ditangani secara konsisten

- Notasi sumber menanamkan akhiran ordinal Inggris di dalam matematika: `r^{th}`, `n^{th}`, `i^{th}`, dan `30^{th}`. Dalam prosa Indonesia, susun sebagai **statistik urutan ke-r**, **suku ke-n**, **nilai terkecil ke-i**, atau **persentil ke-30**. Jangan menerjemahkan `th` menjadi teks Indonesia lain di luar formula lalu menghasilkan urutan kata ganda.
- Sumber berganti-ganti antara `p.d.f.`, `pdf`, dan `PDF`, serta antara `cdf` dan `CDF`. Kandidat mengikuti glosarium: tulis istilah lengkap beserta **(PDF)** atau **(CDF)** pada pemakaian pertama, lalu gunakan singkatannya secara konsisten.
- `tie` pada data berurut tidak diterjemahkan sebagai *ikatan*. Gunakan **nilai sama (tie)** pada pemakaian pertama dan **nilai sama** sesudahnya.
- Huruf besar `Y_i` menyatakan statistik urutan sebagai peubah acak, sedangkan huruf kecil `y_i` menyatakan nilai yang teramati. Terjemahan perlu mempertahankan perbedaan ini melalui **statistik urutan** versus **statistik urutan yang teramati** atau **nilai pengamatan**.

## Keputusan lintas-unit yang material

- Bukti terminologi primer Indonesia untuk topik yang sama adalah artikel *Jurnal Matematika Integratif* tahun 2025, DOI `10.24198/jmi.v21.n1.63667.123-130`. Judul, abstrak, §2.4, definisi, dan pembahasan kepadatan gabungannya konsisten memakai **statistik urutan**, **sampel acak**, **peubah acak**, dan **fungsi kepadatan peluang gabungan**. Pencarian berbatas tidak menemukan sumber arXiv/TeX Bahasa Indonesia yang sesuai, sehingga artikel ini adalah fallback yang dicatat secara jujur.
- Untuk komponen Penn State, **statistik urutan** adalah istilah pengendali dan sudah digunakan pembaca PSU saat ini. Baris glosarium `O006-TERM-0030` yang menyatakan `statistik terurut` sudah usang untuk komponen ini; `statistik terurut` tetap merupakan alias warisan yang diakui dalam edisi Random yang diterbitkan terpisah.
- Istilah lain tetap mengikuti glosarium: **peubah acak**, **sampel acak**, **fungsi kepadatan peluang (PDF)**, **fungsi distribusi kumulatif (CDF)**, **fungsi massa peluang (PMF)**, **himpunan dukungan**, dan **bebas**.
- Varian lama lain tidak mengendalikan unit baru: navigasi memakai `Estimasi`, sedangkan glosarium menetapkan `pendugaan`; beberapa paragraf Lesson 00 memakai `penaksir`, sedangkan glosarium menetapkan `penduga`. Lesson 01 mengikuti glosarium tanpa mengubah berkas lama dalam subtask ini.
- Nada sumber sengaja percakapan (`groove on`, `rocket scientist`, `wash our hands of`, `Whew!`, `cool part`). Terjemahan pembaca sebaiknya mempertahankan keramahan tetapi mengungkapkan maknanya secara alami, bukan menerjemahkan idiom tersebut kata demi kata.
