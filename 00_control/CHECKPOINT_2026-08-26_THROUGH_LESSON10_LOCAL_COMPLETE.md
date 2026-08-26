# Local production checkpoint — cumulative edition through Lesson 10

Date: 2026-08-26
Status: deterministic build and QA complete; 12-of-14 public release next

## Frozen authority and translation

- Official boundary: landing/index plus Lessons 00–12, fourteen documents,
  1,604,869 frozen authority bytes; source manifest SHA-256
  `622c9ed2d82bb0f3f60f6855b341664233dd548b5d53dfaee2a488218a5da515`.
- Lesson 10 authority: 152,767 bytes, SHA-256
  `0cb938a114d27b03ef3196c24a2e87b79a1a466b9dcbe370e6e6553947446bf5`.
- Lesson 10 target: 540 segments / 625 source units / 369 math surfaces / 22
  assets / 9 code surfaces / 2 tables / 28 target-only corrections; target
  153,768 bytes, SHA-256
  `8fb91a9fc5ef0b5a163767aec5e760d19c3e56f6c3dee35ee58323d6c45359c5`.
- Four canonical translation batches cover S0001–S0540. Merged translation
  CSV: 149,472 bytes, SHA-256
  `27305c36d540f63db6dbf925de6caa93dc544fbc0268a863979ac410edad0b51`.
- Translation provenance: `OpenAI Codex gpt-5.6-sol, Ultra`.

## Build and QA

- Cumulative coverage: 12 of 14 documents; 3,998 segments; 5,400 normalized
  units; 5,388 derivative units; 2,540 math nodes; 198 corrections.
- Offline reader: 94 files / 17,020,141 bytes.
- Manifest: 10,100 bytes, SHA-256
  `08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663`.
- Build receipt: 24,978 bytes, SHA-256
  `b31ed728f1b66dc257000aac334fdb5a0240a646777295db1c99396a6884538d`.
- QA receipt: 6,118 bytes, SHA-256
  `c6a1fcf4a2318e2e783f806214dc824fd73da104f19c81fe6965263b1ec7066e`.
- Write and check-only replays pass. QA covers source/target bindings,
  topology/math, correction registry, 22 byte-preserved assets and rights,
  19 duplicate native IDs, 22 linked alts/captions, two semantic tables,
  five R blocks/three output snapshots, runtime disclosure, clean title,
  responsive reflow, privacy, and deterministic 94-file replay.
- Cumulative correction backend: 300,910 bytes, SHA-256
  `2450673f606d7a308dd7490cd811f81dcd3c42cc382b1eefe2b21d3dbb2f2032`.

## Release boundary and next cursor

The next authorized operation is one reader-first 12-of-14 release in the
existing GitHub repository and Zenodo concept, followed by anonymous byte and
live-reader verification. No upstream contact has occurred. After that push,
continue with Lesson 11, then Lesson 12, in source order. The independent
Random edition remains a separate component and is not copied here.
