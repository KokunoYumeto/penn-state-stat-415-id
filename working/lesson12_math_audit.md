# Lesson 12 protected-mathematics audit

The frozen semantic main contains 352 mathematics nodes: 266 inline and 86
display. Their ordered source-text aggregate SHA-256 is
`1e5b97f1531ce06c3a150184c29694dcf08fb80e2e100517c032a10ad76e71a4`.
Normalization must not change any formula node.

The least-squares formulas, the normal-model likelihood, the centered-design
estimators, and their exact normal/t/chi-square sampling laws are mathematically
usable once the fixed-design, `S_xx > 0`, and Gaussian-error hypotheses are made
explicit. The following stable nodes require later registered target repairs:

| Stable math ID | Frozen issue | Later target repair | Finding |
|---|---|---|---|
| `O006-PSU-013-M0056`, `M0059`, `M0060` | Row 2 is labeled with subscript 1; 123.2 changes to 123.3 | Use subscript 2 and one fitted value, 123.2 | L12-D004 |
| `O006-PSU-013-M0136` | centered term is `x-xbar` | use `x_i-xbar` | L12-D009 |
| `O006-PSU-013-M0210` | repeats `a=ybar` and the formula for `b` where the objective should appear | use the residual sum of squares in `alpha,beta` | L12-D011 |
| `O006-PSU-013-M0234`, `M0236` | derivative is labeled `partial L / partial sigma^2` | label it `partial log L / partial sigma^2` | L12-D012 |
| `O006-PSU-013-M0241` | first residual sum uses un-hatted `alpha,beta` | use `hat alpha,hat beta` | L12-D013 |
| `O006-PSU-013-M0260`, `M0272` | expected-value expressions omit a closing parenthesis | restore the delimiters | L12-D014 |
| `O006-PSU-013-M0281`, `M0283` | residual sum uses `hat Y` | use `hat Y_i` | L12-D015 |
| `O006-PSU-013-M0285` | chi-square laws are printed as Latin `x^2` | use `chi^2` | L12-D016 |
| `O006-PSU-013-M0325`, `M0327`, `M0333` | `S_xx`, slope, and MSE do not agree with the displayed dataset | replace all three numerical inputs with one recomputed dataset witness | L12-D018/L12-D019 |

For the displayed anchovy data, direct recomputation gives
`b=-29.39482517651965`, `S_xx=197.5043214285714`,
`SSE=62426.75598107165`, and `MSE=5202.229665089304`. With
`t_(12,0.975)=2.178812829`, the slope half-width is 11.182177536 and the
intercept half-width is 42.000133087. The corresponding intervals are
`[-40.577002713,-18.212647640]` and `[228.499866913,312.500133087]`.

Every other mathematics node remains text-identical unless a later registered
correction supplies equally explicit evidence. The source's unproved sampling
distribution claims receive additive proof in the original companion, not a
silent mutation of the normalized authority.
