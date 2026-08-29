# C3 contract — Bayesian–frequentist comparison and calibration

Status: in production, 2026-08-29

C3 is the next contiguous reader-first batch after the public C2 matrix-model
boundary. It consists of theory documents `O006-C140-CMP-D012` and `D013`,
seeded laboratory `SIM006`, and mastery set `MS11`. It supplements the complete
Penn Lesson 11 reader without copying its prose. The batch must use the regular
likelihood, decision, risk, and testing foundations already proved in C1 rather
than restating them as disconnected formulas.

The admitted theory boundary is:

1. `D012`: prior, likelihood, posterior, posterior predictive distribution,
   action and loss, posterior expected loss, Bayes rule, frequentist risk and
   Bayes risk, conjugate derivations, prior sensitivity, and conditions under
   which improper priors do or do not yield a proper posterior;
2. `D013`: credible sets versus confidence procedures, fixed-parameter
   coverage versus prior-averaged calibration, Bayesian decisions versus
   size/power control, Bayes factors and prior sensitivity, posterior
   predictive checks versus p-values, optional-stopping assumptions, and
   explicit examples/counterexamples showing why the guarantees differ;
3. `SIM006`: deterministic calibration experiments that hold the data-generating
   parameter fixed, vary it over a declared grid, report conditional coverage
   and prior-averaged behavior separately, and test numerical assertions;
4. `MS11`: at least eight nontrivial problems satisfying the complete metadata,
   staged-hint, short-answer, worked-solution, and stable-ID contract.

Every probability statement must identify what is random and what is fixed.
An equal-tail posterior interval is not called a confidence interval merely
because its numerical endpoints resemble one; a frequentist coverage statement
is not called a posterior probability. Bayes rules must name the loss and prior.
Frequentist tests must name size/power guarantees. Bayes factors must expose the
prior on every parameter that is integrated out. Prior-averaged calibration may
not be presented as uniform fixed-parameter coverage. Neither paradigm may be
declared universally superior from one calibrated example.

All content is original CC BY-SA 4.0 with provenance exactly
`OpenAI Codex gpt-5.6-sol, Ultra`. Stable IDs, formulas, cross-references,
reader HTML, backend entities/relations, seeded CSV/SVG outputs, and static QA
must remain deterministic and browser-free. C3 is complete only when all four
items build cumulatively with C1+C2 and pass write/check-only replay. C140
remains active afterward for the remaining mastery sets, three further
cumulative assessments, and two capstones.
