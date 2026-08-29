# C2 matrix Gaussian linear models — publication complete

Date: 2026-08-29

The cumulative C2 companion is publicly preserved after deterministic local
QA, Linux CI replay, static Pages deployment, and independent public-byte
readback. The pedagogical boundary is `D001`–`D011`, `SIM001`–`SIM005`,
`MS07`–`MS10`, `MS12`, and `CA01`: 23 documents, five seeded simulation
families, and 50 fully solved problems.

## Final deterministic evidence

- C2 simulation receipt SHA-256:
  `de89e57c10c178915ddd96e12d368e5e11b40baa47b6fc31c2e3df5adbd63bd2`;
- cumulative build receipt SHA-256:
  `6417c7a8764082ce74e397ccdb79d337534d27c888d8d2cc12830d6947d7c0a1`;
- cumulative QA receipt SHA-256:
  `0f118dae5488a68098aa9fef5c03a4135968eee2c74f509f67b0817e05bc38ef`;
- successful Pages run `33224203232`, commit
  `d330dc7ecbef71c96067f49fab372efd72317d0c`;
- Pages: 171 files / 21,922,300 bytes, two complete readbacks, receipt SHA-256
  `2d0b33a0b2cc25c0171002ae4291a966300b91dc25cfdd837370c2c2d258fd0a`.

Linux CI detected and closed one cross-platform receipt-only issue: low-order
BLAS-dependent floating-point digits in the SIM005 JSON summary. The CSV/SVG,
reader prose, formulas, exercises, and solutions did not change. The final
generator serializes stable summary identities and passes locally and on Linux.

## Public preservation

- GitHub release `378957927`, tag
  `v2026.08.29.c140-companion-c2-replay-fix`, commit
  `7f464d3704c6bbe79fcbf94d5fccd567baa1865f`;
- GitHub: 41 files / 91,249,199 bytes, anonymous receipt SHA-256
  `67e2c95af03695fa4e69de9b8987d755ac24b7f8d7151b3cbf4d68367030917d`;
- Zenodo record `22160621`, DOI `10.5281/zenodo.22160621`, existing concept
  `22077422` / concept DOI `10.5281/zenodo.22077422`;
- Zenodo: the same 41 files / 91,249,199 bytes matched anonymously; lineage
  audit found zero drafts. Readback and audit receipt SHA-256 values are
  `0f17f4f63eb2284563f547d35349d102c12244fd1d092898df0390ef5d7c11fa`
  and `263dcb561b41af1d0fc28a52b61d66314c787f2e25ddf5719163f394e741525b`.

All rights remain component-separated. The original companion remains CC
BY-SA 4.0 with provenance `OpenAI Codex gpt-5.6-sol, Ultra`. No browser process
or upstream message was used.

## Next action

Produce C3 (`D012`–`D013`, `SIM006`, `MS11`) under the Bayesian–frequentist
comparison contract. C140 remains active for C3, the remaining mastery and
assessment sets, and two capstones.
