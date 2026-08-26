# Lesson 12 frozen-source findings

Authority: `authority/upstream/stat415/Lesson12.html`
Bytes: 144,220
SHA-256: `89569622b8fea9bcfc17d51717002ab9840b44e6d80a34ee476d94acd45b515d`
Semantic-main topology SHA-256:
`2adf6ef893702fdf0eb7094f26bffb728f2cab5a271cb9e21de00607cfc1ddca`

The frozen lesson covers deterministic and statistical relationships, the
least-squares idea and formulas, the fixed-design Gaussian simple-linear-model
surface, maximum-likelihood estimation, exact finite-sample distributions,
confidence intervals, and a slope test. These findings authorize only later
target-side repairs. The English authority and the present normalized source
remain byte- and formula-identical.

| Local ID | Kind | Frozen witness | Later target-only disposition |
|---|---|---|---|
| L12-D001 | missing-symbol | The overview asks about a relationship between two empty parenthetical placeholders. | Restore the intended predictor and response symbols, `x` and `y`. |
| L12-D002 | coverage mismatch | Objective 4 promises a confidence interval or test for the correlation parameter `rho`, but no such procedure appears in the lesson. | Mark the objective as unfulfilled by this source and supply the missing correlation-inference surface in the original companion. |
| L12-D003 | mechanical prose | Visible prose includes `we might we interested`, `two different type`, a leading `-let`, and an extra closing parenthesis after `sigma^2`. | Repair the grammar and punctuation without changing mathematical content. |
| L12-D004 | row-index and arithmetic defect | Table 12.1's `(64,121)` observation is the second row, but the following formulas use subscript 1; `M0056` gives fitted value 123.2 while `M0059` subtracts 123.3. | Use subscript 2 consistently and retain the computed fitted value 123.2, residual -2.2, and squared residual 4.84. |
| L12-D005 | placeholder prose | The note immediately before `M0088` is an entire *Lorem ipsum* paragraph. | Remove the placeholder from the derivative reader and replace it with a concise transition identifying the alternative computational slope formula. |
| L12-D006 | least-squares qualification | The source twice suggests that the least-squares formulas require a linear population relationship. | State the actual algebraic condition `S_xx > 0`; a line can be fit without assuming that the conditional mean is truly linear. Reserve linearity for model-based interpretation and inference. |
| L12-D007 | external-only proof | Theorem 12.1's derivation is carried only by two titleless YouTube iframes (Videos 12.1 and 12.2), with no HTML derivation or transcript. | Preserve only provenance links to the videos and supply a complete textual derivation in the derivative; do not redistribute video bytes. |
| L12-D008 | omitted proof | Theorem 12.2 says its result can be proved similarly and leaves the proof as an exercise, but provides no solution. | Add the full centered-parameterization derivation in the companion/solution surface. |
| L12-D009 | predictor-index defect | `M0136` states `Y_i = alpha + beta(x-xbar) + epsilon_i`. | Restore `x_i` in the centered predictor term. |
| L12-D010 | model-condition qualification | Exact sampling results are presented through the `LINE` mnemonic without consistently stating that the design points are fixed (or inference is conditional on them) and that `S_xx > 0`. | State the fixed-design/conditional-on-`X` and nondegeneracy conditions wherever the finite-sample laws are used. |
| L12-D011 | MLE objective defect | After saying the log likelihood must be minimized with respect to `alpha` and `beta`, `M0210` repeats the least-squares estimator formulas rather than displaying the residual sum of squares. | Display the quadratic objective `sum_i (Y_i-alpha-beta(x_i-xbar))^2`. |
| L12-D012 | derivative-label defect | The variance derivation says it differentiates the log likelihood, but `M0234` and `M0236` label the derivative as one of `L`, not `log L`. | Label both derivatives as derivatives of `log L`; retain the valid resulting score equation. |
| L12-D013 | missing hats in MLE | The first equality in `M0241` uses un-hatted `alpha` and `beta` after claiming their MLEs have been substituted. | Use `hat alpha` and `hat beta` in the residual sum of squares. |
| L12-D014 | malformed delimiters | `M0260` and `M0272` each omit a closing parenthesis inside an expected-value derivation. | Restore the missing delimiters while preserving the derivations. |
| L12-D015 | residual-index defect | `M0281` and `M0283` use `hat Y` inside sums indexed by `i`. | Use `hat Y_i` in both residual sums. |
| L12-D016 | distribution-symbol defect | `M0285` labels chi-square laws with Latin `x^2`. | Replace Latin `x` by `chi` in the three distribution labels. |
| L12-D017 | proof-closure defect | Theorem 12.7's proof is a verbal appeal to general normal-theory facts and unspecified textbooks; it does not establish the orthogonal decomposition or independence it invokes. | Supply the projection/decomposition argument and its exact rank conditions in the original rigor companion. |
| L12-D018 | inconsistent anchovy inputs | The displayed data table yields slope about -29.3948 and MSE about 5202.23, while later confidence-interval formulas use -29.402, 5139, and `S_xx=198.7453`. | Recompute all interval inputs from the displayed 14-row dataset and use one internally consistent witness. |
| L12-D019 | inconsistent anchovy intervals | The source's reported slope and intercept intervals do not reconcile with the displayed data and the stated `t` multiplier. | Use the independently recomputed intervals recorded in the mathematics audit. |
| L12-D020 | table accessibility | All six tables lack HTML `caption` elements, and all 31 header cells lack `scope`. | Add Indonesian captions and explicit column/row scopes without changing any table value. |
| L12-D021 | duplicate native IDs | Seven native ID values are duplicated: `fig-lesson9_1` (2), `fig-skin-cancer` (2), `fig-bidsgraph` (4), its caption UUID (2), `fig-scattertemp` (2), `fig-scattertemp2` (2), and `fig-iqnormal` (2). | Preserve source IDs in the normalized authority; generate unique target IDs and retain a reversible source-ID/occurrence map. |
| L12-D022 | image accessibility/layout | The ten image occurrences use inline widths of 60%, 70%, or 90%; six captions are only figure numbers, and none declares intrinsic HTML dimensions. | Preserve the nine separately frozen PNGs, center them, reflow responsively to the reading column, add useful Indonesian alt/captions, and prevent layout shift with intrinsic dimensions. |
| L12-D023 | video accessibility/offline closure | Three YouTube iframes have empty `title` attributes, no local transcript or static equivalent, no lazy-loading/sandbox, and require an external runtime. | Keep URL/caption provenance only; add descriptive titles and complete text/static equivalents in the derivative. Never redistribute the videos. |
| L12-D024 | reproducibility and mastery gap | The semantic main contains zero code blocks despite claiming R/Minitab use; it supplies no environment or expected-output checks, no worked slope-test example, and no prediction/mean-response interval or diagnostic procedure. | Close these gaps in the original reproducible-simulation and mastery companion rather than attributing new material to Penn State. |

Independent numerical witness from the 14 displayed anchovy observations:

- `xbar = 6.183571428571428`, `ybar = 270.5`;
- `S_xx = 197.5043214285714`;
- least-squares slope `b = -29.39482517651965`;
- `SSE = 62426.75598107165`, `MSE = 5202.229665089304`;
- using `t_(12,0.975) = 2.178812829`, the slope interval is approximately
  `[-40.577002713, -18.212647640]` and the intercept interval is approximately
  `[228.499866913, 312.500133087]`.

Asset boundary: the semantic main has ten image occurrences resolving to nine
unique official PNG URLs and three YouTube embeds. The PNGs are frozen and
byte-verified separately. The video URLs are retained only as provenance links.
The page-level `CC BY-NC 4.0 except where otherwise noted` witness is retained;
no asset-specific exception is asserted without a separate source witness.
