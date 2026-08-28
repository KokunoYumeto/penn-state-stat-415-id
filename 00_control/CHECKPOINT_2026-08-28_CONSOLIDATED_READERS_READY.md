# Checkpoint - consolidated readers release-ready

Date: 2026-08-28

The complete fourteen-document Penn State STAT 415 Indonesian component has
two final reader surfaces ready for publication in the existing lineages.

- PDF: 219 A4 pages / 20,170,549 bytes / SHA-256
  `f39c1c438cc3e793fe9522eb11f5b02704d89fcdc7aecb2207a599087d458964`.
- EPUB: 12,301,415 bytes / SHA-256
  `e122d65348971b91a5ac0c7a8219e0fa3e0eabedb92d130c661648e399e3c574`.
- EPUB structure: 111 entries, 107 manifest items, four spine items, 3,159
  MathML nodes, 17 SVG fallbacks, and 125 stable-ID focusable width-risk
  formulas.
- Release union: 17 files / 87,848,426 bytes; package receipt 14,830 bytes /
  SHA-256
  `934f9484dd7fd25a2436c80914c68d9627ba4009da07900a975e168d91d01694`.
- All nine files from Zenodo record `22105616` remain present with exact prior
  byte and SHA-256 identities.

Deterministic checks passing at this cursor:

1. consolidated source normalization `--check-only`;
2. PDF structural audit and byte-identical replay;
3. PDF all-page visual-receipt `--check-only`;
4. EPUB official plus two byte-identical replays;
5. EPUBCheck 5.3.0 with zero messages;
6. final EPUB static/package and reflow-delta audits `--check-only`; and
7. full-union release package and both publication adapters in local-preflight
   mode.

No Chrome, Chromium, Playwright, Puppeteer, Ace, Electron, WebView, or other
browser process may be launched by this lane. The final EPUB receipts disclose
that the earlier Ace pass applies only to its named prior candidate, not the
final hash.

Next action: commit and push the exact source/control/receipt paths; publish
GitHub tag `v2026.08.28.14of14-pdf-epub`; publish Zenodo version
`2026.08.28.14of14-pdf-epub` by creating a new version from record `22105616`;
anonymously download and hash all 17 files from each destination; persist
sanitized receipts and the new Zenodo lineage pointer; then start the distinct
Random completeness donor. Overall C140 remains active through that donor and
the original rigor/simulation/mastery companion.
