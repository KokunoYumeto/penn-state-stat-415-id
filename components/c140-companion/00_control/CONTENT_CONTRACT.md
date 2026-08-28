# Kontrak sumber pendamping C140

Setiap berkas Markdown dimulai dengan tiga baris: `---`, satu objek JSON, dan
`---`. Kunci wajib: `id`, `type`, `title`, `locale`, `license`, `provenance`,
`prerequisites`, `objectives`, `relations`, dan `status`. ID tidak boleh memuat
judul terjemahan. Nilai tetap locale `id-ID`, license `CC-BY-SA-4.0`, dan
provenance `OpenAI Codex gpt-5.6-sol, Ultra`.

Setiap heading substantif didahului `<a id="ID"></a>`. Pola tipe anchor:
`SEC`, `DEF`, `ASM`, `THM`, `PRF`, `EX`, `CTR`, `ALG`, `REM`, `SIM`, `P`,
`H`, `ANS`, `SOL`, dan `RUB`. Referensi internal ditulis `[ref:ID]`; build
mengubahnya menjadi tautan dan hard-fail bila target tidak ada.

Set mastery wajib mempunyai tepat delapan atau lebih anchor masalah `-P01`,
`-P02`, dan seterusnya. Setelah setiap masalah harus ada metadata satu baris:
`<!--PROBLEM_META {"id":"...","prerequisites":[...],"objective":"...","difficulty":"...","misconceptions":[...]}-->`
diikuti sekurangnya dua petunjuk `-H01`/`-H02`, jawaban singkat `-ANS`, dan
solusi lengkap `-SOL`. Asesmen memakai kontrak yang sama dan menambah rubrik
`-RUB`. Solusi tidak boleh hanya menunjuk output perangkat lunak.

Simulasi mempunyai ID stabil, seed eksplisit, lingkungan terkunci, assertion
numerik, output CSV dan SVG/teks statis, serta deskripsi aksesibel. Tidak ada
runtime jaringan atau browser. Semua file teks UTF-8 dengan LF.
