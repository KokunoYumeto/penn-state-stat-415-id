# C5 local completion — 2026-08-31

Translation and original reader production finished before final audit. The
complete companion now contains 39 id-ID source documents / 1,145,637 bytes:
index, D001–D013, SIM001–SIM006, MS00–MS12, CA01–CA04, and CP01–CP02.
There are 1,349 unique anchors, 379 resolved body references, 146 problems,
292 staged hints, 146 short answers, 146 full solutions, and 62 rubric anchors.

## Final corrections and scope

Post-production checks closed theorem-hypothesis and endpoint exceptions,
mastery TeX defects, CP01 aggregate-symbol consistency, Indonesian SVG labels
for SIM001–SIM005, and heading hierarchy in SIM005/SIM006. The final reread
also made the zero-count Poisson LR convention explicit in MS10 and repaired
a missing TeX backslash in MS12. No source authority bytes were changed.
The exact final 39-file identities are in `build/C5_BUILD_RECEIPT.json`.
The five C5 additions also have their current identities in
`00_control/C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md`.

## Deterministic build and QA

Interpreter: Python 3.13.9; NumPy 2.4.4; SciPy 1.17.1. The process uses
`PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`,
`MKL_NUM_THREADS=1`, `NUMEXPR_NUM_THREADS=1`, `TZ=UTC`, and `LC_NUMERIC=C`.

The following were run in order; every invocation exited successfully:

1. `scripts/build_companion.py --write --c5` and two separate `--check-only --c5` runs.
2. `scripts/qa_companion.py --write --c5` and two separate `--check-only --c5` runs.
3. Repository `scripts/assemble_pages_collection.py --write`, then `--check-only`.

Build receipt SHA-256:
`cc9e6002edcbb5adbe5a348233fb73f5588728a4fbc330a93061c1f18807f372`.
QA receipt SHA-256:
`aef36e757fca2d3ad1593087af12a5102120697f16715acf210248d94d296bfd`.

Final public-checkout repair: the builder validates the pinned redacted CP02
witness and sanitized receipt whether or not the excluded original exists;
when present it also replays the exact original-byte redaction. Seven focused
tests passed. Builder identity is 88,390 bytes / SHA-256
`aa8525e715f2cfd69d868d3713295c62344e24847e90d552424390449f1059a2`.
Build, QA, and Pages write/check were repeated after that code-only repair;
all reader/backend/Pages bytes and the build receipt remain unchanged.
The preceding pre-repair QA receipt was
`8f3b50afd84895f3ffb83e2e0f51a8b214b951227c4c9e6aa597e26270a0b14e`.

The reader contains 135 files / 15,757,728 bytes; manifest SHA-256:
`cf5f75feececdf98bb02e9cbd8bb8144b457f3434622f9038af26ae7c89c2f46`.
The backend contains 117 files / 13,568,809 bytes, 1,523 entities and 1,949
relations; manifest SHA-256:
`67defeb90b216f3306c9a49dcbe08bf8da51206cd8d9a9f53a0339374b001bf3`.

The cumulative Penn/donor/companion Pages collection contains 259 files /
35,170,536 bytes; manifest SHA-256:
`43fad46f62f6925e39f5c24a7d0182a26b2e96e884f5e2b0d7f79be28cf64249`;
receipt SHA-256:
`77a30f8239b6181f1641b794c62a21c04eebba0a3f17d3d7248214704f77b0b6`.

## Rights and reproduction

Original companion material remains CC BY-SA 4.0; CP01 data CC BY 4.0;
CP02 data CC0-1.0. Penn and Random retain their separate component rights.
Provenance remains `OpenAI Codex gpt-5.6-sol, Ultra`. The credential-bearing
public DOI witness is excluded in favor of its recorded redacted derivative.
The 135,581,717-byte canonical CP02 coverage CSV stays local; its deterministic
5,761,556-byte gzip is included publicly with both identities bound.

All final build and QA operations are static and browser-free. No Chrome,
Chromium, Playwright, Puppeteer, Electron, WebView or other browser may launch.
No upstream communication was sent.

## Remaining executable work

The final preservation package passes write and two independent check-only
replays: 65 files / 134,904,267 bytes. All 57 C4 assets remain byte-identical.
Package receipt: 64,307 bytes / SHA-256
`4fe5a6686d6c78e8320edc00d274089a9f3419ac175b8647706763ca77d49a02`.
The source ZIP is 24,928,931 bytes / SHA-256
`4de938596957e2116d6292f4a5e493a98212e7f9d1c49de32ae6e57c5b746deb`.
Its pinned 13-file repository context includes the Penn document registry,
current donor identity/credits, MathJax runtime, and collection rights. The
documented fresh-repository layout is required; a flattened component alone
does not have the external authority needed for its cross-course links.
The clean-source reconstruction replay passed: hydration, build write/check,
and static QA reproduce the exact frozen identities. Repository receipt:
`00_control/C5_CLEAN_SOURCE_RECONSTRUCTION_2026-08-31.json`.

The CP02 hydration helper and pinned-public redaction fallback are complete
and tested. The 65-file cumulative union is now public on GitHub release
`v2026.08.31.c140-companion-c5` and Zenodo record `22208527`, DOI
`10.5281/zenodo.22208527`, in concept `22077422`. Every asset at both
destinations passed anonymous byte/SHA-256 readback; all 57 C4 files remain
unchanged. The tagged source commit is
`40acd8e846a4603ac5a90d311794b7e9c9db7bb9`.

The remaining operation is the separate online Pages deployment/readback and
final control closure. CI-only helper changes do not alter any frozen source,
reader, data, release artifact or package identity. Exact current executable
state is in repository `00_control/CURRENT_CURSOR.md`; the publication and
readback receipts are the C5-named JSON records in that same directory.
