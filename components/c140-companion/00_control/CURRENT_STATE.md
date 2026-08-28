# Current state — original C140 companion

Updated: 2026-08-28

Batch C1 is locally complete and awaiting cumulative publication. The admitted
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

The cumulative Pages tree is assembled locally at 159 files / 21,677,818 bytes
with manifest SHA-256
`e73658619391a5eab4d5fab997cce5cfb206fff942138bca92d38a5a22e1ac6f`.
It preserves the 106 Penn and 18 donor files byte-for-byte and adds the 35 C1
files. Publication has not yet occurred, so no public C1 claim is made.

All original companion content is CC BY-SA 4.0. Penn and Random rights remain
separate. Provenance remains exactly `OpenAI Codex gpt-5.6-sol, Ultra`.
Permanent gate: no Chrome, Chromium, Playwright, Puppeteer, Electron, WebView,
DAISY Ace, or other browser process may be launched.

Overall C140 remains incomplete after C1. Matrix Gaussian linear models,
Bayesian–frequentist comparison, remaining simulations, nine mastery sets,
three cumulative assessments, and two capstones remain.
