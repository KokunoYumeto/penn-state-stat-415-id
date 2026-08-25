# Lesson 04 mathematical/source audit

Audited the complete instructional `<main>` in
`authority/upstream/stat415/Lesson04.html` (lines 496–1127; 106,614 bytes;
SHA-256 `9fe5790e577c6ce0b808c92683aea45442187f80f74d540b20bd4514bdefc060`).

## High-confidence defects

1. **Likelihood is misdefined as a probability distribution** —
   `#def-likelihoodfunction`, lines 542–545; repeated at 645–651 and 1119.
   (L(\theta;x)) is the joint pmf/density evaluated at the observed sample and
   viewed as a function of \(\theta\); it is not generally a probability
   distribution over \(\theta\), and continuous observed data do not have
   positive point probability.

2. **Malformed monotonic-log statement** — line 592 says
   \(x_1<x_2\Rightarrow f(x_1)<f(x_2)\).
   Correct: for \(0<x_1<x_2\), \(\log x_1<\log x_2\); hence
   \(\arg\max L=\arg\max\log L\) where \(L>0\), treating \(L=0\) as
   log-likelihood \(-\infty\).

3. **Binomial boundary cases invalidate the stated second-derivative
   argument** — lines 625–629. Strict interior maximization holds only when
   \(0<\sum x_i<10n\). If every observation is 0 or 10, the MLE is
   respectively \(p=0\) or \(p=1\), where the displayed substitution is
   undefined.

4. **“A critical point is enough” is false without hypotheses** — lines 639
   and 669–670. A critical point can be a minimum, saddle, nonglobal maximum,
   or absent; boundaries and parameter-dependent support must be checked. The
   shortcut is valid under an explicitly established concavity/unimodality and
   interior condition. Reversal only if those conditions are added.

5. **Estimator/estimate distinction is collapsed** —
   `#def-MaximumLikelihoodEstimator.ms-3`, lines 647–651. The estimator should
   be \(u_i(X_1,\ldots,X_n)\); its observed estimate is
   \(u_i(x_1,\ldots,x_n)\). The source uses lowercase observed values for both.

6. **Missing conditioning bar** — line 664 has `f(x_i\theta)`.
   Correct: \(f(x_i\mid\theta)\).

7. **One-parameter Gamma derivation contains three exact errors** —
   `#exm-mleonparam2`, lines 701–709. `L(p)` must be \(L(\theta)\); the correct
   log-likelihood is
   \[
   \ell(\theta)=-n\log\Gamma(\alpha)-n\alpha\log\theta
   +(\alpha-1)\sum_i\log x_i-\frac{\sum_i x_i}{\theta},
   \]
   not \((\alpha-1)\log(\log\prod x_i)\); and the prose must say solve for
   \(\theta\), not \(p\).

8. **Geometric numerical example asks for the wrong parameter** —
   `#exm-mleonparam3`, line 720. It asks for an estimate of \(\theta\), but the
   model and solution use \(p\). Correct target: \(p\).

9. **Gamma numerical answer is unfinished** — `#exm-mleonparam4`, lines
   734–736.
   \[
   \hat\theta=\frac{3.4+8.1+5.5}{3\cdot3}
   =\frac{17}{9}\approx1.8889.
   \]

10. **Poisson log-likelihood has the factorial term’s wrong sign** —
    `#exm-mleonparam5`, lines 748–756. Correct:
    \[
    \ell(\lambda)=-n\lambda+\Bigl(\sum_i x_i\Bigr)\log\lambda
    -\sum_i\log(x_i!).
    \]
    The derivative’s left side should also be \(d\ell/d\lambda\), not merely
    \(d/d\lambda\).

11. **Uniform calculus discussion reverses monotonicity and invents a
    solution** — `#exm-suppparam1`, lines 787–790. \(-n/a=0\) has no solution,
    not \(a=\infty\); the displayed \(a^{-n}\) is decreasing, not increasing.

12. **Bernoulli indicator and likelihood indices are corrupted** —
    `#exm-suppparam2`, lines 827–850. Line 828 is missing `y=0`. Lines 837,
    845, and 849 use \(y_1\) where \(y_i\) or \(\sum_i y_i\) is required;
    indicators must also be indexed by \(i\). Bernoulli has a pmf, not a pdf.

13. **Uniform endpoint convention makes the claimed MLE nonexistent as
    written** — `#exm-suppparam3`, lines 854–884. The source explicitly uses
    \(0<x<a\), so at \(a=\max_i x_i\) one indicator is zero; the likelihood has
    a supremum as \(a\downarrow\max x_i\), but no attained maximum. Either
    change the density version to \(0<x\le a\), yielding
    \(\hat a=X_{(n)}\), or preserve the open endpoint and state that no MLE
    exists. The product in line 878 also needs
    \(\mathbf1_{\{x_i\in(0,a)\}}\), not unindexed \(x\).

14. **Pareto endpoint is internally inconsistent** — `#exm-suppparam4`, lines
    890 and 897–903. The stated support is \(x\ge m\), but the likelihood uses
    \(\mathbf1_{\{x_i>m\}}\). Use \(\ge\) to obtain
    \(\hat m=X_{(1)}\); with strict \(>\), the supremum at \(X_{(1)}\) is not
    attained.

15. **Shifted Uniform repeats the open/closed endpoint conflict** —
    `#exm-suppparam5`, lines 918 and 926–954. The model is announced as
    \((3c,10)\), but the density uses \(3c\le x_i\le10\). The estimate
    \(c=\min x_i/3=-5/3\) is attained only under the inclusive lower endpoint.
    Also state \(c<10/3\).

16. **The monotonic-support rule is overgeneralized** — line 913.
    “Increasing implies sample minimum; decreasing implies sample maximum”
    holds only with the corresponding feasible-set direction. Monotonicity
    alone does not determine which order statistic is the MLE.

17. **Laplace likelihood has a missing minus sign** — `#exm-multparam2`, line
    1038. Every factor must be \(\exp(-|x_i-\mu|/b)\); the line’s first
    expression has a positive exponent while its second expression has the
    correct negative exponent.

18. **Laplace differentiation ignores nondifferentiability and
    nonuniqueness** — lines 1057–1083. At \(x_i=\mu\),
    \(d|x_i-\mu|/d\mu\) does not exist; the displayed cases overlap and assign
    both \(-1\) and \(1\). Use a subgradient argument: any minimizer of
    \(\sum_i|x_i-\mu|\), equivalently any sample median, is an MLE. For even
    \(n\), the entire interval between the two central order statistics may
    maximize the likelihood.

19. **Final Laplace MLE formula is malformed TeX and incomplete mathematics**
    — lines 1085–1087. Correct:
    \[
    \hat\mu\in\operatorname{Median}(x_1,\ldots,x_n),\qquad
    \hat b=\frac1n\sum_{i=1}^n|x_i-\hat\mu|.
    \]
    The source omits the closing absolute-value delimiter and closing tuple
    syntax.

20. **Two-parameter Gamma example is inconsistent and its score is wrong** —
    `#exm-multparam3`, lines 1092–1109. The statement names
    \((\alpha,\beta)\), but every formula uses scale \(\theta\). Choose one
    notation. The first score’s numerator is missing `d`, and the
    \(\alpha\)-score omits \(-n\log\theta\):
    \[
    \frac{\partial\ell}{\partial\theta}
      =-\frac{n\alpha}{\theta}+\frac{\sum x_i}{\theta^2},\qquad
    \frac{\partial\ell}{\partial\alpha}
      =-n\psi(\alpha)-n\log\theta+\sum_i\log x_i.
    \]
    Thus \(\hat\theta=\bar x/\hat\alpha\), with \(\hat\alpha\) solving
    \[
    \log\hat\alpha-\psi(\hat\alpha)
    =\log\bar x-\frac1n\sum_i\log x_i
    \]
    numerically. “The Gamma function is not analytically tractable, therefore
    no analytic solution is possible” should be replaced by this precise
    statement.

## Unambiguous surface defects

- Literal `** likelihood**` at line 540.
- `definition og` at line 643.
- `0ne` at line 658.
- `The the` at line 733.
- `indication function` at lines 934 and 938.

## Coverage

Likelihood/log-likelihood construction; one-parameter Binomial, Geometric,
Gamma, and Poisson MLEs; parameter-dependent support via Uniform, Bernoulli
indicators, Pareto, and shifted Uniform; multiparameter Normal, Laplace, and
Gamma MLEs; numerical-root motivation.

## Translation traps

Preserve the distinction between *likelihood* and probability, *estimator* and
observed estimate, pmf and pdf, open and closed support, uppercase random
variables and lowercase realizations, shape versus scale Gamma parameters, and
“any sample median” versus a uniquely defined median.
