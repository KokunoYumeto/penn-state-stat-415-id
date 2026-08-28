# Current state — Penn State STAT 415 id-ID component

Updated: 2026-08-28

## Authority and boundary

All fourteen official Penn State documents—landing/index plus Lessons 00–12—
remain frozen at exactly 1,604,869 bytes. The source-manifest SHA-256 is
`622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`;
the freeze-receipt SHA-256 is
`2a63e37bb6b4637cfd2522e392b140f2b625f2a1cf5f76f267a53ba4fb2e119b`.
Authority bytes are immutable and unchanged.

The validated cumulative reader is complete: landing/index plus Lessons 00–12,
all 14 of 14 documents and all 4,932 admitted translation segments. It has
6,510 normalized source units, 6,498 derivative units, and 3,156 protected
source-mathematics surfaces. The twelve removed derivative units remain the two
registered Lesson 00 source defects plus the complete nested closure of two
visible Lesson 08 internal authoring notes; no instructional unit was removed.
The cumulative correction/disposition ledger now contains 242 target-only
records. Authority bytes remain immutable.

## Lessons 07–09 contiguous batch

Lesson 07 freezes 105,026 authority bytes at SHA-256
`2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`.
Its 237 segments, 399 units, 148 math nodes, two PNG assets, and twelve proved
repairs are complete. The 74,079-byte target SHA-256 is
`d5714697191c3530be7183ee15a8ae3dffda87596338eadb293ac58c0d1cb440`.
The derivative explicitly corrects the source implication that consistency
alone yields expectation convergence: an additional condition such as uniform
integrability is required.

Lesson 08 freezes 135,460 authority bytes at SHA-256
`7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953`.
Its 291 segments, 604 source units / 594 derivative units, 156 math nodes, four
PNG assets, 28 visible code surfaces, and seventeen proved repairs are
complete. The 113,208-byte target SHA-256 is
`d902c11f06ed884d3124596c9c178e87dbd993063b65c454176e73c96b4d3daf`.
Code-line stable IDs are preserved even where corrected code has a different
line count. Bootstrap validity, reproducibility, Pareto endpoint inference,
expected versus observed information, and delta-method conditions are repaired
only in the derivative.

Lesson 09 freezes 114,901 authority bytes at SHA-256
`87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319`.
Its 443 segments, 414 units, 219 math nodes, ten assets, three semantic tables,
and nineteen proved repairs are complete. The 95,275-byte target SHA-256 is
`539cf8f248e654ccb70bf12c98318ece8ac9de7281ae1f1ea5bb3d364d134f64`.
All decision tables have captions, row/column semantics, and explicit header
associations; all images have complete Indonesian alternatives and responsive
reader layout.

## Lesson 10 contiguous boundary

Lesson 10 freezes 152,767 authority bytes at SHA-256
`0cb938a114d27b03ef3196c24a2e87b79a1a466b9dcbe370e6e6553947446bf5`.
Its complete target has 540 segments, 625 source units, 369 math surfaces,
22 byte-preserved assets totaling 8,313,758 bytes, nine code surfaces, two
semantic tables, and 28 proved target-only corrections. The target is 153,768
bytes with SHA-256
`8fb91a9fc5ef0b5a163767aec5e760d19c3e56f6c3dee35ee58323d6c45359c5`.
The cumulative build has 94 files / 17,020,141 bytes; its manifest is 10,100
bytes with SHA-256
`08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663`.
The build receipt is 24,978 bytes, SHA-256
`0f440e56bf71e172815ac0933e752e3f3f12383573e4c501db8fe5aa1922a520`; the
deterministic QA receipt is 6,118 bytes, SHA-256
`6bc589012a12e93d9418fe9f26029ca8b58b6de61235a4d6181114afa2300180`.
Both write and check-only replays pass. The cumulative correction backend now
has the ordered IDs `O006-PSU-ADV-0001` through `O006-PSU-ADV-0198`; the
Lesson 10 suffix is 300,910 bytes, SHA-256
`2450673f606d7a308dd7490cd811f81dcd3c42cc382b1eefe2b21d3dbb2f2032`.
At the historical Lesson 10 boundary, the cumulative reader had 2,540
protected math nodes, 56 substantive images, seven semantic tables, zero
external runtime requests, and no sensitive/local path findings. The Lesson 10
target title, captions, alts, duplicate-ID repairs, table associations, runtime
disclosure, and responsive reflow passed its deterministic QA gate.
Translation provenance remains exactly `OpenAI Codex gpt-5.6-sol, Ultra`.

## Lesson 11 published boundary

Lesson 11 freezes 99,359 authority bytes at SHA-256
`4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32`.
Its normalization has 354 translation segments, 264 stable structural units,
264 protected mathematics surfaces, seven examples, one semantic table, four
code nodes, and one same-origin portrait. The normalization receipt is 8,194
bytes, SHA-256
`448773792cfad18d52fb883d3dba4a298d5271948fdbedd2d9e01d7d2a70cdd4`.

The portrait `bayes.png` is frozen byte-for-byte at 142,195 bytes, SHA-256
`2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22`.
The asset manifest is 434 bytes, SHA-256
`a10a6bc2c5ba7738916eeb2ac1cb12d2ed52a77d505e9843190ffa39a726379b`;
the asset-freeze receipt is 1,062 bytes, SHA-256
`2d128b3d4b4635aa45855b8d5ba82cbec408f139a1ac51bcddcbd7682221f3e2`.
It remains under the official page notice, is copied without binary
modification, and receives an Indonesian alternative description, caption,
rights notice, and responsive full-width centered layout in the derivative.

All 354 translation segments are complete. The canonical merged translation
is 86,242 bytes, SHA-256
`1b54aa89f765f3befbd9464d4382aa68551f7278947a06d01621fd26b632c20c`;
its 354-record binding backend is 165,244 bytes, SHA-256
`dbf90c6a2ed2bc7b31c0df808b28351a08ef61e14ddd73fc048562e1e350ed8f`.
The translation receipt is 3,264 bytes, SHA-256
`fc920cee18729d0e775e7e8cad922163af9a4d50f2ef4826a4c79395a615a374`.
The final Lesson 11 target is 69,861 bytes, SHA-256
`70a954496254cf26abd8d28317d45ac1bc945ed2551dd4a6b0eb902ae78e8002`.

Twenty proved target-only repairs are registered contiguously as
`O006-PSU-ADV-0199` through `O006-PSU-ADV-0218`. Five protected mathematics
surfaces change under explicit records: `O006-PSU-012-M0057`, `M0118`,
`M0134`, `M0253`, and `M0263`. The cumulative 218-record correction backend
is 313,335 bytes, SHA-256
`699377a938dcd9a2336d3d69b2d4258b3358db3f8f3beabb24f666c396c1b53a`;
the durable adverse-ledger prefix through Lesson 11 is 315,281 bytes, SHA-256
`376515c286f48ee5f648097cfa093b2b305e7dec9c67e6ca986300815fc2c17d`.
All repairs are target-only; authority bytes remain unchanged.

## Lesson 12 translation layer

Lesson 12 freezes 144,220 authority bytes at SHA-256
`89569622b8fea9bcfc17d51717002ab9840b44e6d80a34ee476d94acd45b515d`.
Its normalized source has 580 translation segments, 846 structural units, 352
protected mathematics surfaces, nine frozen image assets totaling 233,075
bytes, and three external-video provenance records. The normalization receipt
is 9,727 bytes, SHA-256
`ef7b86ff5d6e46237688051fe1ffd867d2a2006d2c8393370b697abe2fae8156`.

All 580 segments are translated in three canonical contiguous batches. The
merged translation CSV is 140,789 bytes, SHA-256
`a87a42c2aebb2ae38910c75ae354d07b862f6113cb063474bfbb7c8a1ac00531`;
the 580-record binding backend is 279,013 bytes, SHA-256
`f6c64c31aa0514f4b386efa182cfcac128076b3e58f2ddf0bee75d51f229730c`.
The translation receipt is 3,748 bytes, SHA-256
`5514555698cd07737d12e3b91e440af9f9302dc32de5df49716c8b532f248364`.
`source/id-ID/Lesson12.html` is the admitted 146,789-byte generated target at
SHA-256
`6cd3218f6d1a613f1ea9d1459c5506ea8b24f37340a3ee26f17bc18504dd5965`;
its materialization, cumulative build, deterministic QA, and visual QA all
pass. Twenty-four Lesson 12 correction/disposition records extend the ordered
suffix through `O006-PSU-ADV-0242`. Nine images are frozen byte-for-byte and
used in ten occurrences; the three external video runtimes are not
redistributed and instead have complete, expanded offline textual equivalents.

## Deterministic and browser evidence

The complete cumulative offline reader contains 106 files / 17,614,553 bytes.
Its 11,573-byte manifest has SHA-256
`697c9ee8e23cc10469fea4d1894e16471ffb4276edd1f0d25bebfb5be0dbe79e`.
The 17,276-byte build receipt has SHA-256
`b08693e28595bf51814c3cbd6654223f024cb22512b07e849a557e73a27dd328`;
the 12,428-byte deterministic QA receipt has SHA-256
`d12c9dcb4293de0ec929cc2d2c330e197d936a86e17e27adc20dede10bef15db`.
Asset freeze, normalization, merge, materialization, cumulative build, and QA
write/check-only replays pass. The gate covers all 14 documents, 4,932
segments, 6,510/6,498 source/target units, 3,156 protected math surfaces, 242
corrections, stable IDs, links, rights, privacy, and byte-deterministic replay.
The exact 32-command repository CI chain was freshly replayed on 2026-08-26;
all commands passed and reproduced the recorded build and QA receipt hashes.

Fresh browser inspection passes all fifteen routes—index, Lessons 00–12, and
licenses—at 1,280 × 720 and 390 × 844. All 86 referenced same-origin resources
return HTTP 200. All 3,156 protected source-math containers render; Lesson 12
also renders twenty registered target-native/additive containers, giving 372
MathJax containers on that route. There are zero `merror` nodes, console
warnings/errors, page or navigation overflows, broken images, or external
iframes. All 67 substantive image occurrences load; all ten Lesson 12 images
are centered and fill their figure containers. The cumulative reader has 14
tables, twelve captioned and two historical source tables without captions;
all six Lesson 12 tables are captioned and fully scoped. Its three offline
video equivalents are expanded, readable, and unclipped. The 21,702-byte
visual receipt has SHA-256
`02583cecceba1db5f8a9f7561f567ebd98585c441a6e4cae5ba1ef92f8710d6e`;
its write and check-only modes both pass.

The 242-row correction backend has exact ordered IDs
`O006-PSU-ADV-0001` through `O006-PSU-ADV-0242`; SHA-256 is
`2b709bfe05dce6aa84c67513f1679faac0d1c38da987509a558b1dbba1cb0837`.
The complete fourteen-row translation ledger is 5,821 bytes, SHA-256
`c5ba07e250360af2a97957aa957278f43348c05bb44a208a2a2898fc6b034660`.
The 192-row terminology glossary is 20,340 bytes, SHA-256
`554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05`.

Rights remain component-separated: Penn State content is CC BY-NC 4.0 except
where otherwise noted, MathJax 3.1.2 is Apache-2.0, and original repository
support remains CC BY-SA 4.0. Translation provenance remains exactly
`OpenAI Codex gpt-5.6-sol, Ultra`; all source and human-contributor credits are
preserved. No upstream message has been sent.

The one cross-platform defect discovered by the first 14-of-14 GitHub run is
closed locally: `working/lesson12_source_findings.md` is canonically LF at
8,203 bytes and SHA-256
`8b087fb8e545f14ba323afd1caa5672117d60878c3c5924a0b0455136078109c`.
The previous 8,209-byte identity represented CRLF bytes. The two binding
scripts and all downstream receipts now bind the canonical LF identity; the
complete workflow replay passes and the reader manifest remains unchanged.

## Publication state and next work

The complete 14-of-14 boundary is public and anonymously verified. GitHub
content commit `13767f55f739ad7dd058fc1dcb55cf5334ab097c`, tree
`dbf8abf4f729ddca46f69547bcf38d0b71f27f07`, successful Pages run
`32930770236`, tag `v2026.08.26.14of14`, and the corresponding release are
public. Anonymous readback matched all 746 commit-tree blobs / 154,064,493
bytes, all 106 Pages files / 17,614,553 bytes, and all nine release assets /
55,312,500 bytes. The GitHub checkpoint and release receipt SHA-256 values are
respectively
`de0a44ae013f72198b32948a3c5b7f245cdefd2cdeffd902dba615cfb770f752`
and `e3b620272dff1b40f5d2ae8d3707e5e8a57940771f93c22ccd87c7a153052e17`.

Corrected Zenodo record `22105616`, DOI `10.5281/zenodo.22105616`, version
`2026.08.26.14of14-r1`, is submitted in concept record `22077422` / concept
DOI `10.5281/zenodo.22077422`. Anonymous readback matched all nine
reader-first files / 55,312,500 bytes. The final concept audit found one
submitted matching version and zero unsubmitted matching drafts. The
publication, anonymous readback, final lineage-audit, and lineage-pointer
SHA-256 values are respectively
`11a047fc561e1e27f31b3bc800d9de1cf5e78b2e63001ec18563efb7c5ad5cf1`,
`a386fa3539d0366d8890669ddfeaff1853fab10f90c2f24533c0242887897c41`,
`e476b7bb1b447478db30cb6954b6c6cda179cc255923d0bffb7a08eab39f3f92`,
and `80689f675838b69be6636680eb0fef1c3ff8b01fb07386b752c3b4a4620cfe90`.
This version binds the canonical 8,203-byte LF findings file; no duplicate
concept or pending matching draft exists.

The consolidated deterministic PDF and EPUB described below are now publicly
preserved and anonymously verified. The next production boundary is the
distinct exact Random completeness donor, followed by the original C140
rigor/simulation/mastery companion. No upstream message has been sent. The
independent completed Random edition remains outside this repository's write
boundary.

## Consolidated PDF and EPUB release-ready boundary

The consolidated fourteen-document PDF is complete at 219 A4 pages and
20,170,549 bytes, SHA-256
`f39c1c438cc3e793fe9522eb11f5b02704d89fcdc7aecb2207a599087d458964`.
Its canonical replay is byte-identical. The structural QA receipt is 10,208
bytes, SHA-256
`3512a6b05daa115967aa96bdaacba0b7820b7d02b8f9523d2ef8ba27155fed1c`;
the all-page visual receipt is 64,720 bytes, SHA-256
`bf27e907326128653d09bb7417b307c5e226cfac82b7781cdf71f7f1b4f38898`.
The latter binds 219 final page rasters and eleven contact sheets covering the
entire reader; only pages 217-218 changed in the last layout repair.

The final EPUB and its two independent replays are byte-identical at
12,301,415 bytes, SHA-256
`e122d65348971b91a5ac0c7a8219e0fa3e0eabedb92d130c661648e399e3c574`.
EPUBCheck 5.3.0 reports zero messages. The package contains 111 deterministic
entries, 107 manifest items, four spine items, 3,159 MathML nodes, 17
Indonesian-labelled SVG math fallbacks, 102 nonempty image alternatives, and
nineteen navigation entries. CSS containment covers every MathML wrapper;
exactly 125 stable-ID width-risk candidates receive keyboard-focus semantics.
The build, final QA, and static-reflow receipt SHA-256 values are respectively
`bd0db2d244d854a025caf904d1b1b773a37fe4b17513985c3543963dfa453d00`,
`5068b217da737f1a24118360828725c7afc724de1648771c2698c6467ea70537`,
and `27f46841986869f97f73980fc870205627c9ff9ff4c36d9751140000d7457eeb`.
The final EPUB gate used only browser-free static/package tooling. The earlier
Ace 1.4.6 pass remains explicitly scoped to prior artifact
`acf81b8aa62ef77cd574d45d04490ebe173539ea3f8419c5c5e1ffcea5536729`;
it is not represented as final-hash validation.

The deterministic preservation union contains 17 ordered files / 87,848,426
bytes. It preserves all nine files from Zenodo record `22105616` byte-for-byte
and adds the PDF, EPUB, concise rights/status notes, compact labelled QA
evidence, full manifest, checksums, and cryptographic root. Package-receipt
SHA-256 is
`934f9484dd7fd25a2436c80914c68d9627ba4009da07900a975e168d91d01694`.
## Consolidated PDF and EPUB published boundary

GitHub tag/release `v2026.08.28.14of14-pdf-epub` is public at artifact commit
`7d1012119d8bd6b8942347e44ffbbca0b8bcba07`. Anonymous readback matched all
17 assets / 87,848,426 bytes. Release ID is `378391763`; the publication and
independent verification receipt SHA-256 values are respectively
`1f9507df0188a646f0e5b675f3f8bd53e6151d90dfc18e873b49294841eba605`
and
`acdf91afdebb7ab4f0143f93f3c5426dd361ebeb637cf7b73f7689a58a005ef2`.

Zenodo record `22142292`, DOI `10.5281/zenodo.22142292`, version
`2026.08.28.14of14-pdf-epub`, is public in the existing concept record
`22077422` / concept DOI `10.5281/zenodo.22077422`. Two independent anonymous
readbacks matched all 17 files / 87,848,426 bytes. The final authenticated
lineage audit found zero unsubmitted concept drafts. The publication,
anonymous-readback, final-lineage-audit, and lineage-pointer SHA-256 values are
respectively
`07b64d6942ae71cd0cdf4dff58fbbaf56851274beb67b4b98e781f430342867b`,
`af79452568bbde49effe37904e92d5c3acf380ff3dcde9f528753624cc1fe397`,
`f4b65e0ff7706212c4f5ee189b97aabac2d874b1bf73500b70a54780cfb53bf1`,
and
`f56ef5c4adc990bb08a394830df85a653c254ec106d2a67b60478e9137b7b8fc`.
The public PDF and EPUB identities remain exactly those recorded above.

## Exact Random completeness donor — complete public Pages boundary

The selected one-page donor is now a separate component at
`components/random-completeness/`; the independent 29-page Random repository
was read but not modified. The official page remains 57,507 bytes at SHA-256
`4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4`.
The canonical id-ID target is imported byte-for-byte at 60,895 bytes / SHA-256
`255ac88f235727301ee341eef79b9578910be88b7e2e038d4dfecc0ed686513c`
from public sibling commit
`f2aab7b9a0578dd76624e183fc47e3c1faa664e8`; credential-free public readback
matched both source and target identities.

Live static HTTP revalidation matched the donor, landing and Credits rights
witnesses, all six direct source assets, and the official MathJax 3.1.2
`boldsymbol.js` dependency. The landing witness remains CC BY 2.0 while
Credits links CC BY 1.0; both are frozen and disclosed. The 5,720-byte import
receipt has SHA-256
`f8965757775c4aa0f294aac1a7fe7bd04dece9b82f755bd63d1f39abdd52c214`.

The canonical source/target preserve 436/444 elements, 804 delimited TeX
spans, 39 instructional units, 26 derivation disclosures, and 51 canonical
target IDs. The donor backend contains 325 exact stable entities, 474 outgoing
relations, one complete translation-ledger row, and nineteen relevant adverse
records. The derived standalone reader contains 18 files / 1,798,250 bytes.
Its build and static-QA receipt SHA-256 values are respectively
`455afd0c425260517857bc61e108d08b2abf0548dcb880095b3a2d95bdc3ac2d`
and
`5868ed14ecc03094f6fea848d927738f0fe459443c5a5c49afe2a2abbe93c83f`.
All local HTML/CSS/runtime dependencies close, all external links are HTTPS,
all fragments resolve, privacy scans are clear, and check-only replay passes.

The deterministic Pages collection preserves all 106 Penn reader files /
17,614,553 bytes byte-for-byte and mounts the 18 donor files without a
collision. The resulting 124-file / 19,412,803-byte tree has manifest SHA-256
`c7e31332d0401ad149185af3fc2ab2b39baf54a2b37f84dbc0f2720edd8241fa`;
the Pages collection receipt SHA-256 is
`17b60a65cfb181d170f3302fb5f527608e026fcdbcab39839bcc3aad119f329a`.
No browser process was used.

The donor boundary is committed at
`5ed0e501e3a41c1274d90c9f02aee15bc210324a`; GitHub Pages workflow run
`33164278836` completed successfully. Two independent credential-free static
HTTPS passes matched all 124 public files / 19,412,803 bytes: all 106 Penn
reader files / 17,614,553 bytes remain byte-identical, and all 18 donor files /
1,798,250 bytes match. The 49,911-byte sanitized anonymous-readback receipt
has SHA-256
`0ffe07f76adf6187b3c8c006fc61f2da507dd59dda6580c433fafc3a1af7c32a`.
Its verifier disables ambient environment credentials, binds the immutable
content commit and workflow run, pins and recomputes the local collection
manifest, rejects unsafe or colliding paths, and verifies each final HTTPS
path as well as bytes and SHA-256.

The next executable action is to publish a cumulative donor checkpoint in the
existing GitHub and Zenodo lineages while preserving the current seventeen
Penn reader artifacts byte-for-byte, then begin the original C140
rigor/simulation/mastery companion. No upstream message has been sent.
