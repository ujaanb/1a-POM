# Wiki Log

Append-only timeline of wiki operations. Newest entries at the bottom.

Entry header format (mandatory, parseable by `grep "^## \[" wiki/log.md`):
`## [YYYY-MM-DD] <operation> | <short title>`

Allowed operations:
- `ingest` — a raw source was processed into wiki content.
- `query` — an answer was generated from wiki pages.
- `lint` — a health-check pass over wiki structure/content.
- `meta` — schema/index/log/structure maintenance.

---

## [2026-07-18] meta | Instantiate template for Imperial Medicine Year 1

- Filled `AGENTS.md` §1 for Imperial MBBS Year 1 (Phase 1A / POM), primary tag `imperial-med-y1`.
- Defined entity types (anatomical-structure, organ-system, molecule-or-pathway, cell-or-tissue, drug-or-class, disease-or-condition, module-or-block, assessment) and concept guidance.
- Removed TEMPLATE callout; replaced §10 checklist with instantiation status.
- Rewrote `README.md` for this wiki; updated Domain line in `wiki/index.md`.
- Scaffolded empty `raw/{pdfs,web-clips,notes,assets}/` for first ingest.
- Files touched: `AGENTS.md`, `README.md`, `wiki/index.md`, `wiki/log.md`, `raw/`.

## [2026-07-18] meta | POM Study Hub — Cellular Biology notes

- Built `site/` matching the BRS Study Hub UI (shared CSS, topic tiles, lecture cards, Q&A note layout).
- Generated notes for all 16 Cellular Biology lectures from `raw/pdfs/Cellular Biology/*.pdf` (~678 Q&A prompts).
- Topic stubs for Haematology, Immunity, Genetics (coming soon).
- No Anki decks (per request).
- Files touched: `site/index.html`, `site/css/styles.css`, `site/topics/cellular-biology/*`, `site/topics/{haematology,immunity,genetics}/index.html`, `site/_extracted/cellular-biology/*`, `README.md`, `wiki/log.md`.

## [2026-07-18] meta | POM Study Hub — Haematology notes

- Generated Q&A notes for all 10 Haematology lectures from `raw/pdfs/Haematology/*.pdf` (~462 revision prompts).
- Lectures: 3.1–3.10 (RBCs, Hb methods, RBC parameters, clinic I/II, WBCs, blood film, haemostasis, transfusion, plasma).
- Updated home tile badge; Immunity and Genetics remain stubs.
- Files touched: `site/topics/haematology/*`, `site/_extracted/haematology/*`, `site/index.html`, `README.md`, `wiki/log.md`.
