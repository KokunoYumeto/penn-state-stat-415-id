# Local checkpoint through Lesson 05

Date: 2026-08-25

The landing page and Lessons 00–05 are completely translated locally: seven of
fourteen documents, 2,311 segments, 3,209 normalized source units, 3,207 target
units, 1,546 protected math nodes, and 112 target-only corrections. Lesson 05
contributes 340 segments, 1,475 units, 108 math nodes, 267 code nodes, fourteen
reader images, and 31 proved source corrections.

Deterministic evidence:

- Lesson 05 normalization-receipt SHA-256:
  `d00f4238f3fe3b5104c0169a89c00aa940c25bff26ec311354b0651c443d03be`;
- Lesson 05 translation CSV SHA-256:
  `9f9247ff3d7c66e164bc6691fee67da51fcdf88cd951a9582ff32dae3015e3ac`;
- Lesson 05 translation-receipt SHA-256:
  `56ce80c909c360a90e9cbf7b410480cf74e875093e5ada5d12333372c48d6506`;
- Lesson 05 bindings SHA-256:
  `85821982f209874b0270d24fb9a3ac863139ab6d090e4c9ab34c88d262212f58`;
- cumulative build-receipt SHA-256:
  `afe2b51786792ecfc88e556c9a5dd26e1ff45524f45799a64f1f694c77e322a0`;
- cumulative QA-receipt SHA-256:
  `462b7c15f3d506d5028ba2c2c4737dc2bba701bdb91acb0b967620f23c3b3f68`;
- 50-file reader manifest SHA-256:
  `fb600bfedb1792d8b1c9ba8d72d3e5ef6bf94e7a9744a387e15b1d5a7b5f8e6f`;
- visual-QA receipt SHA-256:
  `c595832f3a2efd8b83b3b0fb03051cf271e717a871023cceef0ef83d30a35245`;
- package-receipt SHA-256:
  `7791ab35cc61a0f3851930e836495273202c77d819c51e83dcce2e0d56f81095`.

Write and check-only normalization, translation merge, build, and QA replays
pass. Desktop and mobile visual QA cover all eight routes with exact math-node
counts, no broken images, no document/navigation overflow, and no console
errors or warnings. The cumulative reader is 50 files / 3,588,430 bytes.

The release package is ready and contains nine files / 15,405,459 bytes. Its
primary offline reader is
`00_stat415-id-through-lesson05-offline-reader.zip`, 3,603,326 bytes, SHA-256
`89a4e458ee9aa30d2293cb95b9f0be3ecef947241ddd6dfca473ac568c6ceecf`.
Its resumable source/backend package is
`10_stat415-id-through-lesson05-source-backend.zip`, 11,782,185 bytes, SHA-256
`6235fa7cc11596cd71f40b26f60b7b00851ca03d7cab2b86f56a0b2bfd66e371`.

The last public release remains 5 of 14 at commit
`5727d8fc056d9535ac5d75a4305166f7c027b13f`, tag
`v2026.08.25.5of14`, and Zenodo version DOI `10.5281/zenodo.22088315`. This
checkpoint records local completion only; it does not claim the 7-of-14 bytes
are public before anonymous readback succeeds.

The next executable action is to publish and verify this 7-of-14 package, then
continue in source order with Lesson 06 without reopening completed Lessons
00–05.
