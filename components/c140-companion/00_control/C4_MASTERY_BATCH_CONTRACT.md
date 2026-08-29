# C4 contract — independent-study mastery closure

Status: complete and release-ready, 2026-08-29

C4 extends the publicly preserved C3 companion without changing any C1, C2, or
C3 source, generated asset, or receipt. It adds exactly seven original
Indonesian mastery documents:

`MS00` diagnostic probability/distribution/expectation review,
`MS01` order statistics, `MS02` estimation and bias/MSE, `MS03` sufficiency and
factorization, `MS04` method of moments and likelihood foundations, `MS05`
Fisher information/confidence/bootstrap/delta, and `MS06` exact testing,
power, p-values, and the Wald/score/LR bridge.

Each document is CC BY-SA 4.0, locale `id-ID`, and carries provenance
`OpenAI Codex gpt-5.6-sol, Ultra`. Each has eight contiguous nontrivial
problems (`P01`–`P08`); every problem has a stable anchor, one-line
`PROBLEM_META`, at least two staged hints, a short answer, and a complete
worked solution. Software output never substitutes for a derivation. Existing
Penn State content is referenced by stable document identity and is not copied
or relabelled as original prose.

The cumulative C4 static build uses the same offline HTML renderer, MathJax
closure, backend schema, simulation assets, and no-browser/no-network QA gates
as C3. The C4 build and QA receipts are separate from historical C3 receipts;
the C3 package remains an immutable public witness. New mastery IDs are added
to the backend in source order, and all internal references must resolve before
publication.

## Gate and next boundary

After all seven files pass structural and mathematical review, run:

```text
python -B components/c140-companion/scripts/build_companion.py --write --c4
python -B components/c140-companion/scripts/build_companion.py --check-only --c4
python -B components/c140-companion/scripts/qa_companion.py --write --c4
python -B components/c140-companion/scripts/qa_companion.py --check-only --c4
```

Record source, HTML, backend, and receipt hashes in the C4 local checkpoint.
Only then package and publish a reader-first cumulative C4 release in the
existing GitHub/Zenodo lineage. The C4 release must state that assessments
`CA02`–`CA04` and both capstones remain unfinished. No upstream contact occurs
during this batch.
