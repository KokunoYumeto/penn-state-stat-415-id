# Catatan penerjemahan Lesson 02 — bagian C

## Cakupan

- Segmen: `O006-PSU-003-S0217` hingga `O006-PSU-003-S0324` (108 ID berurutan).
- Terminologi mengikuti `00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv`, khususnya *estimator* → “penduga”, *estimation* → “pendugaan”, *expectation/expected value* → “nilai harapan”, *mean* → “rataan”, dan *mean square(d) error* → “rataan kuadrat galat (MSE)”.
- Teks sumber, simpul matematika, ID, dan berkas otoritas tidak diubah.

## Cacat rumus sumber yang dipertahankan

Rumus berikut berada dalam simpul matematika yang dilindungi. Terjemahan prosa mengikuti makna teks sumber, sedangkan rumus tidak diperbaiki dalam berkas terjemahan ini.

1. `O006-PSU-003-M0152` tampaknya memakai pangkat `1−θ` pada suku kedua hasil integrasi parsial; berdasarkan integrannya, pangkat yang konsisten adalah `1/θ`.
2. `O006-PSU-003-M0160` menyebut parameter `θ`, padahal ketiga penduga dalam contoh tersebut adalah penduga untuk parameter binomial `p`.
3. `O006-PSU-003-M0177` kehilangan tanda kurung tutup pada `Var(p̂₂)`.
4. `O006-PSU-003-M0200` menuliskan `MSE = Var − Bias²`. Identitas bakunya menggunakan tanda tambah: `MSE = Var + Bias²`. Selain itu, ruas bias pada tampilan memakai `Bias(θ)`, sedangkan prosa sesudahnya dan definisi yang dimaksud merujuk pada bias penduga `Bias(θ̂)`.
5. `O006-PSU-003-M0208` kembali mengurangkan kuadrat bias pada ketiga baris MSE. Tanda yang benar adalah tambah. Dengan tanda tambah, simpulan prosa pada segmen `O006-PSU-003-S0306` bahwa penduga kedua memiliki MSE terkecil konsisten; dengan tanda kurang yang ditampilkan, baris penduga ketiga justru bertentangan dengan simpulan tersebut. Ketiga ekspresi `Bias(...)` pada tampilan ini juga memiliki pasangan tanda kurung/siku yang tidak serasi; hasil baris penduga ketiga seharusnya berakhir dengan `+0.01`, bukan `−0.01`.
