# C2 contract — matrix Gaussian linear models

Status: in production, 2026-08-28

C2 is one contiguous reader-first batch. It consists of theory documents
`O006-C140-CMP-D008` through `D011`, seeded laboratory `SIM005`, and mastery set
`MS12`. It supplements the complete Penn Lesson 12 reader without copying its
prose and uses B40 linear algebra rather than reteaching it. Bayesian comparison
and `MS11` belong to the next batch.

The admitted theory boundary is:

1. `D008`: fixed-design matrix formulation, column spaces, orthogonal
   projections, normal equations, rank deficiency, and estimability;
2. `D009`: OLS and Gaussian MLE, covariance geometry, and Gauss–Markov with
   exact hypotheses and proof;
3. `D010`: exact Gaussian sampling laws, variance estimation, Cochran-type
   projection independence, general linear hypotheses, t/F inference, ANOVA,
   confidence, and prediction;
4. `D011`: residual covariance, leverage, deletion diagnostics, Cook distance,
   omitted-variable bias, heteroskedastic sandwich covariance, misspecification,
   and post-selection limitations;
5. `SIM005`: deterministic experiments for exact sampling, coverage,
   heteroskedastic failure, leverage/influence, and multiple regression;
6. `MS12`: at least eight nontrivial problems satisfying the complete problem,
   hint, answer, solution, and metadata contract.

Every theorem must expose rank, moment, covariance, and normality assumptions
at the point where they are used. Distribution-free Gauss–Markov claims must
not import Gaussian assumptions; exact t/F claims must not be presented under
mere finite variance. Rank-deficient models must distinguish fitted-value and
estimable-functional uniqueness from coefficient nonuniqueness. Diagnostics
must not be presented as automatic deletion rules or as proof of causality.

All content is original CC BY-SA 4.0 with provenance exactly
`OpenAI Codex gpt-5.6-sol, Ultra`. Stable IDs, cross-references, formulas,
reader HTML, backend entities/relations, seeded CSV/SVG outputs, and static QA
must remain deterministic and browser-free. C2 is complete only when all six
items above build together and pass write/check-only replay; C140 remains active
afterward for Bayesian comparison and remaining mastery, assessments, and
capstones.
