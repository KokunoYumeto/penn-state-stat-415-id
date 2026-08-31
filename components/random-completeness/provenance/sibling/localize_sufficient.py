#!/usr/bin/env python3
"""Create the bounded id-ID Sufficient/Complete/Ancillary target.

The frozen Random HTML is used as the structural authority.  Reader-facing
prose is replaced by line-locked Indonesian templates; delimited TeX is
restored from the corresponding authority line so that translation never
silently changes a formula.  A small, explicit repair ledger records only
proved source defects and the one malformed list/duplicate-id repair.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag, urljoin


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "random" / "point" / "Sufficient.html"
TARGET = ROOT / "source" / "id-ID" / "random" / "point" / "Sufficient.html"
SOURCE_URL = "https://www.randomservices.org/random/point/Sufficient.html"
SOURCE_SHA256 = "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4"
EXPECTED_SOURCE_BYTES = 57507
EXPECTED_SOURCE_LINES = 583
MATH_RE = re.compile(r"\\\((?:[^\\]|\\.)*?\\\)|\\\[(?:[^\\]|\\.)*?\\\]", re.DOTALL)
TOKEN_RE = re.compile(r"@@M([1-9][0-9]*)@@")


# Only reader-facing rows are replaced. Formula-only rows remain exact source
# bytes unless listed in BOUNDED_FIXES below.
T: dict[int, str] = {
    2: '<html lang="id-ID">',
    6: "\t<title>Statistik Cukup, Lengkap, dan Ancillary</title>",
    9: '\t<meta name="keywords" content="probabilitas, statistika, pendugaan titik, statistik cukup, statistik lengkap, statistik ancillary, teorema faktorisasi Fisher-Neyman, teorema Rao-Blackwell, teorema Lehmann-Scheffe, teorema Basu, distribusi Bernoulli, distribusi Poisson, distribusi normal, distribusi gamma, distribusi beta, distribusi Pareto, distribusi seragam, model hipergeometrik, keluarga eksponensial">',
    36: '\t\t<li class="parent"><a href="../index.html">Random</a></li>',
    37: '\t\t<li class="parent"><a href="index.html">6. Pendugaan Titik</a></li>',
    38: '\t\t<li class="child"><a href="Estimators.html" title="Penduga">1</a></li>',
    39: '\t\t<li class="child"><a href="Moments.html" title="Metode Momen">2</a></li>',
    40: '\t\t<li class="child"><a href="Likelihood.html" title="Kemungkinan Maksimum">3</a></li>',
    41: '\t\t<li class="child"><a href="Bayes.html" title="Penduga Bayes">4</a></li>',
    42: '\t\t<li class="child"><a href="Unbiased.html" title="Penduga Tak Bias Terbaik">5</a></li>',
    44: '\t\t<li class="details"><button type="button" title="Perluas Rincian" onclick="expandDetails(true);"><img src="../icons/Plus.svg" alt="Perluas"></button></li>',
    45: '\t\t<li class="details"><button type="button" title="Ciutkan Rincian" onclick="expandDetails(false);"><img src="../icons/Minus.svg" alt="Ciutkan"></button></li>',
    47: '\t<h2 id="o006.random.point.sufficient.page">6. Statistik Cukup, Lengkap, dan Ancillary</h2>',
    50: '<h3 id="the">Teori Dasar</h3>',
    52: '<h4>Model Statistika Dasar</h4>',
    54: '<p>Tinjau kembali <a href="../sample/Introduction.html">model statistika dasar</a>, yang memuat <a href="../prob/Experiments.html">eksperimen acak</a> dengan <a href="../prob/Probability.html">variabel acak</a> teramati @@M1@@ yang nilainya berada dalam himpunan @@M2@@. Sekali lagi, eksperimen itu biasanya berupa pengambilan sampel @@M3@@ objek dari suatu populasi dan pencatatan satu atau beberapa pengukuran untuk setiap objek. Dalam hal ini, peubah hasil berbentuk',
    56: 'dengan @@M1@@ sebagai vektor pengukuran untuk objek ke-@@M2@@. Secara umum, kita menganggap distribusi @@M3@@ bergantung pada parameter @@M4@@ yang nilainya berada dalam himpunan parameter @@M5@@. Parameter @@M6@@ juga dapat berupa vektor. Kadang-kadang kita memakai subskrip pada fungsi kepadatan probabilitas, nilai harapan, dan sebagainya untuk menyatakan ketergantungannya pada @@M7@@.</p>',
    58: '<p>Seperti biasa, kasus khusus yang paling penting adalah ketika @@M1@@ merupakan barisan variabel acak yang saling bebas dan berdistribusi identik. Dalam hal ini @@M2@@ merupakan <a href="../sample/Introduction.html">sampel acak</a> dari distribusi bersama.</p>',
    60: '<h4>Statistik Cukup</h4>',
    62: '<p>Misalkan @@M1@@ merupakan statistik dengan nilai di suatu himpunan @@M2@@. Secara intuitif, @@M3@@ cukup untuk @@M4@@ jika @@M5@@ memuat seluruh informasi tentang @@M6@@ yang tersedia dalam seluruh peubah data @@M7@@. Berikut definisi formalnya:</p>',
    65: '\t<p class="dfn">Statistik @@M1@@ <dfn>cukup</dfn> untuk @@M2@@ jika <a href="../dist/Conditional.html">distribusi bersyarat</a> @@M3@@ yang diberikan @@M4@@ tidak bergantung pada @@M5@@.</p>',
    68: '<p>Kecukupan berkaitan dengan konsep <dfn>reduksi data</dfn>. Misalkan @@M1@@ bernilai di @@M2@@. Jika kita dapat menemukan statistik cukup @@M3@@ yang bernilai di @@M4@@, kita dapat mereduksi vektor data asli @@M5@@ (yang berdimensi @@M6@@ dan biasanya besar) menjadi vektor statistik @@M7@@ (yang berdimensi @@M8@@ dan biasanya jauh lebih kecil) tanpa kehilangan informasi tentang parameter @@M9@@.</p>',
    70: '<p>Hasil berikut memberikan syarat kecukupan yang ekuivalen dengan definisi ini.</p>',
    73: '\t<p class="math">Misalkan @@M1@@ merupakan statistik yang bernilai di @@M2@@, dan misalkan @@M3@@ serta @@M4@@ berturut-turut menyatakan <a href="../dist/Discrete.html">fungsi kepadatan probabilitas</a> @@M5@@ dan @@M6@@. Maka @@M7@@ cukup untuk @@M8@@ jika dan hanya jika fungsi pada @@M9@@ yang diberikan di bawah tidak bergantung pada @@M10@@:',
    76: '\t\t<summary>Rincian:</summary>',
    77: '\t\t<p>Distribusi bersama @@M1@@ terkonsentrasi pada himpunan @@M2@@. PDF bersyarat @@M3@@ yang diberikan @@M4@@ adalah @@M5@@ pada himpunan ini, dan 0 di luar himpunan tersebut.</p>',
    81: '<p>Definisi <a href="#suf1" class="ref"></a> tepat menangkap gagasan intuitif tentang kecukupan di atas, tetapi sulit diterapkan. Kita harus mengetahui terlebih dahulu kandidat statistik @@M1@@, lalu dapat menghitung distribusi bersyarat @@M2@@ yang diberikan @@M3@@. <dfn>Teorema faktorisasi Fisher-Neyman</dfn> berikut sering memungkinkan kita mengenali statistik cukup dari bentuk fungsi kepadatan probabilitas @@M4@@. Teorema ini dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Fisher.html\')" class="ancillary">Ronald Fisher</a> dan <a href="JavaScript:openAncillary(\'../biographies/Neyman.html\')" class="ancillary">Jerzy Neyman</a>.</p>',
    84: '\t<p class="math"><strong>Teorema Faktorisasi Fisher-Neyman</strong>. Misalkan @@M1@@ menyatakan fungsi kepadatan probabilitas @@M2@@ dan misalkan @@M3@@ merupakan statistik yang bernilai di @@M4@@. Maka @@M5@@ cukup untuk @@M6@@ jika dan hanya jika terdapat @@M7@@ dan @@M8@@ sedemikian sehingga',
    87: '\t\t<summary>Rincian:</summary>',
    88: '\t\t<p>Misalkan @@M1@@ menyatakan PDF @@M2@@ untuk @@M3@@. Jika @@M4@@ cukup untuk @@M5@@, maka menurut teorema sebelumnya fungsi @@M6@@ untuk @@M7@@ tidak bergantung pada @@M8@@. Jadi @@M9@@ untuk @@M10@@, dan pemetaan @@M11@@ berbentuk seperti dalam teorema. Sebaliknya, andaikan pemetaan @@M12@@ berbentuk seperti dalam teorema. Maka terdapat fungsi positif @@M13@@ sedemikian sehingga @@M14@@ untuk @@M15@@ dan @@M16@@. Dengan demikian @@M17@@ untuk @@M18@@, yang tidak bergantung pada @@M19@@.</p>',
    92: '<p>Perhatikan bahwa @@M1@@ hanya bergantung pada data @@M2@@, bukan pada parameter @@M3@@. Dengan bahasa yang tidak terlalu teknis, @@M4@@ cukup untuk @@M5@@ jika fungsi kepadatan probabilitas @@M6@@ bergantung pada vektor data @@M7@@ dan parameter @@M8@@ hanya melalui @@M9@@.</p>',
    95: '\t<p class="math">Jika @@M1@@ dan @@M2@@ merupakan <a href="../sample/Introduction.html">statistik ekuivalen</a> dan @@M3@@ cukup untuk @@M4@@, maka @@M5@@ juga cukup untuk @@M6@@.</p>',
    98: '<h4>Statistik Cukup Minimal</h4>',
    100: '<p>Peubah data seluruhnya @@M1@@ cukup untuk @@M2@@. Namun, seperti telah dicatat di atas, biasanya ada statistik @@M3@@ yang cukup untuk @@M4@@ dan berdimensi lebih kecil, sehingga kita benar-benar dapat mereduksi data. Secara wajar, kita ingin menemukan statistik @@M5@@ dengan dimensi sekecil mungkin. Dalam banyak kasus, dimensi terkecil @@M6@@ ini sama dengan dimensi @@M7@@ vektor parameter @@M8@@. Namun, seperti akan kita lihat, hal ini tidak selalu terjadi; @@M9@@ dapat lebih kecil atau lebih besar daripada @@M10@@. Contoh berdasarkan distribusi seragam diberikan pada <a href="#uni2" class="ref"></a>.</p>',
    103: '<p class="dfn">Misalkan statistik @@M1@@ cukup untuk @@M2@@. Maka @@M3@@ <dfn>cukup minimal</dfn> jika @@M4@@ merupakan fungsi dari setiap statistik lain @@M5@@ yang cukup untuk @@M6@@.</p>',
    106: '<p>Sekali lagi, definisi <a href="#min1" class="ref"></a> tepat menangkap gagasan kecukupan minimal, tetapi sulit diterapkan. Hasil berikut pada <a href="#min2" class="ref"></a> memberikan syarat yang ekuivalen.</p>',
    109: '\t<p class="math">Misalkan @@M1@@ menyatakan fungsi kepadatan probabilitas @@M2@@ yang bersesuaian dengan nilai parameter @@M3@@, dan misalkan @@M4@@ merupakan statistik yang bernilai di @@M5@@. Maka @@M6@@ cukup minimal untuk @@M7@@ jika syarat berikut berlaku: untuk @@M8@@ dan @@M9@@',
    112: '\t\t<summary>Rincian:</summary>',
    113: '\t\t<p>Andaikan syarat dalam teorema terpenuhi. Maka PDF @@M1@@ dari @@M2@@ harus berbentuk seperti dalam teorema faktorisasi <a href="#fac" class="ref"></a>, sehingga @@M3@@ cukup untuk @@M4@@. Selanjutnya, misalkan @@M5@@ merupakan statistik cukup lain untuk @@M6@@ yang bernilai di @@M7@@. Dari teorema faktorisasi, terdapat @@M8@@ dan @@M9@@ sedemikian sehingga @@M10@@ untuk @@M11@@. Jadi, jika @@M12@@ dan @@M13@@, maka',
    115: '\t\t\tdan tidak bergantung pada @@M1@@. Oleh karena itu, dari syarat dalam teorema @@M2@@, statistik yang didefinisikan oleh @@M3@@ merupakan fungsi dari statistik lain @@M4@@.</p>',
    120: '\t<p class="math">Jika @@M1@@ dan @@M2@@ merupakan statistik ekuivalen dan @@M3@@ cukup minimal untuk @@M4@@, maka @@M5@@ juga cukup minimal untuk @@M6@@.</p>',
    123: '<h4>Sifat-Sifat Statistik Cukup</h4>',
    125: '<p>Kecukupan berkaitan dengan beberapa metode konstruksi penduga yang telah kita pelajari.</p>',
    128: '\t<p class="math">Misalkan @@M1@@ cukup untuk @@M2@@ dan terdapat <a href="Likelihood.html">penduga kemungkinan maksimum</a> untuk @@M3@@. Maka terdapat penduga kemungkinan maksimum @@M4@@ yang merupakan fungsi dari @@M5@@.</p>',
    130: '\t\t<summary>Rincian:</summary>',
    131: '\t\t<p>Dari teorema faktorisasi <a href="#fac" class="ref"></a>, fungsi log-kemungkinan untuk @@M1@@ adalah',
    133: '\t\tDengan demikian, nilai @@M1@@ yang memaksimumkan fungsi ini, jika ada, harus merupakan fungsi dari @@M2@@.</p>',
    137: '<p>Secara khusus, misalkan @@M1@@ merupakan penduga kemungkinan maksimum tunggal untuk @@M2@@ dan @@M3@@ cukup untuk @@M4@@. Jika @@M5@@ cukup untuk @@M6@@, maka @@M7@@ merupakan fungsi dari @@M8@@ menurut <a href="#mle" class="ref"></a>. Jadi @@M9@@ cukup minimal untuk @@M10@@. Hasil berikut berlaku untuk <a href="Bayes.html">analisis Bayes</a>.</p>',
    140: '\t<p class="math">Misalkan statistik @@M1@@ cukup untuk parameter @@M2@@ dan @@M3@@ dimodelkan sebagai variabel acak @@M4@@ dengan nilai di @@M5@@. Maka distribusi posterior @@M6@@ yang diberikan @@M7@@ merupakan fungsi dari @@M8@@.</p>',
    142: '\t\t<summary>Rincian:</summary>',
    143: '\t\t<p>Misalkan @@M1@@ menyatakan PDF prior @@M2@@ dan @@M3@@ PDF bersyarat @@M4@@ yang diberikan @@M5@@. Menurut teorema faktorisasi <a href="#fac" class="ref"></a>, PDF bersyarat ini berbentuk @@M6@@ untuk @@M7@@ dan @@M8@@. PDF posterior @@M9@@ yang diberikan @@M10@@ adalah',
    145: '\t\tDi sini fungsi pada penyebut adalah PDF marginal @@M1@@, atau cukup konstanta normalisasi untuk fungsi @@M2@@ pada pembilang. Misalkan @@M3@@ mempunyai distribusi kontinu pada @@M4@@, sehingga @@M5@@ untuk @@M6@@. Maka PDF posterior menyederhana menjadi',
    147: '\t\t\tyang bergantung pada @@M1@@ hanya melalui @@M2@@.</p>',
    151: '<p>Dalam kerangka analisis Bayes yang sama, misalkan @@M1@@ merupakan parameter bernilai riil. Jika kita memakai fungsi kerugian kuadrat rata-rata yang lazim, penduga Bayes adalah @@M2@@. Menurut <a href="#bay" class="ref"></a>, @@M3@@ merupakan fungsi dari statistik cukup @@M4@@. Artinya, @@M5@@.</p>',
    153: '<p>Teorema <a href="#rbt" class="ref"></a> berikut adalah <dfn>teorema Rao-Blackwell</dfn>, dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Rao.html\')" class="ancillary">CR Rao</a> dan <a href="JavaScript:openAncillary(\'../biographies/Blackwell.html\')" class="ancillary">David Blackwell</a>. Teorema ini menunjukkan cara memakai statistik cukup untuk memperbaiki penduga tak bias.</p>',
    156: '\t<p class="math"><strong>Teorema Rao-Blackwell</strong>. Misalkan @@M1@@ cukup untuk @@M2@@ dan @@M3@@ merupakan penduga tak bias bagi parameter riil @@M4@@. Maka @@M5@@ juga merupakan penduga tak bias bagi @@M6@@ dan secara seragam lebih baik daripada @@M7@@.</p>',
    158: '\t\t<summary>Rincian:</summary>',
    159: '\t\t<p>Hal ini mengikuti sifat dasar <a href="../expect/Conditional.html">nilai harapan bersyarat</a> dan varians bersyarat. Pertama, karena @@M1@@ merupakan fungsi dari @@M2@@ dan @@M3@@ cukup untuk @@M4@@, @@M5@@ merupakan statistik yang sah; artinya, ia tidak bergantung pada @@M6@@, meskipun nilai harapan secara formal memuat ketergantungan pada @@M7@@. Selanjutnya, @@M8@@ merupakan fungsi dari @@M9@@ dan @@M10@@ untuk @@M11@@. Jadi @@M12@@ merupakan penduga tak bias bagi @@M13@@. Terakhir, @@M14@@ untuk setiap @@M15@@.</p>',
    163: '<h4>Statistik Lengkap</h4>',
    166: '\t<p class="dfn">Misalkan @@M1@@ merupakan statistik yang bernilai di himpunan @@M2@@. Maka @@M3@@ <dfn>lengkap</dfn> untuk @@M4@@ jika untuk setiap fungsi @@M5@@',
    170: '<p>Untuk memahami syarat yang tampak agak ganjil ini, misalkan @@M1@@ merupakan statistik yang dibangun dari @@M2@@ dan digunakan sebagai penduga untuk 0 (dipandang sebagai fungsi dari @@M3@@). Syarat kelengkapan berarti satu-satunya penduga tak bias semacam itu adalah statistik yang bernilai 0 dengan probabilitas 1.</p>',
    173: '\t<p class="math">Jika @@M1@@ dan @@M2@@ merupakan statistik ekuivalen dan @@M3@@ lengkap untuk @@M4@@, maka @@M5@@ juga lengkap untuk @@M6@@.</p>',
    176: '<p>Teorema <a href="#lst" class="ref"></a> berikut menunjukkan pentingnya statistik yang sekaligus lengkap dan cukup; teorema ini dikenal sebagai <dfn>teorema Lehmann-Scheffé</dfn>, dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Lehmann.html\')" class="ancillary">Erich Lehmann</a> dan <a href="JavaScript:openAncillary(\'../biographies/Scheffe.html\')" class="ancillary">Henry Scheffé</a>.</p>',
    179: '\t<p class="math"><strong>Teorema Lehmann-Scheffé</strong>. Misalkan @@M1@@ cukup dan lengkap untuk @@M2@@, dan @@M3@@ merupakan penduga tak bias bagi parameter riil @@M4@@. Maka @@M5@@ merupakan <a href="Unbiased.html">penduga tak bias bervarians minimum seragam</a> (UMVUE) bagi @@M6@@.</p>',
    181: '\t\t<summary>Rincian:</summary>',
    182: '\t\t<p>Misalkan @@M1@@ merupakan penduga tak bias bagi @@M2@@. Menurut teorema Rao-Blackwell <a href="#rbt" class="ref"></a>, @@M3@@ juga merupakan penduga tak bias bagi @@M4@@ dan secara seragam lebih baik daripada @@M5@@. Karena @@M6@@ merupakan fungsi dari @@M7@@, kelengkapan menyiratkan bahwa @@M8@@ dengan probabilitas 1.</p>',
    186: '<h4>Statistik Ancillary</h4>',
    189: '\t<p class="dfn">Misalkan @@M1@@ merupakan statistik dengan nilai di suatu himpunan @@M2@@. Jika distribusi @@M3@@ tidak bergantung pada @@M4@@, maka @@M5@@ disebut <dfn>statistik ancillary</dfn> untuk @@M6@@.</p>',
    192: '<p>Dengan demikian, gagasan statistik ancillary melengkapi gagasan statistik cukup. Statistik cukup memuat seluruh informasi yang tersedia tentang parameter; statistik ancillary tidak memuat informasi tentang parameter. Teorema <a href="#bas" class="ref"></a>, yang dikenal sebagai <dfn>teorema Basu</dfn> dan dinamai menurut Debabrata Basu, memperjelas hal ini.</p>',
    195: '\t<p class="math"><strong>Teorema Basu</strong>. Misalkan @@M1@@ lengkap dan cukup untuk parameter @@M2@@, dan @@M3@@ merupakan statistik ancillary untuk @@M4@@. Maka @@M5@@ dan @@M6@@ saling bebas.</p>',
    197: '\t\t<summary>Rincian:</summary>',
    198: '\t\t<p>Misalkan @@M1@@ menyatakan fungsi kepadatan probabilitas @@M2@@ dan @@M3@@ menyatakan fungsi kepadatan probabilitas bersyarat @@M4@@ yang diberikan @@M5@@. Dari sifat nilai harapan bersyarat, @@M6@@ untuk @@M7@@. Namun, kelengkapan menyiratkan @@M8@@ dengan probabilitas 1.</p>',
    203: '\t<p class="math">Jika @@M1@@ dan @@M2@@ merupakan statistik ekuivalen dan @@M3@@ ancillary untuk @@M4@@, maka @@M5@@ juga ancillary untuk @@M6@@.</p>',
    206: '<h3 id="exa">Penerapan dan Distribusi Khusus</h3>',
    208: '<p>Dalam subbagian ini, kita akan menelaah statistik cukup, lengkap, dan ancillary untuk sejumlah distribusi khusus. Seperti biasa, cobalah mengerjakan masalahnya sendiri sebelum melihat solusinya.</p>',
    210: '<h4 id="ber">Distribusi Bernoulli</h4>',
    212: '<p>Ingat bahwa <a href="../bernoulli/Introduction.html">distribusi Bernoulli</a> dengan parameter @@M1@@ merupakan distribusi diskret pada @@M2@@ dengan fungsi kepadatan probabilitas @@M3@@ yang didefinisikan oleh',
    214: 'Misalkan @@M1@@ merupakan sampel acak berukuran @@M2@@ dari distribusi Bernoulli dengan parameter @@M3@@. Secara ekuivalen, @@M4@@ merupakan barisan <a href="../bernoulli/index.html">percobaan Bernoulli</a>, dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Bernoulli.html\')" class="ancillary">Jacob Bernoulli</a>. Dalam bahasa keandalan yang lazim, @@M5@@ jika percobaan ke-@@M6@@ berhasil, dan @@M7@@ jika percobaan ke-@@M8@@ gagal. Misalkan @@M9@@ menyatakan banyaknya keberhasilan. Ingat bahwa @@M10@@ memiliki <a href="../bernoulli/Binomial.html">distribusi binomial</a> dengan parameter @@M11@@ dan @@M12@@, serta fungsi kepadatan probabilitas @@M13@@ yang didefinisikan oleh',
    218: '\t<p class="math">@@M1@@ cukup untuk @@M2@@. Secara khusus, untuk @@M3@@, distribusi bersyarat @@M4@@ yang diberikan @@M5@@ seragam pada himpunan titik',
    221: '\t\t<summary>Rincian:</summary>',
    222: '\t\t<p>PDF bersama @@M1@@ dari @@M2@@ didefinisikan oleh',
    224: '\t\tDi sini @@M1@@. Sekarang ambil @@M2@@. Jika @@M3@@, @@M4@@ terkonsentrasi pada @@M5@@ dan',
    226: '\t\tTentu saja, @@M1@@ adalah kardinalitas @@M2@@.</p>',
    230: '<p>Hasil ini secara intuitif masuk akal: dalam barisan percobaan Bernoulli, seluruh informasi tentang probabilitas keberhasilan @@M1@@ terkandung dalam banyaknya keberhasilan @@M2@@. <em>Urutan</em> khusus keberhasilan dan kegagalan tidak memberikan informasi tambahan. Tentu saja, kecukupan @@M3@@ lebih mudah dibuktikan melalui teorema faktorisasi <a href="#fac" class="ref"></a>, tetapi distribusi bersyarat memberikan wawasan tambahan.</p>',
    233: '\t<p class="math">@@M1@@ lengkap untuk @@M2@@ pada himpunan parameter @@M3@@.</p>',
    235: '\t\t<summary>Rincian:</summary>',
    236: '\t\t<p>Jika @@M1@@, maka',
    238: '\t\tJumlah terakhir merupakan polinom dalam variabel @@M1@@. Jika polinom ini 0 untuk semua @@M2@@, semua koefisiennya harus 0. Jadi @@M3@@ untuk @@M4@@.</p>',
    242: '<p>Bukti <a href="#ber2" class="ref"></a> sebenarnya menunjukkan bahwa jika himpunan parameter merupakan sembarang himpunan bagian dari @@M1@@ yang memuat interval dengan panjang positif, maka @@M2@@ lengkap untuk @@M3@@. Namun, gagasan kelengkapan sangat bergantung pada himpunan parameter. Hasil berikut membahas kasus ketika @@M4@@ memiliki himpunan nilai berhingga.</p>',
    245: '\t<p class="math">Misalkan himpunan parameter @@M1@@ merupakan himpunan berhingga dengan @@M2@@ elemen. Jika ukuran sampel @@M3@@ setidaknya @@M4@@, maka @@M5@@ tidak lengkap untuk @@M6@@.</p>',
    248: '\t\t<p>Misalkan @@M1@@ dan @@M2@@ untuk @@M3@@. Maka',
    247: '\t\t<summary>Rincian:</summary>',
    250: '\t\tIni merupakan himpunan @@M1@@ persamaan linear homogen dalam variabel @@M2@@. Karena @@M3@@, kita memiliki sedikitnya @@M4@@ variabel, sehingga terdapat tak hingga banyak solusi nontrivial.</p>',
    254: '<p>Rata-rata sampel @@M1@@ (proporsi keberhasilan dalam sampel) jelas ekuivalen dengan @@M2@@ (banyaknya keberhasilan), sehingga juga cukup untuk @@M3@@ dan lengkap untuk @@M4@@. Ingat bahwa rata-rata sampel @@M5@@ merupakan <a href="Moments.html#ber">penduga metode momen</a> bagi @@M6@@ dan juga <a href="Likelihood.html#ber">penduga kemungkinan maksimum</a> bagi @@M7@@ pada himpunan parameter @@M8@@.</p>',
    256: '<p>Dalam <a href="Bayes.html#ber">analisis Bayes</a>, pendekatan lazim adalah memodelkan @@M1@@ dengan variabel acak @@M2@@ yang memiliki <a href="../special/Beta.html">distribusi beta</a> prior dengan parameter kiri @@M3@@ dan parameter kanan @@M4@@. Maka distribusi posterior @@M5@@ yang diberikan @@M6@@ adalah beta dengan parameter kiri @@M7@@ dan parameter kanan @@M8@@. Distribusi posterior hanya bergantung pada data melalui statistik cukup @@M9@@, sebagaimana dijamin oleh <a href="#bay" class="ref"></a>.</p>',
    260: '\t<p class="math">Varians sampel @@M1@@ merupakan UMVUE dari varians distribusi @@M2@@ untuk @@M3@@, dan dapat ditulis sebagai',
    264: '\t\t<p>Ingat bahwa varians sampel dapat ditulis sebagai',
    266: '\t\tNamun @@M1@@ karena @@M2@@ merupakan variabel indikator, dan @@M3@@. Substitusi menghasilkan representasi di atas. Secara umum, @@M4@@ merupakan penduga tak bias bagi varians distribusi @@M5@@. Tetapi dalam kasus ini, @@M6@@ merupakan fungsi dari statistik cukup dan lengkap @@M7@@, sehingga menurut <a href="#lst" class="ref"></a>, @@M8@@ merupakan UMVUE dari @@M9@@.</p>',
    263: '\t\t<summary>Rincian:</summary>',
    270: '<h4 id="poi">Distribusi Poisson</h4>',
    272: '<p>Ingat bahwa <a href="../poisson/Poisson.html">distribusi Poisson</a> dengan parameter @@M1@@ merupakan distribusi diskret pada @@M2@@ dengan fungsi kepadatan probabilitas @@M3@@ yang didefinisikan oleh',
    274: 'Distribusi ini dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Poisson.html\')" class="ancillary">Simeon Poisson</a> dan digunakan untuk memodelkan banyaknya <q>titik acak</q> dalam wilayah waktu atau ruang, khususnya dalam konteks <a href="../poisson/index.html">proses Poisson</a>. Parameter @@M1@@ sebanding dengan ukuran wilayah tersebut, dan sekaligus merupakan rata-rata serta varians distribusi.</p>',
    276: '<p>Sekarang misalkan @@M1@@ merupakan sampel acak berukuran @@M2@@ dari distribusi Poisson dengan parameter @@M3@@. Ingat bahwa jumlah pengamatan @@M4@@ juga berdistribusi Poisson, tetapi dengan parameter @@M5@@.</p>',
    279: '\t<p class="math">Statistik @@M1@@ cukup untuk @@M2@@. Secara khusus, untuk @@M3@@, distribusi bersyarat @@M4@@ yang diberikan @@M5@@ adalah <a href="../bernoulli/Multinomial.html">distribusi multinomial</a> dengan @@M6@@ percobaan, @@M7@@ kategori, dan probabilitas percobaan seragam.</p>',
    281: '\t\t<summary>Rincian:</summary>',
    282: '\t\t<p>PDF bersama @@M1@@ dari @@M2@@ didefinisikan oleh',
    284: '\t\tDengan @@M1@@. Untuk @@M2@@, vektor acak @@M3@@ bernilai di himpunan @@M4@@. Selain itu,',
    286: '\t\tUngkapan terakhir merupakan PDF distribusi multinomial yang dinyatakan dalam teorema. Yang penting, distribusi bersyarat tersebut tidak bergantung pada @@M1@@.</p>',
    290: '<p>Seperti sebelumnya, teorema faktorisasi <a href="#fac" class="ref"></a> lebih mudah digunakan untuk membuktikan kecukupan @@M1@@, tetapi distribusi bersyarat memberikan wawasan tambahan.</p>',
    293: '\t<p class="math">@@M1@@ lengkap untuk @@M2@@.</p>',
    295: '\t\t<summary>Rincian:</summary>',
    296: '\t\t<p>Jika @@M1@@, maka',
    298: '\t\tJumlah terakhir merupakan deret pangkat dalam @@M1@@ dengan koefisien @@M2@@ untuk @@M3@@. Jika deret ini 0 untuk semua @@M4@@ dalam suatu interval terbuka, koefisiennya harus 0 sehingga @@M5@@ untuk @@M6@@.</p>',
    302: '<p>Seperti pada pembahasan percobaan Bernoulli, rata-rata sampel @@M1@@ jelas ekuivalen dengan @@M2@@, sehingga juga cukup untuk @@M3@@ dan lengkap untuk @@M4@@. Ingat bahwa @@M5@@ merupakan <a href="Moments.html#o006.random.point.moments.section.poisson">penduga metode momen</a> bagi @@M6@@ dan merupakan <a href="Likelihood.html#poi">penduga kemungkinan maksimum</a> pada ruang parameter @@M7@@.</p>',
    305: '\t<p class="math">UMVUE untuk parameter @@M1@@ pada @@M2@@ adalah',
    306: '\t@@M1@@</p>',
    308: '\t\t<summary>Rincian:</summary>',
    309: '\t\t<p> <a href="../expect/Generating.html#pgf">Fungsi pembangkit probabilitas</a> @@M1@@ adalah',
    310: '\t\t@@M1@@',
    311: '\t\tJadi',
    312: '\t\t@@M1@@',
    313: '\t\tJadi @@M1@@ merupakan penduga tak bias bagi @@M2@@. Karena @@M3@@ merupakan fungsi dari statistik cukup dan lengkap @@M4@@, teorema Lehmann-Scheffé <a href="#lst" class="ref"></a> menyatakan bahwa @@M5@@ merupakan UMVUE bagi @@M6@@.</p>',
    317: '<h4 id="nor">Distribusi Normal</h4>',
    319: '<p>Ingat bahwa <a href="../special/Normal.html">distribusi normal</a> dengan rata-rata @@M1@@ dan varians @@M2@@ merupakan distribusi kontinu pada @@M3@@ dengan fungsi kepadatan probabilitas @@M4@@ yang didefinisikan oleh',
    321: 'Distribusi ini sering digunakan untuk memodelkan besaran fisik yang dipengaruhi galat acak kecil, dan karena <a href="../sample/CLT.html">teorema limit pusat</a>, mungkin merupakan distribusi terpenting dalam statistika.</p>',
    324: '\t<p class="math">Misalkan @@M1@@ merupakan sampel acak dari distribusi normal dengan rata-rata @@M2@@ dan varians @@M3@@. Maka setiap pasangan statistik berikut cukup minimal untuk @@M4@@</p>',
    326: '\t\t<li>@@M1@@ dengan @@M2@@ dan @@M3@@.</li>',
    327: '\t\t<li>@@M1@@ dengan @@M2@@ sebagai rata-rata sampel dan @@M3@@ sebagai varians sampel.</li>',
    328: '\t\t<li>@@M1@@ dengan @@M2@@ sebagai varians sampel berbias.</li>',
    331: '\t\t<summary>Rincian:</summary>',
    333: '\t\t\t<li>PDF bersama @@M1@@ dari @@M2@@ diberikan oleh',
    335: '\t\t\tSetelah sedikit aljabar, ini dapat ditulis sebagai',
    336: '\t\t\t@@M1@@',
    337: '\t\t\tDari teorema faktorisasi <a href="#fac" class="ref"></a>, @@M1@@ cukup untuk @@M2@@. Kecukupan minimal mengikuti dari <a href="#min2" class="ref"></a>.</li>',
    338: '\t\t\t<li>Perhatikan bahwa @@M1@@. Jadi @@M2@@ ekuivalen dengan @@M3@@, sehingga @@M4@@ juga cukup minimal untuk @@M5@@.</li>',
    339: '\t\t\t<li>Demikian pula, @@M1@@ dan @@M2@@. Jadi @@M3@@ ekuivalen dengan @@M4@@ dan @@M5@@ juga cukup minimal untuk @@M6@@.</li>',
    344: '<p>Ingat bahwa @@M1@@ dan @@M2@@ merupakan penduga metode momen bagi @@M3@@ dan @@M4@@, berturut-turut, dan juga penduga kemungkinan maksimum pada ruang parameter @@M5@@.</p>',
    347: '\t<p class="app">Jalankan <a href="JavaScript:openAncillary(\'../apps/NormalEstimate.html\')" class="ancillary">eksperimen pendugaan normal</a> 1000 kali dengan berbagai nilai parameter. Bandingkan dugaan parameter berdasarkan bias dan galat kuadrat rata-rata.</p>',
    350: '<p>Kadang-kadang varians @@M1@@ distribusi normal diketahui, tetapi rata-rata @@M2@@ tidak diketahui. Jarang terjadi sebaliknya, yaitu @@M3@@ diketahui tetapi @@M4@@ tidak diketahui. Namun, kita dapat memberikan statistik cukup untuk kedua kasus tersebut.</p>',
    353: '\t<p class="math">Misalkan lagi @@M1@@ merupakan sampel acak dari distribusi normal dengan rata-rata @@M2@@ dan varians @@M3@@.</p>',
    355: '\t\t<li>Jika @@M1@@ diketahui, maka @@M2@@ cukup minimal untuk @@M3@@.</li>',
    356: '\t\t<li>Jika @@M1@@ diketahui, maka @@M2@@ cukup untuk @@M3@@.</li>',
    359: '\t\t<summary>Rincian:</summary>',
    361: '\t\t\t<li>Hasil ini mengikuti persamaan tampilan kedua untuk PDF @@M1@@ dari @@M2@@ dalam bukti <a href="#nor1" class="ref"></a>.</li>',
    362: '\t\t\t<li>Hasil ini mengikuti persamaan tampilan pertama untuk PDF @@M1@@ dari @@M2@@ dalam bukti teorema <a href="#nor1" class="ref"></a>.</li>',
    367: '<p>Dengan ekuivalensi, pada bagian (a) rata-rata sampel @@M1@@ cukup minimal untuk @@M2@@, sedangkan pada bagian (b) varians sampel khusus @@M3@@ cukup minimal untuk @@M4@@. Selain itu, pada bagian (a), @@M5@@ lengkap untuk @@M6@@ pada ruang parameter @@M7@@ dan varians sampel @@M8@@ ancillary untuk @@M9@@ (ingat bahwa @@M10@@ berdistribusi <a href="../special/ChiSquare.html">khi-kuadrat</a> dengan @@M11@@ derajat bebas). Teorema Basu <a href="#bas" class="ref"></a> kemudian menyatakan bahwa rata-rata sampel @@M12@@ dan varians sampel @@M13@@ saling bebas. Kita telah membuktikan hal ini dengan cara yang lebih langsung dalam bagian <a href="../sample/Normal.html">sifat khusus sampel normal</a>, tetapi rumusan melalui statistik cukup dan ancillary memberikan wawasan tambahan.</p>',
    369: '<h4 id="gam">Distribusi Gamma</h4>',
    371: '<p>Ingat bahwa <a href="../special/Gamma.html">distribusi gamma</a> dengan parameter bentuk @@M1@@ dan parameter skala @@M2@@ merupakan distribusi kontinu pada @@M3@@ dengan fungsi kepadatan probabilitas @@M4@@ yang didefinisikan oleh',
    373: 'Distribusi gamma sering digunakan untuk memodelkan waktu acak, khususnya dalam konteks <a href="../poisson/index.html">proses Poisson</a>, serta jenis variabel acak positif lainnya.</p>',
    376: '\t<p class="math">Misalkan @@M1@@ merupakan sampel acak dari distribusi gamma dengan parameter bentuk @@M2@@ dan parameter skala @@M3@@. Setiap pasangan statistik berikut cukup minimal untuk @@M4@@</p>',
    378: '\t\t<li>@@M1@@ dengan @@M2@@ sebagai jumlah pengamatan dan @@M3@@ sebagai hasil kali pengamatan.</li>',
    379: '\t\t<li>@@M1@@ dengan @@M2@@ sebagai rata-rata aritmetika sampel dari @@M3@@ dan @@M4@@ sebagai rata-rata geometrik sampel dari @@M5@@.</li>',
    382: '\t\t<summary>Rincian:</summary>',
    384: '\t\t\t<li>PDF bersama @@M1@@ dari @@M2@@ diberikan oleh',
    386: '\t\t\tDari teorema faktorisasi <a href="#fac" class="ref"></a>, @@M1@@ cukup untuk @@M2@@. Kecukupan minimal mengikuti dari <a href="#min2" class="ref"></a>.</li>',
    387: '\t\t\t<li>Jelas bahwa @@M1@@ ekuivalen dengan @@M2@@ dan @@M3@@ ekuivalen dengan @@M4@@. Jadi @@M5@@ juga cukup minimal untuk @@M6@@.</li>',
    392: '<p>Ingat bahwa penduga metode momen untuk @@M1@@ dan @@M2@@ masing-masing adalah @@M3@@ dan @@M4@@, dengan @@M5@@ sebagai rata-rata sampel dan @@M6@@ sebagai varians sampel berbias. Jika parameter bentuk @@M7@@ diketahui, @@M8@@ merupakan penduga metode momen sekaligus penduga kemungkinan maksimum bagi @@M9@@ pada ruang parameter @@M10@@. Perhatikan bahwa @@M11@@ bukan fungsi dari statistik cukup @@M12@@, sehingga penduga yang didasarkan pada @@M13@@ kehilangan informasi.</p>',
    395: '\t<p class="app">Jalankan <a href="JavaScript:openAncillary(\'../apps/GammaEstimate.html\')" class="ancillary">eksperimen pendugaan gamma</a> 1000 kali dengan berbagai nilai parameter dan ukuran sampel @@M1@@. Bandingkan dugaan parameter berdasarkan bias dan galat kuadrat rata-rata.</p>',
    398: '<p>Bukti <a href="#gam1" class="ref"></a> juga menunjukkan bahwa @@M1@@ cukup untuk @@M2@@ jika @@M3@@ diketahui, dan bahwa @@M4@@ cukup untuk @@M5@@ jika @@M6@@ diketahui.</p>',
    401: '\t<p class="math">Misalkan lagi @@M1@@ merupakan sampel acak berukuran @@M2@@ dari distribusi gamma dengan parameter bentuk @@M3@@ tetap dan parameter skala @@M4@@. Maka @@M5@@ lengkap untuk @@M6@@.</p>',
    403: '\t\t<summary>Rincian:</summary>',
    404: '\t\t<p>@@M1@@ berdistribusi gamma dengan parameter bentuk @@M2@@ dan parameter skala @@M3@@. Jadi, jika @@M4@@, maka',
    406: '\t\tIntegral terakhir dapat ditafsirkan sebagai transformasi Laplace dari fungsi @@M1@@ yang dievaluasi pada @@M2@@. Jika transformasi ini 0 untuk semua @@M3@@ dalam suatu interval terbuka, maka @@M4@@ hampir di mana-mana pada @@M5@@.</p>',
    411: '\t<p class="math">Misalkan lagi @@M1@@ merupakan sampel acak dari distribusi gamma pada @@M2@@ dengan parameter bentuk @@M3@@ tetap dan parameter skala @@M4@@. Misalkan @@M5@@ menyatakan rata-rata sampel dan @@M6@@ rata-rata geometrik sampel, seperti sebelumnya. Maka</p>',
    413: '\t\t<li>@@M1@@ ancillary untuk @@M2@@.</li>',
    414: '\t\t<li>@@M1@@ dan @@M2@@ saling bebas.</li>',
    417: '\t\t<summary>Rincian:</summary>',
    419: '\t\t\t<li>Kita dapat mengambil @@M1@@ untuk @@M2@@, dengan @@M3@@ merupakan sampel acak berukuran @@M4@@ dari distribusi gamma dengan parameter bentuk @@M5@@ dan parameter skala 1 (distribusi gamma <dfn>standar</dfn> dengan parameter bentuk @@M6@@). Kemudian',
    421: '\t\t\t@@M1@@ untuk @@M2@@, dan distribusi @@M3@@ tidak bergantung pada @@M4@@. Oleh karena itu distribusi @@M5@@ tidak bergantung pada @@M6@@.</li>',
    422: '\t\t\t<li>Hal ini mengikuti <a href="#bas" class="ref"></a> milik Basu, karena @@M1@@ lengkap dan cukup untuk @@M2@@ dan @@M3@@ ancillary untuk @@M4@@.</li>',
    427: '<h4 id="bet">Distribusi Beta</h4>',
    429: '<p>Ingat bahwa <a href="../special/Beta.html">distribusi beta</a> dengan parameter kiri @@M1@@ dan parameter kanan @@M2@@ merupakan distribusi kontinu pada @@M3@@ dengan fungsi kepadatan probabilitas @@M4@@ yang diberikan oleh',
    431: 'dengan @@M1@@ sebagai fungsi beta. Distribusi beta sering digunakan untuk memodelkan proporsi acak dan variabel acak lain yang nilainya berada pada interval terbatas.</p>',
    434: '\t<p class="math">Misalkan @@M1@@ merupakan sampel acak dari distribusi beta dengan parameter kiri @@M2@@ dan parameter kanan @@M3@@. Maka @@M4@@ cukup minimal untuk @@M5@@, dengan @@M6@@ dan @@M7@@.</p>',
    436: '\t\t<summary>Rincian:</summary>',
    437: '\t\t<p>PDF bersama @@M1@@ dari @@M2@@ diberikan oleh',
    439: '\t\tDari teorema faktorisasi <a href="#fac" class="ref"></a>, @@M1@@ cukup untuk @@M2@@. Kecukupan minimal mengikuti dari <a href="#min2" class="ref"></a>.</p>',
    443: '<p>Bukti <a href="#bet1" class="ref"></a> juga menunjukkan bahwa @@M1@@ cukup untuk @@M2@@ jika @@M3@@ diketahui, dan @@M4@@ cukup untuk @@M5@@ jika @@M6@@ diketahui. Ingat bahwa <a href="Moments.html#bet">penduga metode momen</a> untuk @@M7@@ dan @@M8@@ adalah',
    445: 'berturut-turut, dengan @@M1@@ sebagai rata-rata sampel dan @@M2@@ sebagai momen sampel orde kedua. Jika @@M3@@ diketahui, penduga metode momen untuk @@M4@@ adalah @@M5@@, sedangkan jika @@M6@@ diketahui, penduga metode momen untuk @@M7@@ adalah @@M8@@. Tak satu pun penduga ini merupakan fungsi dari statistik cukup @@M9@@ sehingga semuanya kehilangan informasi. Sebaliknya, jika @@M10@@, <a href="Likelihood.html#bet">penduga kemungkinan maksimum</a> @@M11@@ pada interval @@M12@@ adalah @@M13@@, yang merupakan fungsi dari @@M14@@ (sebagaimana mestinya).</p>',
    448: '\t<p class="app">Jalankan <a href="JavaScript:openAncillary(\'../apps/BetaEstimate.html\')" class="ancillary">eksperimen pendugaan beta</a> 1000 kali dengan berbagai nilai parameter. Bandingkan dugaan parameter.</p>',
    451: '<h4 id="par">Distribusi Pareto</h4>',
    453: '<p>Ingat bahwa <a href="../special/Pareto.html">distribusi Pareto</a> dengan parameter bentuk @@M1@@ dan parameter skala @@M2@@ merupakan distribusi kontinu pada @@M3@@ dengan fungsi kepadatan probabilitas @@M4@@ yang diberikan oleh',
    455: 'Distribusi Pareto, dinamai menurut <a href="JavaScript:openAncillary(\'../biographies/Pareto.html\')" class="ancillary">Vilfredo Pareto</a>, berekor berat dan sering digunakan untuk memodelkan pendapatan serta beberapa jenis variabel acak lain.</p>',
    458: '\t<p class="math">Misalkan @@M1@@ merupakan sampel acak dari distribusi Pareto dengan parameter bentuk @@M2@@ dan parameter skala @@M3@@. Maka @@M4@@ cukup minimal untuk @@M5@@, dengan @@M6@@ merupakan hasil kali peubah sampel dan @@M7@@ merupakan <a href="../sample/OrderStatistics.html">statistik terurut</a> pertama.</p>',
    461: '\t\t<p>PDF bersama @@M1@@ pada @@M2@@ di titik @@M3@@ diberikan oleh',
    460: '\t\t<summary>Rincian:</summary>',
    463: '\t\t\tyang dapat ditulis ulang sebagai',
    465: '\t\t\tJadi hasilnya mengikuti teorema faktorisasi <a href="#fac" class="ref"></a>. Kecukupan minimal mengikuti dari <a href="#min2" class="ref"></a>.</p>',
    469: '<p>Bukti <a href="#par1" class="ref"></a> juga menunjukkan bahwa @@M1@@ cukup untuk @@M2@@ jika @@M3@@ diketahui (yang sering terjadi), dan @@M4@@ cukup untuk @@M5@@ jika @@M6@@ diketahui (jauh lebih jarang). Ingat bahwa penduga metode momen untuk @@M7@@ dan @@M8@@ adalah',
    471: 'berturut-turut, dengan @@M1@@ sebagai rata-rata sampel dan @@M2@@ sebagai momen sampel orde kedua. Kedua penduga ini bukan fungsi dari statistik cukup sehingga kehilangan informasi. Sebaliknya, penduga kemungkinan maksimum untuk @@M3@@ dan @@M4@@ pada interval @@M5@@ adalah',
    473: 'berturut-turut (baris pertama untuk (a), baris kedua untuk (b)). Penduga-penduga ini merupakan fungsi dari statistik cukup, sebagaimana mestinya.</p>',
    476: '\t<p class="app">Jalankan <a href="JavaScript:openAncillary(\'../apps/ParetoEstimate.html\')" class="ancillary">eksperimen pendugaan Pareto</a> 1000 kali dengan berbagai nilai parameter @@M1@@ dan @@M2@@ serta ukuran sampel @@M3@@. Bandingkan penduga metode momen dengan penduga kemungkinan maksimum berdasarkan bias empiris dan galat kuadrat rata-rata.</p>',
    479: '<h4 id="uni">Distribusi Seragam</h4>',
    481: '<p>Ingat bahwa <a href="../special/UniformContinuous.html">distribusi seragam kontinu</a> pada interval @@M1@@, dengan @@M2@@ sebagai parameter lokasi dan @@M3@@ sebagai parameter skala, memiliki fungsi kepadatan probabilitas @@M4@@ yang diberikan oleh',
    483: 'Distribusi seragam kontinu banyak digunakan dalam penerapan untuk memodelkan bilangan yang dipilih <q>secara acak</q> dari suatu interval. Pertama-tama, pertimbangkan kasus ketika kedua parameter tidak diketahui.</p>',
    486: '\t<p class="math">Misalkan @@M1@@ merupakan sampel acak dari distribusi seragam pada interval @@M2@@. Maka @@M3@@ cukup minimal untuk @@M4@@, dengan @@M5@@ merupakan <a href="../sample/OrderStatistics.html" class="main">statistik terurut</a> pertama dan @@M6@@ merupakan statistik terurut terakhir.</p>',
    489: '\t\t<p>PDF @@M1@@ dari @@M2@@ diberikan oleh',
    488: '\t\t<summary>Rincian:</summary>',
    491: '\t\tKita dapat menulis ulang PDF tersebut sebagai',
    493: '\t\tDari teorema faktorisasi <a href="#fac" class="ref"></a>, @@M1@@ cukup untuk @@M2@@. Selanjutnya, misalkan @@M3@@, dengan @@M4@@ atau @@M5@@. Untuk suatu @@M6@@, kita dapat dengan mudah menemukan nilai @@M7@@ sehingga @@M8@@ dan @@M9@@, serta nilai @@M10@@ lain sehingga @@M11@@. Menurut <a href="#min2" class="ref"></a>, @@M12@@ cukup minimal.</p>',
    497: '<p>Jika parameter lokasi @@M1@@ diketahui, statistik terurut terbesar cukup untuk parameter skala @@M2@@. Namun, jika parameter skala @@M3@@ diketahui, kita tetap memerlukan kedua statistik terurut untuk parameter lokasi @@M4@@. Jadi dalam kasus ini hanya ada satu parameter bernilai riil, tetapi statistik cukup minimalnya merupakan pasangan variabel acak bernilai riil.</p>',
    500: '\t<p class="math">Misalkan lagi @@M1@@ merupakan sampel acak dari distribusi seragam pada interval @@M2@@.</p>',
    502: '\t\t<li>Jika @@M1@@ diketahui, maka @@M2@@ cukup untuk @@M3@@.</li>',
    503: '\t\t<li>Jika @@M1@@ diketahui, maka @@M2@@ cukup minimal untuk @@M3@@.</li>',
    506: '\t\t<summary>Rincian:</summary>',
    507: '\t\t<p>Kedua bagian mengikuti langsung dari analisis dalam bukti <a href="#uni1" class="ref"></a>.</p>',
    512: '\t<p class="app">Jalankan <a href="JavaScript:openAncillary(\'../apps/UniformEstimate.html\')" class="ancillary">eksperimen pendugaan seragam</a> 1000 kali dengan berbagai nilai parameter. Bandingkan dugaan parameter.</p>',
    515: '<p>Ingat bahwa jika kedua parameter tidak diketahui, <a href="Moments.html#uni">penduga metode momen</a> untuk @@M1@@ dan @@M2@@ adalah @@M3@@ dan @@M4@@, berturut-turut, dengan @@M5@@ sebagai rata-rata sampel dan @@M6@@ sebagai varians sampel berbias. Jika @@M7@@ diketahui, penduga metode momen untuk @@M8@@ adalah @@M9@@, sedangkan jika @@M10@@ diketahui, penduga metode momen untuk @@M11@@ adalah @@M12@@. Tak satu pun penduga ini merupakan fungsi dari statistik cukup minimal, sehingga mengakibatkan kehilangan informasi.</p>',
    517: '<h4 id="hyp">Model Hipergeometrik</h4>',
    519: '<p>Sejauh ini, dalam semua contoh kita, peubah dasar membentuk sampel acak dari suatu distribusi. Dalam subbagian ini, peubah dasar kita akan saling bergantung.</p>',
    521: '<p>Ingat bahwa dalam <dfn>model hipergeometrik</dfn> terdapat populasi berisi @@M1@@ objek; @@M2@@ objek <dfn>tipe 1</dfn> dan sisanya @@M3@@ <dfn>tipe 0</dfn>. Ukuran populasi @@M4@@ merupakan bilangan bulat positif dan ukuran tipe 1 @@M5@@ merupakan bilangan bulat nonnegatif dengan @@M6@@. Biasanya salah satu atau kedua parameter tidak diketahui. Kita memilih sampel acak @@M7@@ objek tanpa pengembalian dari populasi, dan @@M8@@ menyatakan tipe objek yang terpilih pada posisi @@M9@@. Jadi barisan dasar variabel acak kita adalah @@M10@@. Peubah-peubah ini merupakan variabel indikator berdistribusi identik dengan @@M11@@ untuk @@M12@@, tetapi saling bergantung. Tentu saja ukuran sampel @@M13@@ merupakan bilangan bulat positif dengan @@M14@@.</p>',
    523: '<p>Peubah @@M1@@ menyatakan banyaknya objek tipe 1 dalam sampel. Peubah ini berdistribusi <a href="../urn/Hypergeometric.html">hipergeometrik</a> dengan parameter @@M2@@, @@M3@@, dan @@M4@@, serta memiliki fungsi kepadatan probabilitas @@M5@@ yang diberikan oleh',
    525: '(Ingat notasi <dfn>pangkat turun</dfn> @@M1@@.)</p>',
    528: '\t<p class="math">@@M1@@ cukup untuk @@M2@@. Secara khusus, untuk @@M3@@, distribusi bersyarat @@M4@@ yang diberikan @@M5@@ seragam pada himpunan titik',
    531: '\t\t<summary>Rincian:</summary>',
    532: '\t\t<p>Dengan menerapkan aturan perkalian kombinatorika secara langsung, PDF @@M1@@ dari @@M2@@ diberikan oleh',
    534: '\t\tDengan @@M1@@. Jika @@M2@@, distribusi bersyarat @@M3@@ yang diberikan @@M4@@ terkonsentrasi pada @@M5@@ dan',
    536: '\t\tTentu saja, @@M1@@ adalah kardinalitas @@M2@@.</p>',
    540: '<p>Terdapat kemiripan kuat antara model hipergeometrik dan model percobaan Bernoulli di atas. Jika pengambilan sampel dilakukan <em>dengan pengembalian</em>, model percobaan Bernoulli dengan @@M1@@ akan berlaku, bukan model hipergeometrik. Menarik pula bahwa satu statistik bernilai riil cukup untuk dua parameter bernilai riil.</p>',
    542: '<p>Sekali lagi, rata-rata sampel @@M1@@ ekuivalen dengan @@M2@@ sehingga juga cukup untuk @@M3@@. Ingat bahwa penduga metode momen bagi @@M4@@ ketika @@M5@@ diketahui adalah @@M6@@, sedangkan penduga metode momen bagi @@M7@@ ketika @@M8@@ diketahui adalah @@M9@@. Penduga @@M10@@ digunakan dalam eksperimen tangkap-tangkap kembali.</p>',
    544: '<h4>Keluarga Eksponensial</h4>',
    546: '<p>Misalkan sekarang vektor data @@M1@@ bernilai di himpunan @@M2@@, dan distribusi @@M3@@ bergantung pada vektor parameter @@M4@@ yang bernilai di ruang parameter @@M5@@. Distribusi @@M6@@ merupakan <a href="../special/GeneralExponential.html">keluarga eksponensial</a> dengan @@M7@@ parameter jika @@M8@@ tidak bergantung pada @@M9@@ dan fungsi kepadatan probabilitas dari @@M10@@ dapat ditulis sebagai',
    548: 'dengan @@M1@@ dan @@M2@@ merupakan fungsi bernilai riil pada @@M3@@, sedangkan @@M4@@ dan @@M5@@ merupakan fungsi bernilai riil pada @@M6@@. Selain itu, @@M7@@ dianggap sebagai bilangan bulat terkecil yang memenuhi bentuk tersebut. Vektor parameter @@M8@@ kadang disebut <dfn>parameter alami</dfn> distribusi, sedangkan vektor acak @@M9@@ kadang disebut <dfn>statistik alami</dfn>. Walaupun definisinya tampak mengintimidasi, keluarga eksponensial berguna karena memiliki banyak sifat matematis yang baik dan karena banyak keluarga parametrik khusus merupakan keluarga eksponensial. Contoh keluarga yang dibahas di atas adalah Bernoulli pada <a href="#ber" class="ref"></a>, Poisson pada <a href="#poi" class="ref"></a>, gamma pada <a href="#gam" class="ref"></a>, normal pada <a href="#nor" class="ref"></a>, dan beta pada <a href="#bet" class="ref"></a>. Pareto pada <a href="#par" class="ref"></a> dibahas di atas, tetapi tidak termasuk dalam klaim keluarga eksponensial dengan dukungan tetap karena dukungannya bergantung pada parameter. Untuk klaim kecukupan minimal berikut, kita memakai keluarga eksponensial penuh dengan ruang parameter alami yang memuat himpunan terbuka.</p>',
    551: '\t<p class="math">Dalam keluarga eksponensial penuh tersebut, @@M1@@ cukup minimal untuk @@M2@@.</p>',
    553: '\t\t<summary>Rincian:</summary>',
    554: '\t\t<p>Bahwa @@M1@@ cukup untuk @@M2@@ segera mengikuti dari teorema faktorisasi <a href="#fac" class="ref"></a>. Untuk keluarga eksponensial penuh dengan ruang parameter alami yang memuat himpunan terbuka, kecukupan minimal bagi @@M3@@ mengikuti kriteria rasio pada teorema kecukupan minimal; sekadar memilih jumlah parameter @@M4@@ sebagai bilangan bulat terkecil tidak cukup tanpa syarat ini. Klaim tersebut harus dibaca dalam kondisi tersebut.</p>',
    558: '<p>Dalam keluarga eksponensial penuh dengan ruang parameter alami yang memuat himpunan terbuka, @@M1@@ juga lengkap untuk @@M2@@, meskipun buktinya lebih sulit. Tanpa syarat ruang parameter tersebut, kelengkapan tidak otomatis.</p>',
    562: '\t\t<li class="parent"><a href="../index.html">Random</a></li>',
    563: '\t\t<li class="parent"><a href="index.html">6. Pendugaan Titik</a></li>',
    564: '\t\t<li class="child"><a href="Estimators.html" title="Penduga">1</a></li>',
    565: '\t\t<li class="child"><a href="Moments.html" title="Metode Momen">2</a></li>',
    566: '\t\t<li class="child"><a href="Likelihood.html" title="Kemungkinan Maksimum">3</a></li>',
    567: '\t\t<li class="child"><a href="Bayes.html" title="Penduga Bayes">4</a></li>',
    568: '\t\t<li class="child"><a href="Unbiased.html" title="Penduga Tak Bias Terbaik">5</a></li>',
    570: '\t\t<li class="details"><button type="button" title="Perluas Rincian" onclick="expandDetails(true);"><img src="../icons/Plus.svg" alt="Perluas"></button></li>',
    571: '\t\t<li class="details"><button type="button" title="Ciutkan Rincian" onclick="expandDetails(false);"><img src="../icons/Minus.svg" alt="Ciutkan"></button></li>',
    574: '\t\t<li class="sister"><a href="JavaScript:openAncillary(\'../apps/index.html\')" class="ancillary">Aplikasi</a></li>',
    575: '\t\t<li class="sister"><a href="JavaScript:openAncillary(\'../data/index.html\')" class="ancillary">Himpunan Data</a></li>',
    576: '\t\t<li class="child"><a href="JavaScript:openAncillary(\'../biographies/index.html\')" class="ancillary">Biografi</a></li>',
}


# Exact, bounded repairs to the frozen authority.  These are mathematical,
# typographical, or structural defects; no other source bytes are changed.
BOUNDED_FIXES: dict[int, tuple[tuple[str, str], ...]] = {
    73: (("suffcient", "sufficient"),),
    88: (
        (r"a positive constant \( C \)", r"a positive function \( c(y) \)"),
        (r"\( h_\theta(y) = C G(y, \theta) \)", r"\( h_\theta(y) = c(y) G(y, \theta) \)"),
        (r"u(x)", r"u(\bs{x})"),
        (r"r(\bs x) / C", r"r(\bs x) / c[u(\bs{x})]"),
    ),
    110: (
        (r"\text{ is independent of }", r"\text{ tidak bergantung pada }"),
        (r"\text{ if and only if }", r"\text{ jika dan hanya jika }"),
    ),
    115: ((r"\theta \in \Theta", r"\theta \in T"),),
    159: ((r"\theta \in \Theta", r"\theta \in T"),),
    167: (
        (r"\E_\theta\left[r(U)\right] = 0 \text{ for all }", r"\E_\theta\left[r(U)\right] = 0 \text{ untuk semua }"),
        (r"\P_\theta\left[r(U) = 0\right] = 1 \text{ for all }", r"\P_\theta\left[r(U) = 0\right] = 1 \text{ untuk semua }"),
    ),
    214: (("langauage", "language"),),
    237: ((r"\binom{n}{k}", r"\binom{n}{y}"),),
    250: (("homogenous", "homogeneous"),),
    254: (("maximum likelihood</a>0\\ estimator", "maximum likelihood</a> estimator"),),
    283: (("g(x_1) g(x_2) \\cdot g(x_n)", "g(x_1) g(x_2) \\cdots g(x_n)"),),
    334: ((r"x_2 \ldots, x_n)", r"x_2, \ldots, x_n)"),),
    336: (
        (r"x_2 \ldots, x_n)", r"x_2, \ldots, x_n)"),
        (r"e^{-n \mu^2 / \sigma^2}", r"e^{-n \mu^2 / (2 \sigma^2)}"),
        (r"+ \frac{2 \mu}{\sigma^2} \sum_{i=1}^n x_i", r"+ \frac{\mu}{\sigma^2} \sum_{i=1}^n x_i"),
    ),
    361: (("This results", "This result"),),
    362: (("theoren", "theorem"),),
    373: (("proccess", "process"),),
    410: (("id=\"gam2\"", "id=\"gam3\""),),
    419: ((r"\bs{Z} = (Z_1, X_2, \ldots, Z_n)", r"\bs{Z} = (Z_1, Z_2, \ldots, Z_n)"),),
    439: ((r"\( (U, V) \)", r"\( (P, Q) \)"),),
    471: ((r"M^{(2)} = \sum_{i=1}^n X_i^2", r"M^{(2)} = \frac{1}{n} \sum_{i=1}^n X_i^2"), ("hence suffers", "hence suffer")),
    486: (("class=\"mian\"", "class=\"main\""),),
    490: ((r"x_2, \ldots x_n)", r"x_2, \ldots, x_n)"),),
    515: ((r"while if \( h \) is known, the method of moments estimator of \( h \) is", r"while if \( h \) is known, the method of moments estimator of \( a \) is"),),
    524: ((r"N - n + r", r"n - N + r"),),
    528: ((r"N - n + r", r"n - N + r"),),
    534: ((r"N - n + r", r"n - N + r"),),
    464: ((r"\bs{1}\left(x_{(n)} \ge b\right)", r"\bs{1}\left(x_{(1)} \ge b\right)"),),
}

# Native Random anchors are retained.  Units that had no upstream id receive
# deterministic additive IDs so the backend can address every instructional
# unit without changing the source's reading order.
GENERATED_UNIT_ORDINALS = (2, 4, 7, 11, 12, 14, 16, 19, 20, 21, 22, 23, 25, 28, 32, 34, 37, 38, 39)
GENERATED_UNIT_IDS = {
    f"o006.random.point.sufficient.unit-{ordinal:02d}"
    for ordinal in GENERATED_UNIT_ORDINALS
}


LOCAL_URLS = {
    "https://www.randomservices.org/random/icons/Icon.svg": "../icons/Icon.svg",
    "https://www.randomservices.org/random/Screen.css": "../Screen.css",
    "https://www.randomservices.org/random/point/index.html": "index.html",
    "https://www.randomservices.org/random/point/Estimators.html": "Estimators.html",
    "https://www.randomservices.org/random/point/Moments.html": "Moments.html",
    "https://www.randomservices.org/random/point/Likelihood.html": "Likelihood.html",
    "https://www.randomservices.org/random/point/Bayes.html": "Bayes.html",
    "https://www.randomservices.org/random/point/Unbiased.html": "Unbiased.html",
    "https://www.randomservices.org/random/sample/index.html": "../sample/index.html",
    "https://www.randomservices.org/random/sample/Introduction.html": "../sample/Introduction.html",
    "https://www.randomservices.org/random/sample/Mean.html": "../sample/Mean.html",
    "https://www.randomservices.org/random/sample/LLN.html": "../sample/LLN.html",
    "https://www.randomservices.org/random/sample/CLT.html": "../sample/CLT.html",
    "https://www.randomservices.org/random/sample/Variance.html": "../sample/Variance.html",
    "https://www.randomservices.org/random/sample/OrderStatistics.html": "../sample/OrderStatistics.html",
    "https://www.randomservices.org/random/sample/Covariance.html": "../sample/Covariance.html",
    "https://www.randomservices.org/random/sample/Normal.html": "../sample/Normal.html",
    "https://www.randomservices.org/random/interval/index.html": "../interval/index.html",
}


EDITION_NOTICE = """
    <section class="edition-notice" data-o006-edition-notice="v1">
        <p><strong>Pemberitahuan edisi.</strong> Terjemahan Bahasa Indonesia ini mengadaptasi <a href="https://www.randomservices.org/random/">Random: Probabilitas, Statistika Matematis, dan Proses Stokastik</a> karya Kyle Siegrist. Perubahan pada halaman ini mencakup penerjemahan, penambahan ID stabil, pengalihan tautan inti yang telah diterjemahkan ke edisi lokal, pengalihan tautan inti yang belum diterjemahkan ke sumber resmi, pengubahan tautan pelengkap menjadi tautan HTTPS resmi, serta koreksi terbatas terhadap kekeliruan matematis, ejaan, dan struktur yang dicatat dalam daftar koreksi edisi.</p>
        <p>Situs asal menyatakan <a href="https://creativecommons.org/licenses/by/2.0/">CC BY 2.0</a>, sedangkan halaman <a href="https://www.randomservices.org/random/Credits.html">Kredit</a> menautkan <a href="https://creativecommons.org/licenses/by/1.0/">CC BY 1.0</a>; perbedaan ini dipertahankan. Edisi independen ini tidak didukung maupun disahkan oleh Kyle Siegrist atau Random Services. Tautan ke aplikasi, data, dan biografi pihak ketiga tidak menyatakan hak untuk mendistribusikan ulang materi tersebut.</p>
     </section>"""


def render_template(line_number: int, source_line: str, template: str) -> str:
    spans = MATH_RE.findall(source_line)
    tokens = [int(value) for value in TOKEN_RE.findall(template)]
    if tokens != list(range(1, len(spans) + 1)):
        raise RuntimeError(
            f"line {line_number}: placeholders {tokens} do not match {len(spans)} TeX spans"
        )
    rendered = template
    for index, span in enumerate(spans, start=1):
        rendered = rendered.replace(f"@@M{index}@@", span, 1)
    return rendered


def apply_bounded_fixes(line_number: int, text: str) -> str:
    for old, new in BOUNDED_FIXES.get(line_number, ()):
        if text.count(old) != 1:
            raise RuntimeError(
                f"line {line_number}: expected one exact defect, found {text.count(old)}: {old!r}"
            )
        text = text.replace(old, new, 1)
    return text


def convert_href(raw_href: str) -> str:
    if raw_href.startswith("#"):
        return raw_href
    ancillary = re.fullmatch(r"JavaScript:openAncillary\('([^']+)'\)", raw_href, re.I)
    candidate = ancillary.group(1) if ancillary else raw_href
    absolute = urljoin(SOURCE_URL, candidate)
    base, fragment = urldefrag(absolute)
    result = LOCAL_URLS.get(
        base, base.replace("http://www.randomservices.org/", "https://www.randomservices.org/")
    )
    return result + (f"#{fragment}" if fragment else "")


def assert_topology(source_text: str, target_text: str) -> None:
    for pattern in (
        r'<div class="unit" id="[^"]+">',
        r"<details>",
        r"<summary>",
        r'<ol class="sub">',
        r'<h3(?: id="[^"]+")?>',
        r'<h4(?: id="[^"]+")?>',
    ):
        source_count = len(re.findall(pattern, source_text))
        target_count = len(re.findall(pattern, target_text))
        if pattern == r'<div class="unit" id="[^"]+">':
            source_count += len(GENERATED_UNIT_IDS)
        if target_count != source_count:
            raise RuntimeError(
                f"topology mismatch for {pattern!r}: source {source_count}, target {target_count}"
            )
    source_ids = set(re.findall(r'\bid="([^"]+)"', source_text))
    target_ids = set(re.findall(r'\bid="([^"]+)"', target_text))
    expected_ids = (source_ids - {"o006.random.point.sufficient.page"}) | {
        "o006.random.point.sufficient.page",
        "the",
        "exa",
        "gam3",
    } | GENERATED_UNIT_IDS
    if target_ids != expected_ids:
        raise RuntimeError(
            f"native-ID mismatch: missing {sorted(expected_ids - target_ids)}, "
            f"extra {sorted(target_ids - expected_ids)}"
        )


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    if len(source_bytes) != EXPECTED_SOURCE_BYTES:
        raise RuntimeError(f"authority byte-count mismatch: {len(source_bytes)}")
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != SOURCE_SHA256:
        raise RuntimeError(f"authority hash mismatch: {digest}")
    lines = source_bytes.decode("utf-8").splitlines(keepends=True)
    if len(lines) != EXPECTED_SOURCE_LINES:
        raise RuntimeError(f"unexpected authority line count: {len(lines)}")
    for line_number, template in sorted(T.items()):
        source = lines[line_number - 1]
        ending = "\r\n" if source.endswith("\r\n") else "\n" if source.endswith("\n") else ""
        source = apply_bounded_fixes(line_number, source.removesuffix(ending))
        lines[line_number - 1] = render_template(
            line_number, source, template
        ) + ending
    for line_number in sorted(set(BOUNDED_FIXES) - set(T)):
        source = lines[line_number - 1]
        ending = "\r\n" if source.endswith("\r\n") else "\n" if source.endswith("\n") else ""
        lines[line_number - 1] = apply_bounded_fixes(
            line_number, source.removesuffix(ending)
        ) + ending
    text = "".join(lines)
    unit_ordinal = 0

    def add_unit_id(match: re.Match[str]) -> str:
        nonlocal unit_ordinal
        unit_ordinal += 1
        if match.group(1):
            return match.group(0)
        return f'<div class="unit" id="o006.random.point.sufficient.unit-{unit_ordinal:02d}">' 

    text = re.sub(r'<div class="unit"(?: id="([^"]+)")?>', add_unit_id, text)
    if unit_ordinal != 39:
        raise RuntimeError(f"unexpected Sufficient unit count: {unit_ordinal}")
    text = re.sub(
        r'href="([^"]+)"',
        lambda match: f'href="{convert_href(match.group(1))}"',
        text,
    )
    marker = "\n</footer>"
    if text.count(marker) != 1:
        raise RuntimeError("footer insertion point is not unique")
    text = text.replace(marker, EDITION_NOTICE + marker, 1)

    source_text = source_bytes.decode("utf-8")
    expected_math_text = source_text
    for line_number in sorted(BOUNDED_FIXES):
        source_line = expected_math_text.splitlines(keepends=True)[line_number - 1]
        ending = "\r\n" if source_line.endswith("\r\n") else "\n" if source_line.endswith("\n") else ""
        repaired = apply_bounded_fixes(line_number, source_line.removesuffix(ending)) + ending
        expected_lines = expected_math_text.splitlines(keepends=True)
        expected_lines[line_number - 1] = repaired
        expected_math_text = "".join(expected_lines)
    if MATH_RE.findall(text) != MATH_RE.findall(expected_math_text):
        raise RuntimeError("delimited TeX inventory differs from the bounded repaired authority")
    output_lines = text.splitlines()
    for line_number, repairs in BOUNDED_FIXES.items():
        output_line = output_lines[line_number - 1]
        for old, new in repairs:
            if old in output_line or (line_number not in T and output_line.count(new) < 1):
                raise RuntimeError(
                    f"line {line_number}: bounded repair not unique: {old!r} -> {new!r}"
                )
    assert_topology(source_text, text)

    required_links = (
        'href="index.html"', 'href="Estimators.html"', 'href="Moments.html"',
        'href="Likelihood.html"', 'href="Bayes.html"', 'href="Unbiased.html"',
        'href="../sample/Introduction.html"', 'href="../sample/CLT.html"',
        'href="../sample/OrderStatistics.html"',
    )
    for link in required_links:
        if link not in text:
            raise RuntimeError(f"required navigation target missing: {link}")
    if 'href="Sufficient.html"' in text:
        raise RuntimeError("future Sufficient page was incorrectly routed locally")
    for phrase in (
        '<html lang="en">', "JavaScript:openAncillary", "Expand Details",
        "Contract Details", ">Details:<", ">Sufficient Statistics<",
        ">Minimal Sufficient Statistics<", ">Properties of Sufficient Statistics<",
        ">Complete Statistics<", ">Ancillary Statistics<", ">Basic Theory<",
        ">Applications and Special Distributions<", ">The Bernoulli Distribution<",
        ">The Poisson Distribution<", ">The Normal Distribution<",
        ">The Gamma Distribution<", ">The Beta Distribution<", ">The Pareto Distribution<",
        ">The Uniform Distribution<", ">The Hypergeometric Model<", ">Exponential Families<",
        ">Apps<", ">Data Sets<", "> Biographies<", "suffcient", "langauage",
        "homogenous", "proccess", "theoren", "mian", "maximum likelihood</a>0",
        "\u0028U, V\u0029 is sufficient", " N - n + r", "#ber\"> considered above",
    ):
        if phrase in text:
            raise RuntimeError(f"untranslated or unsafe phrase remains: {phrase}")
    controls = [char for char in text if ord(char) < 32 and char not in "\t\r\n"]
    if controls:
        raise RuntimeError(f"forbidden control characters: {sorted(map(ord, controls))}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(text.encode("utf-8"))
    output = TARGET.read_bytes()
    print(
        f"WROTE {TARGET.relative_to(ROOT).as_posix()}: "
        f"{len(output)} bytes / sha256 {hashlib.sha256(output).hexdigest()}"
    )


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
