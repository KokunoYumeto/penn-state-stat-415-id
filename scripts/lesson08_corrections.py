#!/usr/bin/env python3
"""Apply and register every admitted Lesson 08 target-only correction."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson08_source_findings.md"
DOCUMENT_ID = "O006-PSU-009"
FIRST_CORRECTION_ORDINAL = 135

ASSETS = (
    {
        "asset_id": "O006-PSU-009-A0001",
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-1-1.png",
        "bytes": 47_071,
        "sha256": "215b809d8213ef56a36c6bf69f1886f964d39d607532d551779f859052c17c0b",
        "source_alt": "Histogram of t distribution",
        "target_alt": (
            "Histogram 25 pengamatan berdistribusi t: sumbu horizontal memuat nilai y "
            "sekitar −2,3 sampai 2,6 dan sumbu vertikal memuat frekuensi; sebagian besar "
            "pengamatan berada antara −1 dan 1. Data ini dipakai untuk menduga parameter "
            "derajat kebebasan."
        ),
    },
    {
        "asset_id": "O006-PSU-009-A0002",
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-8-1.png",
        "bytes": 55_503,
        "sha256": "c41f8223ba0306e6027ea44ec0c293b0b4a9ffdd558d7738e0c911ecc69725b6",
        "source_alt": "Distribution of bootstrap samples",
        "target_alt": (
            "Histogram cuplikan sumber untuk 1.000 nilai dugaan derajat kebebasan dari "
            "bootstrap parametrik: distribusinya sangat menceng ke kanan, dengan sebagian "
            "besar nilai dekat bagian kiri dan beberapa nilai ekstrem hingga sekitar 28 juta. "
            "Cuplikan hulu tidak menyertakan keadaan RNG."
        ),
    },
    {
        "asset_id": "O006-PSU-009-A0003",
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-14-1.png",
        "bytes": 59_111,
        "sha256": "51ed4921773d92575cf3cb560d692c49e2022581b479093ad0a870302208798e",
        "source_alt": "Distribution of bootstrap samples (nonparametric boostrap)",
        "target_alt": (
            "Histogram cuplikan sumber untuk 1.000 nilai dugaan derajat kebebasan dari "
            "bootstrap nonparametrik: massa sangat terkonsentrasi di kiri dan ekor kanan "
            "memuat beberapa nilai ekstrem hingga sekitar 28 juta. Cuplikan hulu tidak "
            "menyertakan keadaan RNG."
        ),
    },
    {
        "asset_id": "O006-PSU-009-A0004",
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-18-1.png",
        "bytes": 52_007,
        "sha256": "11820bf246f37f1463f0384ce77672b0ce0d63466c186e6fb8bf25c5b1f522ad",
        "source_alt": "Histogram of a Pareto distribution",
        "target_alt": (
            "Histogram 40 pengamatan Pareto: sumbu horizontal memuat nilai x dan sumbu "
            "vertikal memuat frekuensi; 27 pengamatan berada di bawah 10, distribusinya "
            "menceng kuat ke kanan, dan satu pengamatan ekstrem berada dekat 66."
        ),
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(defect_number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}"


def one_unit(main: Tag, short_id: str) -> Tag:
    unit_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-id="{unit_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson08 correction unit identity differs: {unit_id}")
    return nodes[0]


def math_node(main: Tag, short_id: str) -> tuple[str, Tag]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson08 correction math identity differs: {math_id}")
    return math_id, nodes[0]


def apply_math(
    main: Tag, short_id: str, expected_sha256: str, target: str
) -> dict[str, object]:
    target = target.replace(r"\n", "\n")
    math_id, node = math_node(main, short_id)
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson08 correction math source differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson08 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def replace_unit_text_by_hash(
    main: Tag,
    short_id: str,
    expected_sha256: str,
    target: str,
    surface: str = "code",
) -> dict[str, object]:
    node = one_unit(main, short_id)
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson08 protected unit text differs: {DOCUMENT_ID}-{short_id}")
    if source == target:
        raise RuntimeError(f"Lesson08 correction makes no unit change: {short_id}")

    # Quarto code blocks bind one stable, aria-hidden anchor to each source
    # line.  Replacing the entire <code> payload would silently discard those
    # locale-neutral unit identities.  Reuse every source line wrapper and its
    # anchor, add unnumbered wrappers only when the corrected code has more
    # lines, and retain surplus anchors invisibly when it has fewer lines.
    line_wrappers = [
        child
        for child in node.children
        if isinstance(child, Tag) and child.name == "span" and child.get("id")
    ]
    if line_wrappers:
        source_unit_ids = [
            str(descendant.get("data-o006-id"))
            for descendant in node.select("[data-o006-id]")
        ]
        preserved: list[tuple[Tag, list[Tag]]] = []
        for wrapper in line_wrappers:
            stable_descendants = list(wrapper.select("[data-o006-id]"))
            if len(stable_descendants) != 1 or stable_descendants[0].name != "a":
                raise RuntimeError(
                    f"Lesson08 code-line identity topology differs: {DOCUMENT_ID}-{short_id}"
                )
            anchor = stable_descendants[0].extract()
            wrapper.clear()
            wrapper.append(anchor)
            preserved.append((wrapper, [anchor]))

        target_lines = target.split("\n")
        rebuilt: list[Tag] = []
        for index, target_line in enumerate(target_lines):
            if index < len(preserved):
                wrapper = preserved[index][0]
            else:
                wrapper = BeautifulSoup("", "html.parser").new_tag("span")
                wrapper["class"] = ["o006-target-code-line"]
            wrapper.append(NavigableString(target_line))
            rebuilt.append(wrapper)
        rebuilt.extend(wrapper for wrapper, _anchors in preserved[len(target_lines):])

        node.clear()
        for index, wrapper in enumerate(rebuilt):
            node.append(wrapper)
            if index < len(target_lines) - 1:
                node.append(NavigableString("\n"))
        if [
            str(descendant.get("data-o006-id"))
            for descendant in node.select("[data-o006-id]")
        ] != source_unit_ids:
            raise RuntimeError(
                f"Lesson08 corrected code lost stable identities: {DOCUMENT_ID}-{short_id}"
            )
    else:
        node.clear()
        node.append(NavigableString(target))
    if node.get_text() != target:
        raise RuntimeError(f"Lesson08 corrected unit did not materialize: {short_id}")
    return {
        "surface": surface,
        "unit_id": f"{DOCUMENT_ID}-{short_id}",
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def row_by_short_id(
    rows: list[dict[str, str]], short_id: str
) -> tuple[str, dict[str, str]]:
    segment_id = f"{DOCUMENT_ID}-{short_id}"
    matches = [row for row in rows if row.get("segment_id") == segment_id]
    if len(matches) != 1:
        raise RuntimeError(f"Lesson08 correction segment identity differs: {segment_id}")
    row = matches[0]
    source = row["source_text"]
    target = row["target_text"]
    if (
        row.get("status") != "translated"
        or not target.strip()
        or sha256(source.encode("utf-8")) != row.get("source_sha256")
    ):
        raise RuntimeError(f"Lesson08 correction segment binding differs: {segment_id}")
    return segment_id, row


def segment_surface(
    rows: list[dict[str, str]], short_id: str
) -> dict[str, object]:
    segment_id, row = row_by_short_id(rows, short_id)
    if row["source_text"] == row["target_text"]:
        raise RuntimeError(f"Lesson08 admitted prose correction is unchanged: {segment_id}")
    return {
        "surface": "translation-segment",
        "segment_id": segment_id,
        "source_surface_sha256": row["source_sha256"],
        "target_surface_sha256": sha256(row["target_text"].encode("utf-8")),
    }


def segment_surfaces(
    rows: list[dict[str, str]], short_ids: list[str]
) -> list[dict[str, object]]:
    return [segment_surface(rows, short_id) for short_id in short_ids]


def replace_segment_targets(
    main: Tag,
    rows: list[dict[str, str]],
    changes: list[tuple[str, str, str]],
) -> dict[str, dict[str, object]]:
    """Replace exact translated text nodes, preserving source/translation bindings."""

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for short_id, expected_target, corrected_target in changes:
        _segment_id, row = row_by_short_id(rows, short_id)
        if row["target_text"] != expected_target:
            raise RuntimeError(f"Lesson08 admitted translation changed: {short_id}")
        if expected_target == corrected_target:
            raise RuntimeError(f"Lesson08 segment correction is a no-op: {short_id}")
        grouped[expected_target].append((short_id, corrected_target))

    surfaces: dict[str, dict[str, object]] = {}
    for expected_target, targets in grouped.items():
        nodes = [
            value
            for value in main.descendants
            if isinstance(value, NavigableString) and str(value) == expected_target
        ]
        targets.sort(key=lambda item: int(item[0][1:]))
        if len(nodes) != len(targets):
            raise RuntimeError(
                "Lesson08 translated-node census differs for "
                f"{[short_id for short_id, _target in targets]}: {len(nodes)}"
            )
        for node, (short_id, corrected_target) in zip(nodes, targets):
            segment_id, row = row_by_short_id(rows, short_id)
            node.replace_with(NavigableString(corrected_target))
            surfaces[short_id] = {
                "surface": "translated-segment-correction",
                "segment_id": segment_id,
                "source_surface_sha256": row["source_sha256"],
                "translation_surface_sha256": sha256(expected_target.encode("utf-8")),
                "target_surface_sha256": sha256(corrected_target.encode("utf-8")),
            }
    return surfaces


def insert_note_after(
    main: Tag,
    short_id: str,
    defect_number: int,
    text: str,
    note_index: int = 1,
) -> dict[str, object]:
    anchor = one_unit(main, short_id)
    source_marker = f"{DOCUMENT_ID}-{short_id}\n{sha256(str(anchor).encode('utf-8'))}"
    selector = (
        f'[data-o006-correction-id="{correction_id(defect_number)}"]'
        f'[data-o006-note-index="{note_index}"]'
    )
    if main.select(selector):
        raise RuntimeError(f"Lesson08 correction note already exists: D{defect_number:03d}")
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction"]
    note["data-o006-correction-id"] = correction_id(defect_number)
    note["data-o006-note-index"] = str(note_index)
    note["role"] = "note"
    note.append(NavigableString(text))
    anchor.insert_after(note)
    target_marker = source_marker + "\n" + str(note)
    return {
        "surface": "adjacent-correction-note",
        "unit_id": f"{DOCUMENT_ID}-{short_id}",
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256(target_marker.encode("utf-8")),
    }


def insert_output_snapshot_note(
    main: Tag,
    output_short_id: str,
    expected_output_sha256: str,
    note_index: int,
    text: str,
) -> dict[str, object]:
    output = one_unit(main, output_short_id)
    output_text = output.get_text()
    if sha256(output_text.encode("utf-8")) != expected_output_sha256:
        raise RuntimeError(f"Lesson08 fixed output differs: {output_short_id}")
    wrapper = output.find_parent("div", class_="cell-output")
    if wrapper is None or not wrapper.get("data-o006-id"):
        raise RuntimeError(f"Lesson08 output wrapper differs: {output_short_id}")
    source_marker = "\n".join(
        (
            f"{DOCUMENT_ID}-{output_short_id}",
            str(wrapper.get("data-o006-id")),
            expected_output_sha256,
        )
    )
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", "reproducibility-note"]
    note["data-o006-correction-id"] = correction_id(7)
    note["data-o006-note-index"] = str(note_index)
    note["role"] = "note"
    note.append(NavigableString(text))
    wrapper.insert_after(note)
    return {
        "surface": "output-disposition-note",
        "unit_id": f"{DOCUMENT_ID}-{output_short_id}",
        "output_sha256": expected_output_sha256,
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256(
            (source_marker + "\n" + str(note)).encode("utf-8")
        ),
    }


def remove_unit(main: Tag, short_id: str) -> dict[str, object]:
    node = one_unit(main, short_id)
    source = str(node)
    unit_id = f"{DOCUMENT_ID}-{short_id}"
    removed_unit_ids = [
        unit_id,
        *[
            str(descendant.get("data-o006-id"))
            for descendant in node.select("[data-o006-id]")
        ],
    ]
    node.extract()
    if main.select(f'[data-o006-id="{unit_id}"]'):
        raise RuntimeError(f"Lesson08 removed unit remains: {unit_id}")
    target = f"removed:{unit_id}"
    return {
        "surface": "removed-editorial-structure",
        "unit_id": unit_id,
        "removed_unit_ids": removed_unit_ids,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
        "substantive_following_content_retained": True,
    }


def repair_figures(main: Tag) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    asset_root = ROOT / "authority" / "assets" / "stat415" / "lesson08"
    target_style = "display:block;width:100%;max-width:100%;height:auto;margin-inline:auto"
    for row in ASSETS:
        asset_id = str(row["asset_id"])
        path = asset_root / str(row["source_ref"])
        payload = path.read_bytes()
        if len(payload) != row["bytes"] or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"Lesson08 authority figure differs: {asset_id}")
        nodes = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson08 figure identity differs: {asset_id}")
        image = nodes[0]
        if (
            image.get("src") != row["source_ref"]
            or image.get("alt") != row["source_alt"]
            or image.get("style") != "width:70.0%"
        ):
            raise RuntimeError(f"Lesson08 figure source surface differs: {asset_id}")
        source = str(image)
        image["alt"] = str(row["target_alt"])
        image["style"] = target_style
        parent = image.parent
        if not isinstance(parent, Tag) or parent.name != "p":
            raise RuntimeError(f"Lesson08 figure parent differs: {asset_id}")
        parent["style"] = "text-align:center"
        target = str(image)
        surfaces.append(
            {
                "surface": "figure-accessibility-layout",
                "asset_id": asset_id,
                "unit_id": image.get("data-o006-id"),
                "authority_path": path.relative_to(ROOT).as_posix(),
                "authority_bytes": len(payload),
                "authority_asset_sha256": row["sha256"],
                "authority_asset_unchanged": True,
                "source_surface_sha256": sha256(source.encode("utf-8")),
                "target_surface_sha256": sha256(target.encode("utf-8")),
            }
        )
    return surfaces


def record(
    defect_number: int, surfaces: list[dict[str, object]], note: str
) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson08 defect has no target evidence: D{defect_number:03d}")
    return {
        "correction_id": correction_id(defect_number),
        "source_defect_id": f"L08-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


FIT_T_Y = """## fungsi negatif log-kemungkinan dengan df dibatasi positif
nll.t=function(df,y){
  if(length(df)!=1L || !is.finite(df) || df<=0) return(Inf)
  value=-sum(dt(y,df=df,log=TRUE))
  if(is.finite(value)) value else Inf
}
## MLE numerik berbatas; simpan dan periksa diagnostik pengoptimal
out=optim(4,fn=nll.t,y=y,method="L-BFGS-B",
          lower=sqrt(.Machine$double.eps),hessian=TRUE)
if(out$convergence!=0L || !is.finite(out$value) ||
   any(!is.finite(out$par))) stop("Pendugaan MLE t gagal")
df.hat=unname(out$par)
df.hat"""

FIT_T_X = FIT_T_Y.replace("y=y,method", "y=x,method")

OBSERVED_INFORMATION = """## informasi teramati: Hessian negatif log-kemungkinan pada nilai dugaan
J.n=drop(out$hessian)
if(length(J.n)!=1L || !is.finite(J.n) || J.n<=0)
  stop("Informasi teramati tidak positif dan berhingga")
## selang Wald asimtotik dengan informasi teramati plug-in
c(df.hat-1.96*sqrt(1/J.n),df.hat+1.96*sqrt(1/J.n))"""

PARAMETRIC_SIMULATION = """## protokol RNG eksplisit untuk eksekusi turunan
RNGversion("4.3.0")
RNGkind("Mersenne-Twister","Inversion","Rejection")
set.seed(4150801)
n=length(x)
M=1000L
sim.data=replicate(M,rt(n,df=df.hat),simplify=FALSE)"""

NONPARAMETRIC_SIMULATION = """## protokol RNG eksplisit untuk eksekusi turunan
RNGversion("4.3.0")
RNGkind("Mersenne-Twister","Inversion","Rejection")
set.seed(4150802)
n=length(x)
M=1000L
sim.data=replicate(M,sample(x,size=n,replace=TRUE),simplify=FALSE)"""

BOOTSTRAP_T_FITS = """## simpan nilai dugaan dan diagnostik untuk tepat M replikasi
theta.hat.vals=rep(NA_real_,M)
convergence=rep(NA_integer_,M)
for(m in seq_len(M)){
  out.sim=tryCatch(
    optim(df.hat,nll.t,y=sim.data[[m]],method="L-BFGS-B",
          lower=sqrt(.Machine$double.eps)),
    error=function(e) NULL
  )
  if(is.null(out.sim)) next
  convergence[m]=out.sim$convergence
  if(out.sim$convergence==0L && is.finite(out.sim$value) &&
     all(is.finite(out.sim$par))) theta.hat.vals[m]=out.sim$par
}
failed=is.na(convergence) | convergence!=0L | !is.finite(theta.hat.vals)
if(any(failed)) stop(sprintf("%d pendugaan bootstrap gagal",sum(failed)))
sessionInfo()"""

PARAMETRIC_TEMPLATE = """## baca data
x=c(1,2,3)

## (1) tentukan MLE; ganti ... dan batas dengan spesifikasi model
nll=function(theta,x){
  ## kode negatif log-kemungkinan model ditempatkan di sini
}
out=optim(...,nll,x=x,method="L-BFGS-B",lower=...,upper=...)
if(out$convergence!=0L || !is.finite(out$value) ||
   any(!is.finite(out$par))) stop("Pendugaan data asli gagal")
theta.hat=out$par
## siapkan bootstrap yang dapat direproduksi
RNGversion("4.3.0")
RNGkind("Mersenne-Twister","Inversion","Rejection")
set.seed(4150803)
M=1000L
n=length(x)
sim.data=vector("list",M)
theta.hat.vals=rep(NA_real_,M)
convergence=rep(NA_integer_,M)

for(m in seq_len(M)){
  ## (2) ganti rexp(...) dengan pembangkitan dari model yang dipasang
  sim.data[[m]]=rexp(n,theta.hat)
  ## (3) pasang model yang sama pada data bootstrap
  out.sim=tryCatch(
    optim(...,nll,x=sim.data[[m]],method="L-BFGS-B",lower=...,upper=...),
    error=function(e) NULL
  )
  if(is.null(out.sim)) next
  convergence[m]=out.sim$convergence
  if(out.sim$convergence==0L && is.finite(out.sim$value) &&
     all(is.finite(out.sim$par))) theta.hat.vals[m]=out.sim$par
}
failed=is.na(convergence) | convergence!=0L | !is.finite(theta.hat.vals)
if(any(failed)) stop(sprintf("%d pendugaan bootstrap gagal",sum(failed)))
quantile(theta.hat.vals,c(.025,.975))
sessionInfo()"""

NONPARAMETRIC_TEMPLATE = PARAMETRIC_TEMPLATE.replace(
    "set.seed(4150803)", "set.seed(4150804)"
).replace(
    "## (2) ganti rexp(...) dengan pembangkitan dari model yang dipasang\n"
    "  sim.data[[m]]=rexp(n,theta.hat)",
    "## (2) resampel dari distribusi empiris\n"
    "  sim.data[[m]]=sample(x,size=n,replace=TRUE)",
)

PARETO_BOOTSTRAP = """## MLE analitik Pareto-I; domain dan kegagalan diperiksa eksplisit
pareto.mle=function(z){
  if(!length(z) || any(!is.finite(z)) || any(z<=0))
    stop("Data Pareto harus positif dan berhingga")
  L.hat=min(z)
  denominator=sum(log(z/L.hat))
  if(!is.finite(denominator) || denominator<=0)
    stop("Pendugaan bentuk Pareto gagal")
  a.hat=length(z)/denominator
  if(!is.finite(a.hat) || a.hat<=0) stop("Pendugaan bentuk Pareto gagal")
  c(L=L.hat,a=a.hat)
}
theta.hat=pareto.mle(x)
L.hat=unname(theta.hat["L"])
a.hat=unname(theta.hat["a"])

RNGversion("4.3.0")
RNGkind("Mersenne-Twister","Inversion","Rejection")
set.seed(4150805)
M=1000L
n=length(x)
L.hat.vals=rep(NA_real_,M)
a.hat.vals=rep(NA_real_,M)
for(m in seq_len(M)){
  sim.data=sample(x,size=n,replace=TRUE)
  fit=tryCatch(pareto.mle(sim.data),error=function(e) NULL)
  if(is.null(fit)) next
  L.hat.vals[m]=fit["L"]
  a.hat.vals[m]=fit["a"]
}
failed=!is.finite(L.hat.vals) | !is.finite(a.hat.vals)
if(any(failed)) stop(sprintf("%d pendugaan bootstrap gagal",sum(failed)))

## Hanya kontraexample: kuantil ini bukan selang kepercayaan sah untuk L
quantile(L.hat.vals,c(.025,.975))
sessionInfo()"""


def apply_lesson08_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    finding_ids = re.findall(
        r"^## (L08-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE
    )
    expected_findings = [f"L08-D{i:03d}" for i in range(1, 18)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson08 admitted finding sequence differs: {finding_ids}")

    prose = replace_segment_targets(
        main,
        rows,
        [
            (
                "S0059",
                ", peroleh nilai dugaan ",
                ", dugalah parameter tersebut dengan penduga ",
            ),
            ("S0101", ", kita menduga parameter ", ", kita memperoleh nilai dugaan "),
            ("S0153", ", kita menduga parameter ", ", kita memperoleh nilai dugaan "),
            (
                "S0211",
                "Selang kepercayaan bootstrap nonparametrik 95% bagi parameter lokasi, ",
                "Kuantil persentil bootstrap nonparametrik bagi parameter lokasi, ",
            ),
            (
                "S0212",
                ", adalah (5.06, 5.28). Selang kepercayaan bootstrap nonparametrik 95% bagi parameter bentuk, ",
                ", adalah (5.06, 5.28); bagi lokasi Pareto angka ini adalah kontracontoh "
                "kegagalan, bukan selang kepercayaan 95%. Kuantil persentil bootstrap "
                "nonparametrik bagi parameter bentuk, ",
            ),
            (
                "S0213",
                ", adalah (1.2912, 2.2905).",
                ", adalah (1.277910, 2.270643), sesuai dengan keluaran tetap yang ditampilkan.",
            ),
            (
                "S0223",
                " dengan pendugaan kemungkinan maksimum, maka kita mengetahui bahwa distribusi asimtotik MLE ",
                " dengan pendugaan kemungkinan maksimum, maka—di bawah konsistensi, "
                "identifiabilitas, parameter benar yang interior, diferensiabilitas, "
                "pertukaran turunan dan integral yang sah, serta informasi tak singular—"
                "distribusi limit MLE ",
            ),
            (
                "S0226",
                " merupakan “informasi Fisher”, yang didefinisikan sebagai ",
                " merupakan informasi Fisher harapan untuk sampel, yang didefinisikan sebagai ",
            ),
            (
                "S0230",
                " merupakan fungsi yang dapat dibalik, maka pendekatan umum untuk inferensi adalah apa yang disebut ‘metode delta’. Metode ini bertumpu pada distribusi Gaussian asimtotik MLE serta hasil baku transformasi peubah untuk memperoleh hampiran Gaussian bagi distribusi MLE dari parameter yang ditransformasi ",
                " terdiferensialkan pada parameter benar—tanpa perlu dapat dibalik—maka "
                "pendekatan umum untuk inferensi adalah metode delta. Metode ini memakai "
                "distribusi limit Gaussian MLE untuk memperoleh hampiran bagi distribusi "
                "penduga parameter yang ditransformasi ",
            ),
            (
                "S0247",
                "Pendekatan bootstrap tidak memberlakukan batasan apa pun pada fungsi ",
                "Menerapkan transformasi pada setiap replikasi bootstrap tidak menuntut fungsi ",
            ),
            (
                "S0248",
                ", sedangkan pendekatan metode delta mensyaratkan ",
                " dapat dibalik. Namun, keabsahan inferensi bootstrap tetap bergantung "
                "pada statistik, transformasi, skema resampling, desain sampel, dan syarat "
                "keteraturan; bootstrap parametrik juga mengasumsikan keluarga distribusi "
                "yang dipasang. Untuk metode delta orde pertama, ",
            ),
            (
                "S0249",
                " merupakan fungsi yang dapat dibalik.",
                " harus terdiferensialkan pada parameter benar.",
            ),
            (
                "S0271",
                " merupakan informasi Fisher teramati.",
                " merupakan informasi teramati pada nilai dugaan; besaran ini berbeda "
                "dari informasi Fisher harapan.",
            ),
            (
                "S0290",
                "Kita juga telah mempelajari cara menerapkan metode bootstrap parametrik dan nonparametrik untuk menghasilkan selang kepercayaan dari data, sebagaimana diperagakan dengan himpunan data berdistribusi t dan Pareto. Dengan demikian, kita dapat melakukan inferensi yang andal tanpa asumsi distribusional yang ketat.",
                "Kita juga mempelajari bootstrap parametrik dan nonparametrik untuk membentuk "
                "selang hampiran. Bootstrap parametrik mengasumsikan keluarga distribusi "
                "yang dipasang; bootstrap nonparametrik tetap memerlukan desain sampling "
                "dan syarat keteraturan yang sesuai. Karena itu, keandalannya harus "
                "dievaluasi untuk statistik dan masalah yang sedang dipelajari.",
            ),
            (
                "S0291",
                "Ke depan, teknik selang kepercayaan bootstrap yang telah kita kuasai akan sangat berguna untuk menangani himpunan data dunia nyata dengan distribusi nonbaku atau ukuran sampel kecil, sehingga Anda mampu mengambil keputusan berbasis data dalam analisis statistik mendatang.",
                "Teknik bootstrap berguna untuk data dunia nyata, tetapi sampel kecil, "
                "batas parameter, statistik takmulus, dan identifikasi lemah memerlukan "
                "pemeriksaan validitas khusus sebelum hasil dipakai untuk keputusan.",
            ),
        ],
    )

    code_u0067 = replace_unit_text_by_hash(
        main, "U0067",
        "bb8fc17e8aea95d74bdaebe372194b7537752c11fbde2b39df650272366c6e47",
        FIT_T_Y,
    )
    code_u0088 = replace_unit_text_by_hash(
        main, "U0088",
        "f48f481b93e93f17d6674a8b9afb85ceb5c268d808552e799071e83d88b045e5",
        OBSERVED_INFORMATION,
    )
    code_u0151 = replace_unit_text_by_hash(
        main, "U0151",
        "01b3a0a9ab00937b3614d2cca818cef1181f1e687b64e5ecc6b5ca03bb2b2343",
        FIT_T_X,
    )
    code_u0173 = replace_unit_text_by_hash(
        main, "U0173",
        "17e2749d235482464873abcd180a842c1b700a69214b27541d7269f1d5c1fab1",
        PARAMETRIC_SIMULATION,
    )
    code_u0194 = replace_unit_text_by_hash(
        main, "U0194",
        "b7a9119061f416acbd131d7df5e5bf44afd8c4ec3dde3470d056e09fdd8fd5fe",
        BOOTSTRAP_T_FITS,
    )
    code_u0272 = replace_unit_text_by_hash(
        main, "U0272",
        "e9854dcf860aad6851dc3a8b8fa92bf0977b74e8e69387a3acd3e0bf300fb0ec",
        FIT_T_X,
    )
    code_u0296 = replace_unit_text_by_hash(
        main, "U0296",
        "21fbc1788f6df927871a7e76697008d13bb6da3e65bea9a3adc09557ef7454dc",
        NONPARAMETRIC_SIMULATION,
    )
    code_u0317 = replace_unit_text_by_hash(
        main, "U0317",
        "b7a9119061f416acbd131d7df5e5bf44afd8c4ec3dde3470d056e09fdd8fd5fe",
        BOOTSTRAP_T_FITS,
    )
    code_u0390 = replace_unit_text_by_hash(
        main, "U0390",
        "148293c748ded2ac2f5f03a851789eefd7c51da96a32e649879bb5a4aba813f8",
        PARAMETRIC_TEMPLATE,
    )
    code_u0435 = replace_unit_text_by_hash(
        main, "U0435",
        "57ae462cd272edf5e643af69bafea6d53743fdb1338cd28582c86182f577fb89",
        NONPARAMETRIC_TEMPLATE,
    )
    code_u0501 = replace_unit_text_by_hash(
        main, "U0501",
        "33644b02ebea89858eaa744a79a2bb909866ff6a506f223f25d025e8ebf80b11",
        PARETO_BOOTSTRAP,
    )

    m0004 = apply_math(
        main, "M0004",
        "c66db240d599cf538d74e7e7125fa755099683e953ffdda12f58f3828e064e0d",
        r"\(M\)",
    )
    m0006 = apply_math(
        main, "M0006",
        "caed5ea613942a234ba9d1f191adca143b86192819f22607086714008a986e12",
        r"\(\hat{\theta}^{(m)}\)",
    )
    m0007 = apply_math(
        main, "M0007",
        "58d40436ffa199b7786763b40bba046a490fe9412edd10108dec8c614c9e93fd",
        r"\(m=1,\ldots,M\)",
    )
    m0035 = apply_math(
        main, "M0035",
        "086c287906d419b47d4f0dddcfaf96a8c67e9bb88fd9ba26de05306a9c1272fb",
        r"\(\{\hat{\theta}^{(m)}\}_{m=1}^{M}\)",
    )
    m0068 = apply_math(
        main, "M0068",
        "086c287906d419b47d4f0dddcfaf96a8c67e9bb88fd9ba26de05306a9c1272fb",
        r"\(\{\hat{\theta}^{(m)}\}_{m=1}^{M}\)",
    )
    m0096 = apply_math(
        main, "M0096",
        "086c287906d419b47d4f0dddcfaf96a8c67e9bb88fd9ba26de05306a9c1272fb",
        r"\(\{\hat{\theta}^{(m)}\}_{m=1}^{M}\)",
    )
    m0053 = apply_math(
        main, "M0053",
        "de450f60a0e79e54719bc9c45c6d4fbb554bf6bbe84070150b8780a7cca494c6",
        r"\[\text{SK }95\%\text{ untuk }\theta\approx\left(\hat q_{.025}"
        r"\{\hat\theta^{(1)},\ldots,\hat\theta^{(M)}\},\ \hat q_{.975}"
        r"\{\hat\theta^{(1)},\ldots,\hat\theta^{(M)}\}\right)\]",
    )
    m0084 = apply_math(
        main, "M0084",
        "667fd319191157097511ba785e0d5f647f1baa38c3248d405b78e431643f09e4",
        r"\[P_n(X=x)=\frac{1}{n}\sum_{i=1}^{n}\mathbf{1}\{x_i=x\}\]",
    )
    m0076 = apply_math(
        main, "M0076",
        "baffd7e1776a73e2f1c541a3cbb53120dc41baef4ea223f1ef735763244a0e94",
        r"\((2.612500,\ 1.342177\times10^7)\)",
    )
    m0104 = apply_math(
        main, "M0104",
        "63f6393ef9ee83147f4fda1a184120d42870b331336899c74ba52fcc049ff34c",
        r"\((3.339766,\ 6.710887\times10^6)\)",
    )
    m0120 = apply_math(
        main, "M0120",
        "9ebaa7659a6378af9f445688031aaa82a49d4db3b24f93d22bc6e53063a1320e",
        r"\(I_n(\theta)\)",
    )
    m0121 = apply_math(
        main, "M0121",
        "a9d9948188c6a96568ed045d4b884127071cc12ac5c1c6704ba2afd56240eb92",
        r"\[I_n(\theta)=-\operatorname{E}_{\theta}\!\left[\ell_n''(\theta;X)\right]\]",
    )
    m0149 = apply_math(
        main, "M0149",
        "56d38b8a3db3360d4a2effebea3eb7cea27efb4a906c1f6dd08174f1e210beb6",
        r"\[\hat{\theta}_n\pm z_{\alpha/2}\frac{1}{\sqrt{J_n(\hat{\theta}_n)}}\]",
    )
    m0150 = apply_math(
        main, "M0150",
        "dbe4a51e6f485a26f88802b32e07edebd9871e83dcfc991a448cd236e2501d2c",
        r"\(J_n(\hat{\theta}_n)\)",
    )
    m0119 = apply_math(
        main, "M0119",
        "6ded6348bb13b9bc2f6e40ea13b87558f9ad34b29840b625138ed0c21b6bbbc1",
        r"\[\sqrt{n}(\hat{\theta}_n-\theta_0)\xrightarrow{d}"
        r"N\!\left(0,I_1(\theta_0)^{-1}\right)\]",
    )
    m0127 = apply_math(
        main, "M0127",
        "6aa3aab202ab5f5381d600c0e856544e974cda5e139cf502aa89be7f138bf18e",
        r"\[\sqrt{n}\{g(\hat{\theta}_n)-g(\theta_0)\}\xrightarrow{d}"
        r"N\!\left(0,[g'(\theta_0)]^2I_1(\theta_0)^{-1}\right)\]",
    )
    m0129 = apply_math(
        main, "M0129",
        "5c8a7d50635d79429b1456bc8827fdce28402b5f123f69811d72365f72fec18c",
        r"\[g(\hat{\theta}_n)\pm1.96"
        r"\frac{|g'(\hat{\theta}_n)|}{\sqrt{J_n(\hat{\theta}_n)}}\]",
    )
    m0110 = apply_math(
        main, "M0110",
        "ae12545079af363eb4d9afd3cf18508f63bd18b94bb279eff34ef202c962525c",
        r"\(x_i\in[L,\infty)\)",
    )

    output_notes = [
        insert_output_snapshot_note(
            main, "U0238",
            "d33c265dac56d1277941604369f07070e3d1f3cd8ade23e0c0c66652ec8fd633",
            1,
            "Catatan reproduktibilitas: angka dan histogram di atas adalah cuplikan "
            "sumber hulu tanpa seed, versi RNG, atau rekaman lingkungan. Kode turunan "
            "menetapkan RNG R 4.3.0, seed 4150801, pemeriksaan kegagalan, dan "
            "sessionInfo(); cuplikan dipertahankan sebagai ilustrasi, bukan diklaim "
            "sebagai keluaran verifikasi protokol turunan. Teks interval diselaraskan "
            "dengan cuplikan yang tampil.",
        ),
        insert_output_snapshot_note(
            main, "U0361",
            "159ba7295d0d288b9be408334fc2dffd5a1afe61fcd733285a2b6c290c479f5f",
            2,
            "Catatan reproduktibilitas: angka dan histogram di atas adalah cuplikan "
            "sumber hulu tanpa seed, versi RNG, atau rekaman lingkungan. Kode turunan "
            "menetapkan RNG R 4.3.0, seed 4150802, pemeriksaan kegagalan, dan "
            "sessionInfo(); cuplikan dipertahankan sebagai ilustrasi, bukan diklaim "
            "sebagai keluaran verifikasi protokol turunan. Teks interval diselaraskan "
            "dengan cuplikan yang tampil.",
        ),
        insert_output_snapshot_note(
            main, "U0546",
            "c7ce1ff3e36d4621f9899a2c2a9c606d270bb4618dbe1825cdd8756f1503db15",
            3,
            "Catatan reproduktibilitas: keluaran Pareto ini adalah cuplikan sumber "
            "hulu tanpa keadaan RNG. Kode turunan menetapkan RNG R 4.3.0, seed "
            "4150805, MLE analitik dengan pemeriksaan domain, dan sessionInfo(); "
            "cuplikan tidak diklaim sebagai keluaran verifikasi protokol turunan. "
            "Angka bentuk pada teks diselaraskan dengan snapshot, sedangkan kuantil "
            "lokasi dipertahankan hanya sebagai kontracontoh.",
        ),
    ]

    regularity_note = insert_note_after(
        main, "U0555", 10,
        "Syarat koreksi: hasil limit ini memerlukan model terdominasi dan dapat "
        "diidentifikasi, parameter benar yang interior, konsistensi, diferensiabilitas "
        "dan pertukaran integral-turunan yang sah, serta informasi Fisher yang positif "
        "dan taksingular. I₁ adalah informasi harapan per pengamatan; Jₙ pada nilai "
        "dugaan hanya merupakan besaran plug-in untuk galat baku, bukan varians acak "
        "dalam hukum limit.",
    )
    delta_note = insert_note_after(
        main, "U0556", 11,
        "Metode delta orde pertama hanya memerlukan g terdiferensialkan pada parameter "
        "benar. Turunan dalam varians limit dievaluasi pada nilai benar; turunan pada "
        "nilai dugaan dipakai hanya sebagai plug-in. Jika turunannya nol, limit orde "
        "pertama degenerat dan metode orde lebih tinggi mungkin diperlukan.",
    )
    bootstrap_scope_note = insert_note_after(
        main, "U0603", 12,
        "Koreksi cakupan: bootstrap bukan prosedur bebas-asumsi. Keabsahannya "
        "bergantung pada statistik, transformasi, skema resampling, desain sampel, dan "
        "keteraturan; bootstrap parametrik secara khusus mengasumsikan keluarga "
        "distribusi yang dipasang.",
    )
    pareto_note = insert_note_after(
        main, "U0547", 14,
        "Koreksi inferensi titik ujung: (5.06, 5.28) bukan selang kepercayaan 95% "
        "yang sah bagi L. Setiap minimum resampel sedikitnya sebesar minimum teramati "
        "5.06, sedangkan pada model Pareto kontinu minimum sampel melebihi L dengan "
        "peluang satu. Karena itu, selang persentil ini mengecualikan L hampir pasti "
        "dan dipertahankan hanya sebagai kontracontoh; klaim afirmatif memerlukan "
        "metode inferensi titik ujung yang valid.",
    )
    figure_surfaces = repair_figures(main)
    editorial_surfaces = [remove_unit(main, "U0572"), remove_unit(main, "U0598")]

    records = [
        record(
            1,
            [
                m0004, m0006, m0007, m0035, m0068, m0096,
                prose["S0059"], prose["S0101"], prose["S0153"],
            ],
            "distinguish theta, hat-theta, M repetitions, and repetition index m",
        ),
        record(2, [m0053], "remove the unmatched upper-quantile opening brace"),
        record(
            3,
            [m0084, *segment_surfaces(rows, ["S0139", "S0140", "S0141", "S0142"])],
            "assign empirical mass by observed multiplicity divided by n",
        ),
        record(
            4, [code_u0151, code_u0272],
            "fit both restated t examples to local x rather than stale global y",
        ),
        record(
            5, [code_u0390, code_u0435, code_u0501],
            "size every bootstrap result vector by M",
        ),
        record(
            6,
            [
                code_u0067, code_u0151, code_u0194, code_u0272,
                code_u0317, code_u0390, code_u0435, code_u0501,
            ],
            "enforce valid domains, retain diagnostics, and fail on bad fits",
        ),
        record(
            7,
            [
                code_u0173, code_u0194, code_u0296, code_u0317,
                code_u0390, code_u0435, code_u0501, *output_notes,
            ],
            "add explicit RNG/environment protocols and label unseeded source snapshots",
        ),
        record(
            8, [m0076, m0104, prose["S0213"], *output_notes],
            "align prose intervals with fixed outputs and disclose snapshot status",
        ),
        record(
            9,
            [
                code_u0088, m0120, m0121, m0149, m0150,
                prose["S0226"], prose["S0271"],
            ],
            "separate expected Fisher information I_n from observed information J_n",
        ),
        record(
            10, [m0119, prose["S0223"], regularity_note],
            "state MLE normality as a convergence theorem with actual conditions",
        ),
        record(
            11, [m0127, m0129, prose["S0230"], delta_note],
            "require differentiability, use the derivative at theta_0 in the limit, "
            "and label plug-in quantities",
        ),
        record(
            12,
            [
                prose["S0247"], prose["S0248"], prose["S0249"],
                prose["S0290"], prose["S0291"], bootstrap_scope_note,
            ],
            "replace unconditional bootstrap claims with problem-dependent validity",
        ),
        record(13, [m0110], "include L in the implemented Pareto support"),
        record(
            14, [code_u0501, prose["S0211"], prose["S0212"], pareto_note],
            "retain the Pareto endpoint percentile result only as a counterexample",
        ),
        record(
            15, figure_surfaces,
            "supply full Indonesian alternatives and use centered reader width "
            "without changing authority PNG bytes",
        ),
        record(
            16,
            [
                *editorial_surfaces,
                *segment_surfaces(rows, ["S0258", "S0289"]),
            ],
            "remove internal authoring notes while retaining substantive summaries",
        ),
        record(
            17,
            [
                m0004, m0006, m0007, m0035, m0068, m0096,
                code_u0390, code_u0435,
                *segment_surfaces(
                    rows,
                    [
                        "S0022", "S0023", "S0025", "S0026", "S0065", "S0136",
                        "S0182", "S0183", "S0184", "S0185", "S0186", "S0187",
                        "S0188", "S0189", "S0190", "S0191", "S0192", "S0193",
                        "S0194", "S0195", "S0196", "S0197", "S0198", "S0241",
                        "S0245",
                    ],
                ),
            ],
            "repair indexing, agreement, capitalization, template lists, optim "
            "spelling, the Section 8.1 reference, and plural quantiles",
        ),
    ]

    expected_correction_ids = [
        f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(135, 152)
    ]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson08 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson08 correction/finding binding differs")
    if len({str(row["correction_id"]) for row in records}) != len(records):
        raise RuntimeError("Lesson08 correction identities are not unique")
    return records
