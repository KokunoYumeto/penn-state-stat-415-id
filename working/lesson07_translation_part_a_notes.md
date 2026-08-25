# Lesson 07 translation part A — decisions and deferred corrections

Scope: exactly `O006-PSU-008-S0001` through
`O006-PSU-008-S0080`, in source order.

Authority and ledger:

- `authority/upstream/stat415/Lesson07.html`: 105,026 bytes; SHA-256
  `2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c`
- `working/lesson07_segments.csv`: SHA-256
  `1d7f6cb87bb3faedfabeb66709ceca6cea1c33a818f2e30708c30ebeb908c1e3`
- assigned source-hash binding digest: SHA-256
  `ced90d17daea5efd64063c9f038e7a445394147a5e59f27b9c4c6c7ffdd48a21`
  over the 80 UTF-8 lines `segment_id<TAB>source_sha256<LF>`
- protected source formula SHA-256:
  `c2da24f78e6d812d1bd5245e5cb671b52c1f3c5053de56e8141d13512fa36bb3`

## Translation decisions

- Applied the controlling glossary distinctions **penduga** versus **nilai
  dugaan**, **fungsi kemungkinan**, **fungsi log-kemungkinan**, **selang
  kepercayaan**, **simpangan baku**, **varians**, and **himpunan dukungan**.
- Used **distribusi asimtotik**, **normalitas asimtotik**, **sifat
  ekuivarian**, **syarat keteraturan**, and **informasi Fisher** in accordance
  with `working/lesson07_terminology_qa.md`.
- Retained `MLE`, `iid`, `R`, `optim`, distribution names, mathematical
  symbols, and all protected formula/code boundaries. No formula or code text
  occurs inside this target JSON.
- Expanded `iid` once as **saling bebas dan berdistribusi identik (iid)** and
  then used **sampel iid**.
- Rendered `odds ratio` as **rasio odds**; its protected `OR` notation remains
  outside the translated text node.
- Preserved uppercase emphasis in `S0015` as **SETIAP MLE!** and the trailing
  newlines in `S0024`, `S0033`, and `S0064`.
- Preserved the source's explicit limitation at `S0021`: the full list of MLE
  regularity conditions and their proofs is not supplied, and the reader is
  referred to Wasserman, Chapter 9.13. The translation does not manufacture
  omitted hypotheses or proofs.

## Registered corrections deliberately not folded into substantive claims

The translation JSON is a source-faithful language layer. The following
findings remain explicit downstream correction obligations rather than hidden
changes to the source's mathematical assertions.

### `L07-D008` — stale overview scope (`S0009`–`S0010`)

The claims that Lesson07 teaches parametric/nonparametric bootstrap methods,
the Delta method, and t/Pareto examples are translated as the source states
them. The correction layer must label them as stale scope or forward-looking
material; those topics are absent from the instructional body.

### `L07-D012` — parameter boundary versus support (`S0019`–`S0020`)

The source wording that the MLE is “not in the support” is translated
faithfully. The correction layer must instead explain that the relevant
regularity condition concerns the true parameter being an interior point of
the parameter space; the support is the set of possible data values.

### `L07-D001` — false expectation corollary (`S0025`–`S0030`)

The target preserves the source's claim that
`E(hat(theta)_mle) -> theta` is a consequence of consistency. It does not
silently insert the proof correction. The correction layer must state that
consistency alone is insufficient and that an additional condition such as
uniform integrability is needed. The counterexample and exact sufficient
condition are recorded in `working/lesson07_math_audit.md`.

### `L07-D002` — expected versus observed information (`M0043`, adjacent to
`S0070`–`S0074`)

The protected formula is outside this JSON and remains byte-identical. The
translated prose retains the source label **informasi Fisher**. The correction
layer must define expected information at the parameter and distinguish it
from the observed Hessian used later; this part does not rewrite `M0043`.

### `L07-D011` — mechanical surfaces in this range

- `S0049`: the nonsensical English `respectfully` was rendered naturally as
  **masing-masing**, the intended equivalent of `respectively`.
- `S0061`: the missing source space in `.Therefore` was rendered as the
  natural Indonesian sentence boundary `. Oleh karena itu`.

These two language-level repairs are disclosed here rather than hidden. Their
source findings remain registered for provenance. The later `L07-D011`
surfaces beginning at `S0089` are outside this part and were not touched.

## Validation contract

- JSON must contain exactly 80 keys and no metadata keys.
- Keys must be the contiguous ordered range `S0001`–`S0080`.
- Every key must bind the frozen `source_sha256` in the segment ledger, and
  every target must be a nonempty string.
- Leading and trailing whitespace, including newlines, must match each source
  segment exactly.
- No shared glossary, control, script, normalized source, backend, Git, prior
  lesson, or publication artifact is modified by this part.
