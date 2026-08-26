# Lesson 12 terminology QA

The cumulative id-ID glossary currently ends at `O006-TERM-0168`. Lesson 12
must preserve established choices including `peubah acak`, `penduga`, `nilai
dugaan`, `varians`, `galat baku`, `selang kepercayaan`, `uji hipotesis`, and
`fungsi kemungkinan`. The following candidate rows are reserved for the later
Lesson 12 translation; this ingest step does not yet mutate the cumulative
glossary.

| Proposed ID | English | Indonesian | Controlling distinction |
|---|---|---|---|
| O006-TERM-0169 | simple linear regression | regresi linear sederhana | use *linear*, not *linier*, consistently with formal mathematical Indonesian |
| O006-TERM-0170 | predictor / explanatory variable | peubah prediktor / peubah penjelas | the input/design coordinate; do not imply stochastic independence |
| O006-TERM-0171 | response / outcome variable | peubah respons / peubah hasil | modeled outcome, not a deterministic function unless explicitly stated |
| O006-TERM-0172 | deterministic / functional relationship | hubungan deterministik / hubungan fungsional | exact relation, contrasted with a statistical relationship |
| O006-TERM-0173 | statistical relationship | hubungan statistis | conditional response varies around a mean relation |
| O006-TERM-0174 | scatterplot | diagram pencar | reader-facing plot term |
| O006-TERM-0175 | least squares | kuadrat terkecil | name of the criterion/method |
| O006-TERM-0176 | least-squares estimator / estimate | penduga / nilai dugaan kuadrat terkecil | preserve the statistic-versus-realized-value distinction |
| O006-TERM-0177 | least-squares criterion | kriteria kuadrat terkecil | the residual-sum-of-squares objective |
| O006-TERM-0178 | fitted value | nilai suaian | `hat y_i`; keep distinct from a future response prediction |
| O006-TERM-0179 | residual | sisaan (residual) | observed response minus fitted value; introduce the English parenthetical once |
| O006-TERM-0180 | prediction error | galat prediksi | source's observed-minus-line quantity; distinguish from out-of-sample prediction error |
| O006-TERM-0181 | regression line | garis regresi | fitted or population line must be qualified in context |
| O006-TERM-0182 | intercept | intersep (titik potong) | use *intersep* in formulas and explain geometrically once |
| O006-TERM-0183 | slope | kemiringan | coefficient multiplying the predictor |
| O006-TERM-0184 | centered predictor | prediktor terpusat | `x_i-xbar`; makes the intercept the mean response at `xbar` |
| O006-TERM-0185 | error term | suku galat | model disturbance `epsilon_i`, not an observed residual |
| O006-TERM-0186 | fixed-design linear model | model linear rancangan tetap | exact inference is conditional on fixed predictor values |
| O006-TERM-0187 | homoscedasticity | homoskedastisitas | equal conditional error variance |
| O006-TERM-0188 | coefficient of determination | koefisien determinasi | retain `R^2` notation |
| O006-TERM-0189 | analysis of variance | analisis varians (ANOVA) | preserve ANOVA as the standard abbreviation |
| O006-TERM-0190 | correlation coefficient | koefisien korelasi | reserve `rho` for the population coefficient and `r` for the sample coefficient |
| O006-TERM-0191 | prediction interval | selang prediksi | interval for a future response; not a mean-response confidence interval |
| O006-TERM-0192 | residual diagnostics | diagnostik sisaan | checks model assumptions using residual surfaces |

The existing Indonesian-field terminology audit remains controlling. No new
external terminology source was needed for this bounded ingest step. These
choices should be appended only when translation starts and after a collision
check against the then-current cumulative glossary.
