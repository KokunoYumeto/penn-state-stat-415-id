# Current state — original C140 companion

Updated: 2026-08-31

## C5 asesmen dan capstone — sumber, build, dan QA lengkap; pengemasan aktif

Seluruh 39 dokumen sumber `id-ID` lengkap, termasuk `CA02`–`CA04` dan
`CP01`–`CP02`. Produksi sumber selesai sebelum audit. Keempat asesmen dan
kedua capstone telah lulus pemeriksaan matematika, bahasa, solusi, rubrik,
hak, dan binding hasil. Seluruh angka hasil capstone terikat pada keluaran
analisis deterministik; tidak ada template inert atau status `draft`.
Identitas lima dokumen C5 yang dihitung ulang tercatat dalam
`C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md`.

Data `CP01` telah dibekukan dari UCI Concrete Compressive Strength di bawah CC
BY 4.0; data `CP02` telah dibekukan dari Dryad v3 Greater sage-grouse nesting
propensity di bawah CC0. Byte mentah, bukti hak, provenans, schema, dan
transformasi lokal berada di `data/capstones/CP01/` dan `CP02/`. Transformasi,
analisis, aset CSV/SVG/teks aksesibel, dan manifest sudah lengkap. Koreksi
pascaaudit menyamakan simbol agregat CP01, menerjemahkan teks SVG SIM001–SIM005,
memperbaiki hierarki heading SIM005/SIM006, dan menutup kasus batas matematis
serta kerusakan TeX pada set penguasaan. Pembacaan akhir MS09–MS12 lulus;
jangan mengulang terjemahan atau audit sumber yang telah selesai.

Belum ada publikasi C5: C4 tetap batas publik terakhir. Build HTML/backend
dan QA C5 sekarang lulus write dan dua replay check-only; koleksi Pages
259 berkas juga lulus. Pendamping memuat 146 soal terselesaikan, 1.523 entitas,
dan 1.949 relasi. Identitas lengkap tercatat dalam
`CHECKPOINT_2026-08-31_C5_LOCAL_COMPLETE.md`. Tindakan berikutnya adalah
membekukan paket kumulatif 65 berkas. Setelah gate lulus, publikasikan
ke lineage GitHub/Zenodo yang sudah ada dan baca balik seluruh byte secara
anonim. Larangan browser dan kontak upstream tetap berlaku.

## C4 mastery boundary — public deterministic closure

Batch C4 is complete and publicly preserved. It adds the
seven original `id-ID` mastery sets `MS00`–`MS06` without changing C1–C3.
Each set has eight nontrivial problems with stable metadata, two staged hints,
a short answer, and a complete worked solution. The cumulative source is 34
documents / 683,211 bytes / 1,057 anchors / 280 body references. Thirteen
mastery sets and `CA01` contain 114 fully solved problems.

The browser-free reader has 64 files / 3,024,784 bytes; manifest SHA-256 is
`629870245f726b01534c09f7e595e8a15cf11015a63280c0a16b056ce7cb4178`.
The backend has 1,113 entities / 1,424 relations / 359,500 bytes; manifest
SHA-256 is
`86190eddcd4cc4e99ed3adfc22a3d8391934fb940f5ec1ea1572a532df6b44e3`.
Build and QA receipt SHA-256 values are
`c21aecda780cf8e56eb82a41d19b9b0a112e81caf583f38041a5d9fd4ffc0ac1`
and `dfadcc6338ad44d9dadd13fa2f7ef19d9b9e19e428f25f3fe7607852bfa8e2e7`.
Write/check-only replay passes with browser and network use false.

The cumulative C4 preservation package passes contract/write/check replay and
an independent ZIP/inventory/inheritance/rights/privacy audit. It contains 57
files / 93,850,993 bytes: all 49 C3 files / 92,476,057 bytes remain
byte-identical and eight C4 files are appended at orders 50–57. The 34,142-byte
package receipt SHA-256 is
`45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f`.
The cumulative Pages candidate has 188 files / 22,437,587 bytes, manifest
SHA-256 `fdd057c53c7bb0a092d8ee3499b9116b9219463034c0426b5373687ba9200f90`,
and receipt SHA-256
`ef92d1871a85336890fc48798ad50d170d4de18505cc5ee8c441621fa2473d31`.

Content commit `9b10b3e04b451232b1233d0b35cf31c3860d63db` is public. All 62
changed files / 1,997,776 bytes matched immutable raw commit URLs. Static
workflow run `33264397424` passed, and two credential-free passes matched all
188 Pages files / 22,437,587 bytes. The Pages receipt SHA-256 is
`5e002a9f7926def73034a6d18686d36a257b7dd9daaf6fa6aa12db9fe764a012`.

GitHub release `379047752`, tag `v2026.08.29.c140-companion-c4`, points to
that content commit through annotated tag object
`1dd397eeb0d717046e4f31a5d65abe97c3c9567b`. Transactional and independent
direct credential-free readbacks matched all 57 assets / 93,850,993 bytes.
Publication, anonymous-readback, and direct-readback receipt SHA-256 values
are `6dd0611b227940b2a63c1fc5652c4d7d585e1f522f3a07215ac7f39348e649c8`,
`efd537d327dcd6d4a02a74c1194696c860f8f1273b88cbd6db920c81faa9598c`,
and `53235cdaf793eb5600256519eedd4becab85867e3a4a94377c39871a7708ea2f`.

Zenodo record `22164344`, DOI `10.5281/zenodo.22164344`, is public in existing
concept `22077422` / DOI `10.5281/zenodo.22077422`. Anonymous and independent
direct readbacks matched the same 57-file union. Publication, public-readback,
direct-readback, and final lineage-audit receipt SHA-256 values are
`573f155ec965e6849ed0fff0deb9a04b6ab90c38f6e34deccf0999f0fd4cf30a`,
`fe92ec27c63d8af29ea30bf46977fd8694e6febcdc3375db29f8bf2db60acf8d`,
`a8c01aa346b27d49468a41be230289c8c761b8fa94d041c92ab1467c640969d1`,
and `c02a40387634f79f0f784ed4c8e4ec4b849f5e6e88ec995fbe851914f877effb`.
The concept has exactly one matching C4 version and zero drafts.

The independent mathematical audit of all 56 C4 problems found and closed the
MS00 denominator/horizon defects, an MS01 order-statistic symbol collision, an
MS02 minimax overclaim, a missing Poisson normalization factor in MS03, the
exact MS04 finite-MLE condition, MS05 endpoint arithmetic, and an MS06
Student-t digit error. It reported all remaining numerical and algebraic
results correct. The complete local evidence is
`CHECKPOINT_2026-08-29_C4_LOCAL_COMPLETE.md`.

The complete public evidence is
`CHECKPOINT_2026-08-29_C4_PUBLICATION_COMPLETE.md`. Next executable action:
continue C5 under `C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md`, beginning with
the complete `CA02` assessment and then `CA03`, `CA04`, `CP01`, and `CP02`.
C140 remains incomplete until those five documents are closed and published.

## C3 Bayesian–frequentist boundary — public deterministic closure

Batch C3 is complete and publicly preserved. It adds `D012`, `D013`, `SIM006`, and `MS11`
without changing C1/C2. The cumulative source is 27 documents / 528,082 bytes
/ 763 anchors / 251 body references. Six mastery sets and `CA01` contain 58
fully solved problems. The reader has 57 files / 2,713,731 bytes; manifest
SHA-256 is
`18b3ab09539eee0baa355dcb7f7edc2cec00f0960c5508a9419bf2bde7bb1273`.
The backend has 812 entities / 1,084 relations / 269,101 bytes; manifest
SHA-256 is
`2c5b84d662713a037b512a6751dd9e8e7eb2504a69141d6268993db859e83d66`.
Build, QA, and C3 simulation receipt SHA-256 values are
`79661673ad7f4d74eff997cebd6fca1f46d2a74cbab5930147ca109762ef37ca`,
`6f53a1f54d3a1b3e23b874a3c13adda9726bc0a8456d2fb4a8315d11912f72d7`,
and `c7f176380b2e30b9931cc44bcc2e39bb541559030cf65b1c41f32045c13b1040`.
Static write/check replay passes.

Independent audits checked the D012/D013 hypotheses and derivations, SIM006
numerics/accessibility, all eight MS11 solutions, generated-directory closure,
receipt identity, IDs/relations, and browser/network gates. All bounded
findings were repaired. The cumulative Pages candidate has 181 files /
22,126,534 bytes, manifest SHA-256
`205b1e3ad157d1967f26582ab22bfc0a3c73c2defaf812dbf16a66df33951b98`,
and deterministic receipt SHA-256
`b2b42257757950b0baf7240787b36d48ca06c353f35a860b0a3bcf2d8c9e82f5`.

The cumulative release package has 49 files / 92,476,057 bytes. It preserves
all 41 anonymously verified C2 files / 91,249,199 bytes byte-for-byte and adds
eight C3 files / 1,226,858 bytes. The 30,151-byte package receipt has SHA-256
`d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637`.
The compact source/backend archive embeds both the component licence and the
exact collection licence governing its repository-level reproduction scripts.
Package contract/write/check replay and independent ZIP, inheritance, rights,
privacy, and checksum audit pass.

Content commit `1c8f97f02e9bccfdbe4df91dd77af969cd6e33d6` is public. All 68
changed blobs / 1,676,888 bytes matched immutable raw commit URLs. Static
workflow run `33251730934` passed, and two credential-free passes matched all
181 Pages files / 22,126,534 bytes; the Pages receipt SHA-256 is
`9beb5dae3023d6549f6f5ad52ee6e472e1a001bc035d09d1cfbc4091585b1007`.

GitHub release `378973936`, tag `v2026.08.29.c140-companion-c3`, points to the
same content commit. The transactional publication and two independent direct
credential-free readbacks matched all 49 assets / 92,476,057 bytes. Publication
and direct-readback receipt SHA-256 values are respectively
`62c58f7d5de7eb07e459fcfdf7d4d2450801cda57d68912607de21353a7cf4e4`
and `84a09172a8a17be2a9aaa991db40b00fd2a4fdb88581277ad3e667b7e4e9043b`.

Zenodo record `22161363`, DOI `10.5281/zenodo.22161363`, is public in existing
concept `22077422`. Its publication and credential-free 49-file readback
receipts have SHA-256 values
`999dc33490eb77c4759857f7fb8ac3baf8919bde5780dc17b4959657dbfe98df`
and `c53bd0827a06a25dd81bee46d8c6630ce4147f256f0605f089f16aa712a69bbf`;
the final lineage audit found one submitted matching version and zero drafts.
An independent paced direct HTTPS replay also matched all 49 files, metadata
MD5 values, sizes, and SHA-256 values; its receipt is
`ZENODO_DIRECT_READBACK_2026-08-29_C140_COMPANION_C3.json`, SHA-256
`55f607cc41f6a0a8ad1355d1a46aa3d22f6b7f27a9224f986fd6f3f136f29ce2`.

The complete publication checkpoint is
`CHECKPOINT_2026-08-29_C3_PUBLICATION_COMPLETE.md`.

All minimum theory and simulation-family boundaries are closed. Seven mastery
sets `MS00`–`MS06`, three assessments `CA02`–`CA04`, and two capstones remain.

## C2 matrix-linear-model boundary — public deterministic closure

Batch C2 is complete and publicly preserved. It adds
`D008`–`D011`, `SIM005`, and `MS12` without replacing C1. The cumulative
reader now contains 23 documents / 422,089 source bytes / 640 stable anchors /
221 resolved body references. Five mastery sets and `CA01` contain 50 problems;
every problem has metadata, two or more staged hints, a short answer, and a
complete worked solution.

The C2 seeded simulation produces three substantive CSV/SVG outputs plus its
manifest: 4 files / 3,873 bytes. Its receipt SHA-256 is
`de89e57c10c178915ddd96e12d368e5e11b40baa47b6fc31c2e3df5adbd63bd2`.
Together, C1+C2 cover five simulation families and 12 substantive generated
assets. The cumulative browser-free HTML closure contains 47 files / 2,509,497
bytes; manifest SHA-256
`17d7dfd35cadf0b16b373221ba490fbd1c1d903c039327b2013a57963660b170`.
The backend contains 679 entities and 917 relations in four files / 225,463
bytes; manifest SHA-256
`3304645393ab94d9c3f0b0861876a5123b4db7ac32f797c3fdebba2635c30a9d`.

Build receipt SHA-256 is
`6417c7a8764082ce74e397ccdb79d337534d27c888d8d2cc12830d6947d7c0a1`;
QA receipt SHA-256 is
`0f118dae5488a68098aa9fef5c03a4135968eee2c74f509f67b0817e05bc38ef`.
Both write/check-only replays pass with browser and network use false. A bounded
post-authoring audit repaired hidden control-character damage in two formulas,
restored missing TeX commands, reconciled SIM005 notation and replication
counts, and independently checked the theory and all eight MS12 solutions.

Linux CI initially exposed platform-dependent low-order floating-point digits
in the SIM005 JSON receipt, while all substantive CSV/SVG results were
unchanged. The generator now quantizes receipt-only summary floats to stable
decimal identities. CI run `33224203232` passed at commit
`d330dc7ecbef71c96067f49fab372efd72317d0c`; two static readbacks matched all
171 Pages files / 21,922,300 bytes. Pages receipt SHA-256 is
`2d0b33a0b2cc25c0171002ae4291a966300b91dc25cfdd837370c2c2d258fd0a`.

The final corrected cumulative GitHub release is `378957927`, tag
`v2026.08.29.c140-companion-c2-replay-fix`, at commit
`7f464d3704c6bbe79fcbf94d5fccd567baa1865f`. Anonymous readback matched all
41 files / 91,249,199 bytes. Its verification receipt SHA-256 is
`67e2c95af03695fa4e69de9b8987d755ac24b7f8d7151b3cbf4d68367030917d`.
The final Zenodo version is record `22160621`, DOI
`10.5281/zenodo.22160621`, in concept `22077422`; anonymous readback matched
the same 41-file union and the final lineage audit found zero drafts. Zenodo
publication, readback, and audit receipt SHA-256 values are
`57e3a76045b625517d79a009835f7c5dbec4f3c936ec3f60b2ae1e46abc3b0ab`,
`0f17f4f63eb2284563f547d35349d102c12244fd1d092898df0390ef5d7c11fa`,
and `263dcb561b41af1d0fc28a52b61d66314c787f2e25ddf5719163f394e741525b`.

Batch C1 is publicly preserved as a coherent partial checkpoint. The admitted
reader contains 17 documents: index, `D001`–`D007`, `SIM001`–`SIM004`, mastery
sets `MS07`–`MS10`, and cumulative assessment `CA01`. The source is 288,436
bytes with 442 stable anchors and 173 resolved body references. The four
mastery sets contain 32 problems; CA01 contains ten problems and an explicit
100-point rubric. All 42 problems have metadata, at least two staged hints, a
short answer, and a complete worked solution.

Four seeded simulations generate nine substantive CSV/SVG outputs plus their
manifest: 10 files / 17,645 bytes. Python 3.13.9, NumPy 2.4.4, and PCG64 are
locked. All numerical assertions pass, including computed Wald/score/LR
agreement and actual bootstrap-index resampling. The simulation receipt is
5,468 bytes, SHA-256
`834c8a20025d51bf53ef4e8d0f7d805489af21c34065238131366a734df7e213`.

The deterministic offline HTML reader contains 35 files / 2,265,015 bytes.
Its manifest SHA-256 is
`4f6eaee5df63a2bf37e6f88a36794fa01c200e38a37fe85076e5008ce7b4d36d`.
The backend contains 469 entities and 648 relations in four files / 157,004
bytes; its manifest SHA-256 is
`a4ff6674dc9c35bff0baf488fbccee195a73d0a2d0ccc9739ac8faa18e05ba0c`.
Build receipt SHA-256 is
`1f9c746e723259ec46419586ac2c6f4b6ef7684deb9427e3eeb9cbc488e9ba35`;
QA receipt SHA-256 is
`c6b5977feb035d0f1425438dfd88b12cf8fc876820ddb04287fd62b6c37cfd67`.
Write and check-only replays pass.

Two independent bounded mathematical audits covered the regular/nonregular and
optimality/decision surfaces. Proved theorem-hypothesis gaps, malformed TeX,
one wrong simulation reference, and two circular simulation checks were fixed.
Both post-fix read-only audits report no remaining high-confidence defect.

The cumulative Pages tree is public at 159 files / 21,677,818 bytes
with manifest SHA-256
`e73658619391a5eab4d5fab997cce5cfb206fff942138bca92d38a5a22e1ac6f`.
It preserves the 106 Penn and 18 donor files byte-for-byte and adds the 35 C1
files. Static workflow run `33188506179` passed at content commit
`be8f189a9fbb922795492eab8cadbe81cd58d2b4`; two credential-free readbacks
matched every public file. The 57,970-byte Pages receipt has SHA-256
`a176d7fcbf272757d9130ce6d5211661bab0e1a8645efb571ed8f09a54d16ebb`.

The cumulative preservation union has 33 files / 90,175,090 bytes. It keeps all
25 prior files byte-for-byte and appends only eight C1 reader/source/rights/QA
and manifest artifacts. GitHub release `378644493`, annotated tag
`v2026.08.28.c140-companion-c1`, points to commit
`cfcfb5b172f04f6b77b98fa04fb093520cdb8881`; anonymous readback matched all
33 assets. Its publication and independent readback receipt SHA-256 values are
`09da3a9d356c06295058e6b581a245f175ec64f7514f716d95560b433190779b`
and `46fc2b4bdf39b36e26cf4c000528b74b1a59d71965d9576e7e0910487af2eb70`.

Zenodo record `22148810`, DOI `10.5281/zenodo.22148810`, version
`2026.08.28.c140-companion-c1`, is public in concept record `22077422` /
concept DOI `10.5281/zenodo.22077422`. Independent anonymous readback matched
all 33 files / 90,175,090 bytes and the final lineage audit found zero
unpublished drafts. Publication, readback, lineage-audit, and lineage-pointer
receipt SHA-256 values are
`c19afd7a4de6fcb9cc163d2f57067cb32571d64801102cb6cc9b4bbd0869fc5c`,
`3e11aa7dd86726d01ec63aa92a9c4ebdbfc860ece7841881611b2dd2197c1a38`,
`f1ecaa62696db901c49ad10d92c029136a4a84bbd68fdc89c73816ba1b67f441`,
and `c16fc96521afbee4cdcb4d63ea8d868e3760007532687414b82db2a40fa246a9`.

All original companion content is CC BY-SA 4.0. Penn and Random rights remain
separate. Provenance remains exactly `OpenAI Codex gpt-5.6-sol, Ultra`.
Permanent gate: no Chrome, Chromium, Playwright, Puppeteer, Electron, WebView,
DAISY Ace, or other browser process may be launched.

Overall C140 remains incomplete after the public C2 boundary. The matrix Gaussian linear-model
bridge is closed. Bayesian–frequentist comparison, remaining scheduled
simulations, eight mastery sets, three cumulative assessments, and two capstones
remain.
