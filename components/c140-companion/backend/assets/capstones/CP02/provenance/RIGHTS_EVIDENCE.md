# Bukti hak dan pemisahan lisensi CP02

## Kesimpulan

Dua aset yang dibekukan untuk CP02, `raw/nest_propensity.csv` dan
`raw/README.md`, merupakan bagian dari versi 3 deposit Dryad
`10.5061/dryad.573n5tbf3` dan ditandai **CC0-1.0**. Dedikasi CC0 membolehkan
penyalinan, redistribusi, dan pembuatan turunan tanpa syarat atribusi lisensi.
Sitasi ilmiah tetap diberikan sebagai tata krama akademik dan untuk menjaga
rantai provenans.

## Saksi primer yang dibekukan

1. `witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json` adalah respons API
   dataset Dryad. Field `license` menunjuk
   `https://spdx.org/licenses/CC0-1.0.html`, sementara relasi versi menunjuk
   version ID `268230`.
2. `witnesses/datacite-doi-10.5061-dryad.573n5tbf3.json` adalah metadata DOI
   DataCite. `rightsList` menyatakan `Creative Commons Zero v1.0 Universal`,
   pengenal `cc0-1.0`, dan URL legal code
   `https://creativecommons.org/publicdomain/zero/1.0/legalcode`.
3. `witnesses/doi-10.5061-dryad.573n5tbf3-resolved.html` adalah hasil resolusi
   DOI ke landing page Dryad. Metadata terstruktur pada halaman itu menyatakan
   nama lisensi dan URL SPDX CC0-1.0 untuk record yang sama, serta memuat tautan
   publik file ID `2765112` dan `2765118`.
4. `witnesses/dryad-reuse-guide.html` adalah panduan reuse Dryad yang
   menjelaskan bahwa dataset Dryad dipublikasikan di bawah dedikasi domain
   publik CC0 dan menganjurkan sitasi walaupun atribusi bukan kewajiban CC0.
5. `witnesses/cc0-1.0-legalcode.html` adalah legal code Creative Commons yang
   ditunjuk metadata DataCite.

Ukuran, SHA-256, URL pengambilan, waktu pengambilan, MIME, dan encoding setiap
saksi dicatat di `DATASET_PROVENANCE.json`; identitas kedua input dicatat lagi
secara tabular di `INPUT_MANIFEST.csv`.

## Lingkup dan pemisahan

Freeze ini hanya mengimpor CSV hitungan agregat per tipe pemancar × tahun dan
README-nya. Tidak ada file encounter-history, nest-level, atau microdata
individual lain dari deposit yang diimpor.

Pernyataan tersebut membatasi **data analitik**, bukan setiap byte saksi
provenans. Dua respons API penerbit yang dibekukan, yaitu
`witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json` dan
`witnesses/version-268230.json`, mempertahankan metadata pencipta yang
dipublikasikan Dryad, termasuk satu entri email dan satu ORCID yang tidak
kosong pada masing-masing respons. Field itu dipertahankan hanya untuk
provenans dan atribusi; field tersebut bukan baris analitik, microdata subjek
studi, atau input model CP02.

CC0-1.0 tetap melekat secara terpisah pada byte sumber di `raw/`. Teks
pendamping CP02 yang orisinal memakai CC BY-SA 4.0. Lisensi pendamping tersebut
tidak diterapkan pada, tidak menggantikan, dan tidak mempersempit status CC0
aset Dryad.

Sitasi dataset yang dipertahankan:

> Stevens, Bryan; Conway, Courtney; Tisdale, Cody; Denny, Kylie; Meyers,
> Andrew; Makela, Paul (2023). *Supporting data for assessing impacts of
> satellite GPS transmitters on survival, nesting propensity, and nest success
> of greater sage-grouse*. Dryad, Dataset.
> https://doi.org/10.5061/dryad.573n5tbf3
