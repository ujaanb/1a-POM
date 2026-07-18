# Imperial Medicine Year 1 Wiki

Personal LLM-maintained knowledge base for **Imperial College London MBBS Year 1** (Phase 1A), starting with the Principles of Medicine (POM) block.

You drop lecture slides, notes, and clips into `raw/`. The agent reads them, builds structured wiki pages, and keeps cross-references current. You steer and revise; the agent does the bookkeeping.

Pattern reference: [`docs/LLM-WIKI.md`](./docs/LLM-WIKI.md). Operating contract: [`AGENTS.md`](./AGENTS.md).

---

## Study hub (notes site)

Same UI as the [BRS Study Hub](https://ujaanb.github.io/1b-BRS/): open [`site/index.html`](./site/index.html) in a browser, or from `site/`:

```bash
python3 -m http.server 8765
```

Then visit http://127.0.0.1:8765 — **Cellular Biology** (16 lectures) and **Haematology** (10 lectures) are ready. Immunity and Genetics are stubs until their PDFs are processed.

---

## Quick start

1. Put lecture PDFs in `raw/pdfs/<Topic>/`.
2. Ask for notes pages (study hub) and/or *"Ingest this source"* (wiki).
3. Browse notes in `site/`; ask wiki questions anytime for synthesis.

Catalog: [`wiki/index.md`](./wiki/index.md). History: [`wiki/log.md`](./wiki/log.md).

---

## Layout

```
.
├── AGENTS.md           # schema — auto-loaded by Cursor
├── README.md           # this file
├── docs/
│   └── LLM-WIKI.md     # pattern doc (do not modify)
├── raw/                # immutable sources (you add files here)
│   └── pdfs/           # Cellular Biology, Haematology, Immunity, Genetics
├── site/               # HTML study hub (BRS-style notes UI)
└── wiki/               # LLM-owned knowledge pages
```

---

## Domain snapshot

| | |
|---|---|
| **Subject** | Imperial MBBS Year 1 / Phase 1A medicine notes |
| **Primary tag** | `imperial-med-y1` |
| **Entities** | anatomical structures, systems, pathways, cells, drugs, diseases, modules, assessments |
| **Concepts** | mechanisms, presentations, processes, learning frameworks, exam themes |
| **Out of scope** | Later clinical years unless clarifying Year 1; admin trivia; conflicting non-Imperial curricula without marking |

---

## Workflows

- **Ingest** — process one new `raw/` source into source + entity/concept updates.
- **Query** — answer from wiki pages with citations; optionally file lasting answers as analyses.
- **Lint** — health-check orphans, dead links, stale claims, missing pages.
- **Meta** — schema/structure changes.

Details in [`AGENTS.md`](./AGENTS.md) §5.
