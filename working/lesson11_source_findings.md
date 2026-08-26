# Lesson 11 frozen-source findings

Authority: `authority/upstream/stat415/Lesson11.html`  
Bytes: 99,359  
SHA-256: `4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32`  
Semantic-main topology SHA-256:
`9dc34953c3bbddbe8d4001d3fa76547ab0f8d85f226bbbf6fca1edd63a87efcd`

These findings authorize target-only repairs. The authority file remains
immutable. Correction IDs continue after the cumulative Lesson 10 suffix,
starting at `O006-PSU-ADV-0199`.

| Local ID | Kind | Frozen witness | Target-only disposition |
|---|---|---|---|
| L11-D001 | missing-symbol | Objective 2 ends `unknown parameter, .` | Restore `θ` and translate the objective naturally. |
| L11-D002 | terminology-defect | The horse example calls an event probability a `likelihood` | Use `peluang`; do not conflate event probability with the likelihood function. |
| L11-D003 | precision-qualification | The Poisson update uses table-rounded masses `0.022` and `0.105`, yielding `0.328` | Retain the pedagogical rounded calculation and add the exact reproducible values: 0.02160403145, 0.10444486296, and posterior 0.32552803889. |
| L11-D004 | support-defect | `M0057` integrates over the whole real line for an arbitrary parameter | Integrate over the parameter space `Θ`. |
| L11-D005 | measure-type-defect | Mixed discrete/continuous examples repeatedly call the law of discrete `Y` and its marginal a p.d.f. | Distinguish p.m.f., density, and mixed joint law in Indonesian prose. |
| L11-D006 | notation-defect | `M0118` says `k_1(p)` where the normalizing marginal is a function of `y` | Change it to `k_1(y)`. |
| L11-D007 | formula-defect | `M0134` normalizes Beta(4, y+1) with `Γ(4+y)` | Change the numerator to `Γ(5+y)`. |
| L11-D008 | mechanical-defects | `a a`, `they track`, `Bernouli`, and `posteriour` occur in visible prose | Repair the duplicated word, grammar, and spellings in the target. |
| L11-D009 | conditional/joint-label defect | The Bernoulli example calls `k(θ|x_1,…,x_n) ∝ h(θ)L(θ)` the joint distribution | Identify it as the posterior kernel; the joint kernel is `h(θ)L(θ)`. |
| L11-D010 | decision-theory qualification | Posterior mean/median minimizers are stated without conditions or nonuniqueness | State the finite-moment condition for squared loss and that any posterior median minimizes absolute loss. |
| L11-D011 | topology/accessibility defect | Example 11.6 has worked-solution prose but no semantic `Solution` heading | Add an Indonesian solution heading without deleting source content. |
| L11-D012 | mechanical distribution typo | Example 11.6 calls the posterior a `bets p.d.f.` | Restore `beta`. |
| L11-D013 | parameter/endpoint defect | The credible-interval introduction says the parameter is known and asks for `two value of y` | Say fixed but unknown, and identify `a(y), b(y)` as posterior bounds for the parameter conditional on observed `y`. |
| L11-D014 | measure-type defect | Example 11.7 calls the discrete geometric law `p(1-p)^y` a p.d.f. | Call it a p.m.f. |
| L11-D015 | numerical formula defect | `M0253` states `Γ(8)/(Γ(4)Γ(4)) = 35/4` | Use the exact value `140`; the source is low by a factor of 16. |
| L11-D016 | omitted-prior formula defect | `M0263` gives `k(θ|y)=g(y|θ)/k_1(y)` | Restore the factor `h(θ)` in the numerator. |
| L11-D017 | table-accessibility defect | The horse table has no caption or scoped headers | Add an Indonesian caption, column scopes, and row-header scopes without changing values. |
| L11-D018 | figure-accessibility/layout defect | The portrait is floated at an inline width of 70% and has only a short source caption | Preserve its separately frozen bytes, add an informative Indonesian caption/alt and component rights note, remove the float, center it, and let it reflow responsively. |
| L11-D019 | reproducibility omission | The two `qbeta` commands have correct outputs but no runtime contract | Declare Base R semantics and exact expected outputs `0.2253216` and `0.7746784`; no seed is needed. |
| L11-D020 | interpretation/surface defect | `Key Takeways` is misspelled and the summary calls credible intervals Bayesian counterparts without stating the different probability interpretation | Repair the heading and explicitly distinguish posterior-probability coverage from repeated-sampling confidence coverage. |

Independent numerical witnesses:

- `P(X=7 | λ=3) = exp(-3) 3^7 / 7! = 0.02160403145248382`;
- `P(X=7 | λ=5) = exp(-5) 5^7 / 7! = 0.104444862957054`;
- exact posterior `P(λ=3 | X=7) = 0.32552803888965215`;
- `Γ(8)/(Γ(4)Γ(4)) = 140`;
- Base R-compatible Beta(4,4) quantiles are `0.2253215840` and
  `0.7746784160`.

Asset closure: `assets/bayes.png` is frozen separately at 142,195 bytes,
SHA-256 `2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22`,
PNG 308 × 321 RGBA. The page-level CC BY-NC 4.0 notice is retained; no
asset-specific exception was found.
