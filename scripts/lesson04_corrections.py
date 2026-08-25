#!/usr/bin/env python3
"""Apply and register every admitted Lesson 04 target-only correction."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson04_source_findings.md"
DOCUMENT_ID = "O006-PSU-005"
FIRST_CORRECTION_ORDINAL = 47
ASSET_SOURCE_SHA256 = "5c6f266e5a56ef3aa37bed6a8af263e64cd235691100b38d7cdf3475812d268c"
ASSET_TYPO = b'<text class="cls-8" transform="translate(252.88 244.77) scale(0.58)">1</text>'
ASSET_REPAIR = b'<text class="cls-8" transform="translate(252.88 244.77) scale(0.58)">2</text>'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_math(main: Tag, short_id: str, expected_sha256: str, target: str) -> dict[str, object]:
    # Compact registry literals spell physical line breaks as ``\n``. No
    # admitted target uses a TeX control sequence beginning with ``\n``.
    target = target.replace(r"\n", "\n")
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson04 correction math identity differs: {math_id}")
    node = nodes[0]
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson04 correction math source differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson04 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def repair_following_text(
    main: Tag, short_math_id: str, expected: str, target: str
) -> dict[str, object]:
    math_id = f"{DOCUMENT_ID}-{short_math_id}"
    node = main.select_one(f'[data-o006-math-id="{math_id}"]')
    if node is None or not isinstance(node.next_sibling, NavigableString):
        raise RuntimeError(f"Lesson04 following-text identity differs: {math_id}")
    sibling = node.next_sibling
    source = str(sibling)
    if source != expected:
        raise RuntimeError(f"Lesson04 following-text source differs: {math_id}: {source!r}")
    sibling.replace_with(NavigableString(target))
    return {
        "surface": "text-after-math",
        "math_id": math_id,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def segment_surfaces(rows: list[dict[str, str]], short_ids: list[str]) -> list[dict[str, object]]:
    by_id = {row["segment_id"]: row for row in rows}
    surfaces: list[dict[str, object]] = []
    for short_id in short_ids:
        segment_id = f"{DOCUMENT_ID}-{short_id}"
        row = by_id.get(segment_id)
        if row is None:
            raise RuntimeError(f"Lesson04 correction segment missing: {segment_id}")
        source = row["source_text"]
        target = row["target_text"]
        if row["status"] != "translated" or not target.strip():
            raise RuntimeError(f"Lesson04 correction segment unfinished: {segment_id}")
        if sha256(source.encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"Lesson04 correction source binding differs: {segment_id}")
        if source == target:
            raise RuntimeError(f"Lesson04 admitted prose correction is unchanged: {segment_id}")
        surfaces.append({
            "surface": "translation-segment",
            "segment_id": segment_id,
            "source_surface_sha256": row["source_sha256"],
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })
    return surfaces


def record(defect_number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson04 defect has no target evidence: D{defect_number:03d}")
    return {
        "correction_id": f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}",
        "source_defect_id": f"L04-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def corrected_asset(authority: bytes) -> tuple[bytes, dict[str, object]]:
    if len(authority) != 2_259 or sha256(authority) != ASSET_SOURCE_SHA256:
        raise RuntimeError("Lesson04 authority SVG differs")
    if authority.count(ASSET_TYPO) != 1 or ASSET_REPAIR in authority:
        raise RuntimeError("Lesson04 SVG label-defect surface differs")
    target = authority.replace(ASSET_TYPO, ASSET_REPAIR)
    return target, {
        "surface": "asset",
        "asset_id": "O006-PSU-005-A0001",
        "source_path": "authority/assets/stat415/lesson04/STAT-415-SEC-1-15.svg",
        "target_path": "build/html-id/assets/lesson04/STAT-415-SEC-1-15.svg",
        "source_surface_sha256": sha256(authority),
        "target_surface_sha256": sha256(target),
        "source_bytes": len(authority),
        "target_bytes": len(target),
    }


def apply_lesson04_corrections(
    main: Tag, rows: list[dict[str, str]], authority_asset: bytes
) -> tuple[list[dict[str, object]], bytes]:
    finding_ids = re.findall(r"^## (L04-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_findings = [f"L04-D{i:03d}" for i in range(1, 36)]
    if finding_ids != expected_findings:
        raise RuntimeError("Lesson04 admitted finding sequence differs")

    records: list[dict[str, object]] = []
    records.append(record(1, [apply_math(main, "M0030", "1d0caf04a03e184dd26ba38eac9c18c0eb661dc0293f66689d869444c5b3572c", r"\[\begin{align*}\n    \frac{d}{dp}L(p)=\left[\prod_{i=1}^n {10\choose x_i}\right]\left(\sum x_i\right)p^{\sum x_i-1}(1-p)^{10n-\sum x_i}-\left[\prod_{i=1}^n {10\choose x_i}\right]p^{\sum x_i}\left(10n-\sum x_i\right)(1-p)^{10n-\sum x_i-1}\n\end{align*}\]")], "use lowercase p consistently"))
    records.append(record(2, [apply_math(main, "M0073", "a6ac5e94e8fdfe32b3d64a0b7a6362fc5b739bb47e373b4bca002396c4906f74", r"\[\begin{align*}\n         \ell(\theta)=\ln L(\theta)=\ln \prod_{i=1}^n f(x_i|\theta)=\sum_{i=1}^n \ln f(x_i|\theta)\n     \end{align*}\]")], "restore the conditioning bar"))
    records.append(record(3, [apply_math(main, "M0098", "af52c1d06484165835ce7347ce9b3215e63aac44dceef73092e0bc89d8b0dc27", r"\[\begin{align*} L(\theta)=\prod_{i=1}^n \frac{1}{\Gamma(\alpha)\theta^\alpha}x_i^{\alpha-1}e^{-x_i/\theta}=\left(\frac{1}{\Gamma(\alpha)\theta^\alpha}\right)^n\left(\prod_{i=1}^n x_i\right)^{\alpha-1}e^{-\frac{\sum x_i}{\theta}} \end{align*}\]")], "use the Gamma scale parameter theta"))
    records.append(record(4, [apply_math(main, "M0099", "53de406ed7f795fb119e79ac9232664ebde521ffcc7307ba5361bde532fd682d", r"\[\begin{align*}\n         \ell(\theta)=-n\ln \Gamma(\alpha)-n\alpha\ln \theta+(\alpha-1)\sum_{i=1}^n\ln x_i-\frac{\sum_{i=1}^n x_i}{\theta}\n     \end{align*}\]")], "remove the nested logarithm and state the equivalent sum"))
    records.append(record(5, [apply_math(main, "M0108", "2182836b0dd38dcedf7ca513e40817d8cef3819fb6c12eb0ad0f0d3976d69019", r"\(p\)")], "the Geometric parameter is p"))
    records.append(record(6, [apply_math(main, "M0116", "c12d2dc793e9cfded3c91e678ddd938fe352d9a1b438395af90b96ac9bab073e", r"\[\begin{align*}\n    \hat{\theta}=\frac{\sum x_i}{n\alpha}=\frac{3.4+8.1+5.5}{3(3)}=\frac{17}{9}\approx1.8889\n\end{align*}\]")], "complete the numerical estimate"))
    records.append(record(7, [apply_math(main, "M0121", "c857353f56b16c3b9809bc9891f820997120947330177e41e7371af5a2c36491", r"\[\begin{align*}\n    \ell(\lambda)=-n\lambda +\left(\sum x_i\right)\ln \lambda-\sum_{i=1}^n\ln(x_i!)\n\end{align*}\]")], "the factorial product is in the denominator"))
    records.append(record(8, segment_surfaces(rows, ["S0195", "S0196", "S0197", "S0198"]) + [repair_following_text(main, "M0138", "!.", ".")], "the score has no interior zero and a^-n is decreasing"))
    records.append(record(9, [apply_math(main, "M0155", "d59e7e9ad38e4ed5e50c5b853a337f2e89bf6a05e9af52d4f1944e494d0620ec", r"\[\begin{align*}\n    \mathbf{1}_{\{y \in \{0,1\}\}}=\begin{cases}\n    1 & \text{ if $y=0$ or $y=1$}\\\n    0 & \text{otherwise}\n    \end{cases}\n\end{align*}\]")], "restore the missing Bernoulli support value"))
    records.append(record(10, [apply_math(main, "M0157", "75017976868e2c1804b0a83fde3036a0b83187cac10b3d4d0382d675466b3d0a", r"\[\begin{align*}\n    L(p)=\prod_{i=1}^n p^{y_i}(1-p)^{1-y_i}\mathbf{1}_{\{y_i\in \{0,1\}\}}=p^{\sum_i y_i}(1-p)^{n-\sum_i y_i}\prod_{i=1}^n\mathbf{1}_{\{y_i\in \{0,1\}\}}\n\end{align*}\]")], "index every Bernoulli product factor by i"))
    d011 = [
        apply_math(main, "M0160", "118cfaaf548c7a4e0055b97d05d1dfbbe44cba55357744de4d09fe0012b4124c", r"\[\begin{align*}\n    \frac{d\ell(p)}{dp}=\frac{\sum_i y_i}{p}-\frac{n-\sum_i y_i}{1-p}\n\end{align*}\]"),
        apply_math(main, "M0162", "55dcc3539a65d87e212d4cfa199f5bda44654c2d51ea7d407a7e3d9685f6218f", r"\[\begin{align*}\n    & \frac{\sum_i y_i}{p}=\frac{n-\sum_i y_i}{1-p}, \qquad \Rightarrow \sum_i y_i-p\sum_i y_i=np-p\sum_i y_i\\\n    & \Rightarrow \sum_i y_i=np, \qquad \Rightarrow \hat{p}=\frac{\sum_i y_i}{n}\n\end{align*}\]"),
    ]
    records.append(record(11, d011, "restore the score label and the varying index"))
    records.append(record(12, [apply_math(main, "M0170", "34abf0db66ce1c22d3d122c90c431d8999f649e0863b8780d01b65bd4466d9aa", r"\[\begin{align*}\n    L(a)=\prod_{i=1}^n \frac{1}{a}\mathbf{1}_{\{x_i\in(0,a)\}}=a^{-n}\prod_{i=1}^n\mathbf{1}_{\{x_i\in(0,a)\}}\n\end{align*}\]")], "index the Uniform support indicator"))
    d013 = [
        apply_math(main, "M0176", "1aa1768d460883a8f52740d373da03f3ce36863f0dfec8d2e5b84b4904cecc03", r"\[\begin{align*}\n    a\downarrow X_{(n)}=Y_n\n\end{align*}\]"),
        apply_math(main, "M0179", "b7aa1bde1efa4453f371c888e6cd80e45ee56e6769db84bc651ae983ea3114f9", r"\(a\downarrow\max_i x_i\)"),
        *segment_surfaces(rows, ["S0241", "S0242", "S0243", "S0244", "S0245", "S0246", "S0247", "S0248", "S0249"]),
    ]
    records.append(record(13, d013, "preserve the strict open endpoint and report a boundary supremum, not an attained MLE"))
    d014 = [
        apply_math(main, "M0185", "f517c9b57f6971da1fa162beb9df50b5efbec339d72d92d4607131937a351307", r"\[\begin{align*}\n    L(m)=\prod_{i=1}^n \frac{2m^2}{x_i^3}\mathbf{1}_{\{x_i\ge m\}}=\frac{2^nm^{2n}}{\prod x_i^3}\prod_{i=1}^n\mathbf{1}_{\{x_i\ge m\}}\n\end{align*}\]"),
        apply_math(main, "M0187", "9cbb1e7abf57a43d2fb944fb6655a7b9ae85d5631782e206ff802e6018289b82", r"\[\begin{align*}\n    m^{2n}\prod_{i=1}^n\mathbf{1}_{\{x_i\ge m\}}\n\end{align*}\]"),
        apply_math(main, "M0188", "33535261146ba7e9ec21cfcf1f9be1d54378a78cce5424d914439315402e0c92", r"\(x_1\ge m\)"),
        apply_math(main, "M0189", "c3bf2fc8a395fdfa86f00a8fc8ef2ec70a9ae89a49a6bfa86ff84fc682777a02", r"\(x_2\ge m\)"),
        apply_math(main, "M0190", "67d6ede1898821b87de29fc991e28f4a4805f5e2cc1a4d5b73d3fcfad4be6e92", r"\(x_n\ge m\)"),
        *segment_surfaces(rows, ["S0260", "S0261", "S0262", "S0263", "S0264", "S0265", "S0266"]),
    ]
    records.append(record(14, d014, "use the inclusive Pareto endpoint stated by the density"))
    records.append(record(15, [apply_math(main, "M0230", "4c9dbd548a737c507452a5a529e0f562d573a1c6a540d84e9f850f98f3c07a58", r"\(\hat{\underline{\theta}}=(\hat{\theta}_1,\ldots,\hat{\theta}_p)\)")], "repair the final vector component"))
    records.append(record(16, [apply_math(main, "M0249", "224e34248601d10475c6e726d64846514ef2786d4ba6e6510f1a3898783821e1", r"\[\begin{align*}\n    L(\underline{\theta})=\prod_{i=1}^n \frac{1}{2b}e^{-\frac{|x_i-\mu|}{b}}=(2b)^{-n}e^{-\frac{\sum_i|x_i-\mu|}{b}}\n\end{align*}\]")], "restore the negative Laplace exponent"))
    d017 = [
        apply_math(main, "M0259", "3497e8346a0b5d31c914ebd3c01ebfbd59f501706b6c692b89bbb7af43a4ba5d", r"\[\partial_\mu|x_i-\mu|=\begin{cases}-1,&\mu<x_i,\\[-2pt] [-1,1],&\mu=x_i,\\[-2pt] 1,&\mu>x_i.\end{cases}\]"),
        apply_math(main, "M0262", "715abee4488cd9cb1db9e78bdfb9e958630bb43d9270677a362d0a14c0a21201", r"\[\begin{align*}\n0\in\sum_{i=1}^n\partial_\mu|x_i-\mu|\quad\Longleftrightarrow\quad \#\{i:x_i<\mu\}\le\frac n2,\ \#\{i:x_i>\mu\}\le\frac n2.\n\end{align*}\]"),
        *segment_surfaces(rows, ["S0333", "S0334", "S0335", "S0336", "S0337", "S0338"]),
    ]
    records.append(record(17, d017, "use the subgradient at the absolute-value kink"))
    records.append(record(18, [apply_math(main, "M0273", "463f2f8c4bae910216cae492c93279a47e0771d67c2a4090b61e47450a9e05db", r"\[\begin{align*}\n    \hat\mu&\in\operatorname{Median}(x_1,\ldots,x_n),\\\n    \hat b&=\frac1n\sum_{i=1}^n|x_i-\hat\mu|.\n\end{align*}\]")], "close the delimiters and state the Laplace MLEs"))
    d019 = [
        apply_math(main, "M0276", "b11c91bb2934fd170c713aa9d4ac0240dc5d0404a2e3729c80a269642ae6baa9", r"\(\theta\)"),
        apply_math(main, "M0277", "feb30be141c9c3df8eac744343bcc62fe24e4a02a779f6538fca45b89d66a2d0", r"\(\underline{\theta}=(\alpha,\theta)\)"),
    ]
    records.append(record(19, d019, "use theta consistently for the Gamma scale"))
    gamma_scores = apply_math(main, "M0282", "49eb39249a935856f26edfc953d7b69e02c42cbb5f085528ceab023569319f80", r"\[\begin{align*}\n    \frac{\partial\ell}{\partial\theta}&=-\frac{n\alpha}{\theta}+\frac{\sum_i x_i}{\theta^2},\\\n    \frac{\partial\ell}{\partial\alpha}&=-n\psi(\alpha)-n\ln\theta+\sum_i\ln x_i.\n\end{align*}\]")
    records.append(record(20, [gamma_scores], "restore the missing differential in the theta score"))
    records.append(record(21, [{**gamma_scores, "shared_surface_with": "L04-D020"}], "restore -n ln(theta) in the alpha score"))
    target_asset, asset_surface = corrected_asset(authority_asset)
    records.append(record(22, [asset_surface], "repair the second horizontal coordinate label to x_2"))
    records.append(record(23, segment_surfaces(rows, ["S0021", "S0030", "S0033", "S0034", "S0099", "S0368", "S0369"]), "define likelihood as observed-data joint mass/density viewed over parameters"))
    records.append(record(24, segment_surfaces(rows, ["S0064", "S0065", "S0066", "S0067", "S0068", "S0069"]), "state order preservation by the natural logarithm"))
    records.append(record(25, segment_surfaces(rows, ["S0085", "S0086", "S0087", "S0088"]), "include the Binomial boundary cases"))
    records.append(record(26, segment_surfaces(rows, ["S0052", "S0090", "S0091", "S0119", "S0120", "S0121", "S0122", "S0123", "S0301", "S0302", "S0303", "S0304", "S0305"]), "do not promote an unchecked critical point to an MLE"))
    d027 = [
        apply_math(main, "M0063", "3dd191d130cde5f9e42729600254afa48f1523337e7cd2ff7aee1531f0f05b22", r"\(\left[u_1(X_1, X_2, \ldots, X_n), u_2(X_1, X_2, \ldots, X_n), \ldots, u_m(X_1, X_2, \ldots, X_n)\right]\)"),
        apply_math(main, "M0065", "d21432e3c1c1ea8fe48ed743d5105dd234756f2268585ded2db5a71a1888cfc3", r"\[\begin{align*}\n    \hat{\theta}_i=u_i(X_1, X_2, \ldots, X_n), \qquad i=1, 2, \ldots, m\n\end{align*}\]"),
        *segment_surfaces(rows, ["S0011", "S0012", "S0013", "S0014", "S0015", "S0088", "S0099", "S0100", "S0101", "S0102", "S0103", "S0104", "S0105", "S0106", "S0107", "S0108", "S0109", "S0110", "S0156", "S0159", "S0162", "S0167", "S0170", "S0173", "S0180", "S0255", "S0265", "S0275", "S0286", "S0288", "S0290", "S0310", "S0323", "S0346", "S0347", "S0348", "S0355", "S0370", "S0371"]),
    ]
    records.append(record(27, d027, "distinguish the random estimator from its observed estimate"))
    records.append(record(28, [apply_math(main, "M0103", "624cbe11d8e1556c7a3dfd5d0d4228b74c7d2ad56113019fae7a12dee42b3555", r"\(\theta\)")], "solve the Gamma score for theta"))
    records.append(record(29, [apply_math(main, "M0122", "e617d25c5813e6a5245b2a8cde9fd274574f3624d88c591aa351fca4fe3c627e", r"\[\begin{align*}\n    \frac{d\ell(\lambda)}{d\lambda}=-n+\frac{\sum_i x_i}{\lambda}\n\end{align*}\]")], "label the differentiated Poisson log-likelihood"))
    d030 = [
        apply_math(main, "M0202", "adbc628cbc0ed3aee6b42a0a9542c87a54530f4d9651bf0a254bfa30677138a9", r"\([3c,10]\)"),
        apply_math(main, "M0206", "182577fff2d773d4b8d538b9888e9de38ea80e8161af8311335de7b633654733", r"\[\begin{align*}\n    f(x_i|c)=\frac{1}{10-3c}\mathbf{1}_{\{3c\le x_i\le10\}},\qquad i=1,2,3,4,\quad c<\frac{10}{3}.\n\end{align*}\]"),
    ]
    records.append(record(30, d030, "use the inclusive density convention consistently and state c<10/3"))
    records.append(record(31, segment_surfaces(rows, ["S0268", "S0269", "S0270", "S0271"]), "tie the order statistic to the feasible support boundary, not monotonicity alone"))
    d032 = [
        apply_math(main, "M0271", "6097a2f9db33707fafaf353567e1834f3fbb057802aa0068cffcf3d33a132703", r"\(\hat\mu\in\operatorname{Median}(x_1,\ldots,x_n)\)"),
        *segment_surfaces(rows, ["S0333", "S0334", "S0335", "S0336", "S0337", "S0338", "S0339", "S0340", "S0341", "S0342", "S0343", "S0344", "S0345", "S0346", "S0347", "S0348"]),
    ]
    records.append(record(32, d032, "state the set of sample medians and even-n nonuniqueness"))
    records.append(record(33, segment_surfaces(rows, ["S0360", "S0361", "S0362", "S0363"]), "state the profiled digamma root that generally requires numerical solution"))
    records.append(record(34, segment_surfaces(rows, ["S0021", "S0092", "S0113", "S0169", "S0281", "S0282"]), "repair five unambiguous source typos"))
    records.append(record(35, segment_surfaces(rows, ["S0218", "S0220", "S0221", "S0223"]), "call the Bernoulli surface a PMF, not a PDF"))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(47, 82)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson04 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson04 correction/finding binding differs")
    return records, target_asset
