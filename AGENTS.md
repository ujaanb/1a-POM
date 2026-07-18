# AGENTS.md — Wiki Schema

This file is the operating contract between the human curator and the LLM agent maintaining this wiki.
It is loaded automatically by Cursor and other agentic tools at the start of every session.
Read it in full before performing any wiki operation. Update it via the `meta` log operation when conventions change.

The pattern this wiki implements is described in [`docs/LLM-WIKI.md`](./docs/LLM-WIKI.md). This file is the project-specific instantiation of that pattern.

---

## 1. Domain

- **Subject:** Imperial College London MBBS Year 1 (Phase 1A) medicine — lecture notes, tutorials, and related study material, starting with the Principles of Medicine (POM) block and expanding across Year 1 modules as sources are ingested.
- **Goal of the wiki:** Build a durable, interlinked knowledge base of Year 1 biomedical and early clinical science for revision, exam prep, and connecting topics across modules (anatomy, physiology, biochemistry, pathology, pharmacology, and professional practice as they appear in Year 1).
- **Out of scope:** Later clinical years (Phase 2/3) specialty content unless it clarifies a Year 1 concept; administrative/logistics detail unrelated to learning (timetable trivia, room bookings); content from other universities' curricula when it conflicts with Imperial teaching without being marked as external comparison. If a source is broader than Year 1, extract only the Year 1–relevant facts; note the rest under the source page's "Out of scope notes".
- **Audience:** the curator (human owner) is the primary reader. Pages should be readable on their own without chat context.
- **Primary tag:** `imperial-med-y1`

### Entity / concept categories (domain guidance)

Use these types consistently when creating pages:

| Kind | Type values / examples | Page location |
|------|------------------------|---------------|
| **Entity** | `anatomical-structure`, `organ-system`, `molecule-or-pathway`, `cell-or-tissue`, `drug-or-class`, `disease-or-condition`, `module-or-block`, `assessment` | `wiki/entities/` |
| **Concept** | mechanisms, clinical presentations, physiological processes, learning frameworks (e.g. SOAP, ABCDE), exam themes | `wiki/concepts/` |
| **Analysis** | topic comparisons, revision maps, gap analyses, "how topics connect" deep dives | `wiki/analyses/` |

Prefer entity pages for named structures, drugs, diseases, and course blocks. Prefer concept pages for processes and themes that span multiple entities (e.g. "Starling forces", "inflammation", "acid–base balance").

---

## 2. Repository layout

```
.
├── AGENTS.md                         # this file — the schema (auto-loaded by Cursor)
├── README.md                         # human-facing project readme for this wiki
├── docs/
│   ├── LLM-WIKI.md                   # the pattern document (do not modify)
│   └── diagrams/                     # PlantUML sources + render script (optional)
├── raw/                              # immutable source documents (created on first ingest)
│   ├── pdfs/                         # lecture PDFs by topic (Cellular Biology, Haematology, Immunity, Genetics)
│   ├── web-clips/                    # markdown clipped from the web
│   ├── notes/                        # transcribed meeting notes, interviews
│   └── assets/                       # images, attachments
├── site/                             # HTML study hub (BRS-style lecture notes UI)
├── wiki/                             # ALL files in here are LLM-owned
│   ├── index.md                      # canonical page catalog
│   ├── log.md                        # append-only chronological record
│   ├── overview.md                   # top-level synthesis (created on first ingest that warrants it)
│   ├── sources/                      # one page per ingested raw source
│   ├── entities/                     # one page per stable entity
│   ├── concepts/                     # one page per stable concept
│   ├── analyses/                     # generated synthesis: comparisons, gap analyses, design proposals
│   └── _archive/                     # deprecated/superseded pages, never referenced from index (created on first supersession)
└── .cursor/                          # editor config (Cursor will populate as needed)
```

### Ownership rules

- `raw/` is **immutable**. Never modify or delete files in `raw/`. If a source needs correction, ingest a new version with a date-suffixed filename and supersede the old source page.
- `wiki/` is **LLM-owned**. The human reads, comments, and steers; the LLM writes every file.
- `docs/` is **human-owned**, except for the schema pattern doc (`docs/LLM-WIKI.md`) which is reference-only.
- `AGENTS.md` is **co-evolved** — the LLM may propose changes via diff but the human approves them.

---

## 3. Page format

Every wiki page (other than `index.md` and `log.md`) starts with YAML frontmatter:

```yaml
---
title: <Human-readable page title>
type: source | entity | concept | analysis | overview
status: draft | active | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:                       # list of relative links to wiki/sources/*.md that back this page (omit for source pages)
  - ../sources/foo.md
aliases: []                    # alternate names that should resolve to this page
tags: [<primary-tag>, ...]     # always include the primary tag from §1; add domain tags as appropriate
---
```

Body sections vary by page `type`:

### 3.1 Source pages (`wiki/sources/<slug>.md`)

```
# <Source Title>

## Metadata
- **Origin:** <URL or local path under raw/>
- **Author / Publisher:** ...
- **Date of source:** ...
- **Date ingested:** YYYY-MM-DD
- **Format:** pdf | web | transcript | image | data
- **Decode confidence:** high | medium | low — <one-line reason>

## Summary
<3–8 sentence neutral summary of what this source says, in your own words.>

## Key facts
- <atomic, citeable fact 1>
- <atomic, citeable fact 2>
- ...

## Quotes (optional)
> <direct quote>
— location/timestamp/page

## In-scope extraction
<What this source contributes specifically to the wiki's domain (per §1). This is the section that downstream entity/concept pages will draw from.>

## Out-of-scope notes
<Bullet list of out-of-scope content present in the source, captured briefly so we don't lose track but kept out of the wiki's main graph.>

## Open questions / contradictions
- <Anything unclear, contradicted by another source, or worth following up.>
```

### 3.2 Entity pages (`wiki/entities/<slug>.md`)

For things with **stable identity** within the domain. Use the entity types listed under §1 (anatomical structures, organ systems, molecules/pathways, cells/tissues, drugs, diseases/conditions, modules/blocks, assessments).

```
# <Entity Name>

## What it is
<One paragraph definition.>

## Properties
- **Type:** <entity-type — anatomical-structure | organ-system | molecule-or-pathway | cell-or-tissue | drug-or-class | disease-or-condition | module-or-block | assessment | …>
- **Owner / Operator:** ...
- **Status in our context:** in-use | proposed | competitor | external | historical | …

## Description
<Multi-paragraph description, organized by sub-headings as needed.>

## Relationships
- Uses: [[concept]], [[entity]]
- Used by: ...
- Related to: ...
- Built on: ...

## Open questions
- ...

## Citations
Every non-trivial claim above must be backed by an inline citation of the form `[^src-slug]` or a parenthetical `(see [foo](../sources/foo.md))`. Collect footnote definitions at the bottom:
[^src-slug]: [Source page](../sources/src-slug.md), §Key facts
```

### 3.3 Concept pages (`wiki/concepts/<slug>.md`)

For **ideas, patterns, practices, themes** within the domain — physiological/pathophysiological processes, clinical presentations, learning frameworks, exam themes — anything that is not a discrete named entity but is referenced repeatedly across sources.

Same structure as entity pages, with `Properties.Type` omitted. Add a `## Variants` section if the concept has multiple flavors worth distinguishing (e.g. types of shock, classes of hypersensitivity).

### 3.4 Analysis pages (`wiki/analyses/<slug>.md`)

For generated synthesis: comparisons, gap analyses, design proposals, recommendations, deep dives. These are the wiki's "outputs" — answers worth keeping.

```
# <Analysis Title>

## Question / brief
<Why this analysis exists. The original question or hypothesis.>

## TL;DR
<3–5 bullet points or a short paragraph with the headline takeaway.>

## Body
<Multi-section analysis with explicit citations to source and entity/concept pages.>

## Confidence and gaps
- High confidence: ...
- Medium: ...
- Low / unknown: ...

## Implications
<What follows from this analysis for the domain (per §1)?>

## Citations
<Footnote-style references as in entity pages.>
```

### 3.5 Overview page (`wiki/overview.md`)

A single living synthesis page maintained from the second ingest onward. Sections:
- `## What we know about <subject from §1>`
- `## Open questions`
- `## Active hypotheses`
- `## Major sources`
- `## Recent shifts in understanding` (last 3–5 ingests)

---

## 4. Conventions

- **Filenames:** `kebab-case.md`, ASCII only. No spaces, no caps.
- **Slugs:** entity/concept slugs are the canonical name lowercased and hyphenated. Aliases live in frontmatter.
- **Links:** always relative markdown links from the page's location. Never absolute paths.
- **Dates:** ISO `YYYY-MM-DD`.
- **Citations:** every claim about the world (not generic background) must cite at least one source page. If a claim is the LLM's inference, mark it explicitly: `(inferred — no direct source)`.
- **Voice:** neutral, factual, concise. No hedging filler ("it should be noted that..."). Prefer short sentences and bulleted lists over prose where possible.
- **One topic per page.** If a page grows past ~400 lines or covers two distinct things, split it and update the index.
- **No silent deletes.** When a page is superseded, move it to `wiki/_archive/<old-slug>.md`, set `status: superseded` in frontmatter, and remove it from `index.md`. The log records the supersession.
- **Domain sync:** Section 1 Domain in `AGENTS.md` is canonical. Whenever Subject or other Domain fields change in a material way, update the **Domain** bullet in `wiki/index.md` so it matches **Subject** (or a short headline explicitly derived from it—same meaning, fewer words). Refresh the domain summary in `README.md` if it exists. Append a `meta` log entry listing files touched.

---

## 5. Workflows

### 5.1 Ingest

When the human drops a source into `raw/` and asks to ingest:

1. **Read** the source in full. For PDFs, prefer text extraction; if extraction is poor, fall back to fetching the original URL or processing images.
2. **Discuss** the key takeaways with the human in chat (3–6 bullets) before writing anything.
3. **Create** `wiki/sources/<slug>.md` per §3.1.
4. **Update entity/concept pages** that this source touches. Each affected page must:
   - Have its `updated:` date bumped.
   - Add a citation to the new source.
   - Add or revise claims as needed; flag contradictions explicitly with a `> ⚠ contradicts <other-source>` callout.
5. **Update `wiki/overview.md`** if this source shifts the high-level synthesis.
6. **Update `wiki/index.md`** with the new source page link and any new entity/concept pages.
7. **Append a log entry** per §6.
8. **Report back** to the human: list of files touched, contradictions flagged, follow-up sources suggested.

A single ingest typically touches 5–15 wiki files. Don't shortcut by only writing the source page.

### 5.2 Query

When the human asks a question:

1. **Read `wiki/index.md` first** to find candidate pages.
2. **Read the candidate pages** (and their cited sources if needed for verification).
3. **Synthesize** an answer with inline citations to wiki pages. Prefer `[entity name](../wiki/entities/foo.md)` style links.
4. **Offer to file the answer** as a new analysis page if it has lasting value. If the human accepts, create `wiki/analyses/<slug>.md` per §3.4, update the index, and log it as a `query` entry that produced an analysis.
5. If the wiki cannot answer the question, say so explicitly and propose what sources to ingest to fix the gap.

### 5.3 Lint

When the human asks for a health check (or proactively, every ~10 ingests):

Scan the wiki for:
- **Orphans:** pages with no inbound links (other than from `index.md`).
- **Dead links:** broken relative paths.
- **Stale claims:** statements that newer sources have superseded but the older page still asserts.
- **Missing pages:** entities or concepts repeatedly mentioned across multiple sources but lacking their own page.
- **Contradictions:** conflicting claims across pages.
- **Citation gaps:** claims without a source citation.
- **Index drift:** pages on disk not listed in `index.md`, or listed pages that don't exist.
- **Overview staleness:** if `wiki/overview.md` hasn't been updated in the last 5 ingests, propose revisions.

Output a lint report as a chat message. Do not make changes silently. The human approves changes before they are applied. Append a `lint` log entry once a lint pass completes (whether or not changes were made).

### 5.4 Meta

For schema/index/log/structure changes that are not ingests, queries, or lints. Always logged with operation `meta`.

---

## 6. Index and log

### 6.1 `wiki/index.md`

- Canonical, hand-maintained-by-the-LLM catalog of every wiki page.
- Sections in this order: `Core`, `Overview`, `Sources`, `Entities`, `Concepts`, `Analyses`, `Archive`.
- Each entry: `- [\`relative/path.md\`](relative/path.md) — one-line summary.`
- Updated on every ingest, query-that-files-an-analysis, lint-that-changes-pages, and meta operation.

### 6.2 `wiki/log.md`

- Append-only. Newest entries at the bottom.
- Entry header format (mandatory, parseable by `grep "^## \[" wiki/log.md`):

  `## [YYYY-MM-DD] <operation> | <short title>`

- Allowed `<operation>` values: `ingest`, `query`, `lint`, `meta`.
- Body: 2–6 bullet points covering what changed and why. Always list the wiki files touched.
- Never edit or delete past entries. To correct, append a new `meta` entry that supersedes the previous one.

---

## 7. Citation and provenance rules

- **Every fact-bearing claim** in entity/concept/analysis/overview pages must have a citation to at least one source page. Source pages cite the raw source.
- **Inferences** are allowed but must be marked: `(inferred from X + Y)`.
- **Quotes** must be exact. If paraphrasing, do not use quote marks.
- **Confidence markers** (`[high]`, `[medium]`, `[low]`) may be appended to claims when the source is partial, contested, or indirect.
- **Never invent sources.** If a claim isn't sourced and you can't infer it cleanly, leave it out and add it to the page's "Open questions" section.

---

## 8. Tooling notes

- **PlantUML:** `docs/diagrams/` is reserved for `.puml` files. The render script (`docs/diagrams/render-diagrams.ps1`) and the `plantuml.jar` binary are gitignored. When a diagram would help an analysis, generate the `.puml` source under `docs/diagrams/` and reference the rendered SVG/PNG from the analysis page.
- **Web clips:** prefer markdown clips into `raw/web-clips/`. If only a URL is provided, fetch it, save the markdown clip into `raw/web-clips/<slug>.md` with a leading frontmatter block recording the URL and fetch date, then ingest from that.
- **Search:** the wiki should remain navigable via `index.md` alone for now. If page count exceeds ~100, revisit and propose a search tool (e.g. `qmd`) via a `meta` log entry.
- **Git:** the wiki is intended to live in a git repo. Don't create commits unless the human explicitly asks.

---

## 9. Boundaries

The agent must:

- ✅ Always read `wiki/index.md` and `wiki/log.md` (last ~10 entries) at the start of any wiki operation.
- ✅ Always update the index and log when wiki content changes.
- ✅ Always cite. Always flag contradictions. Always discuss before writing on first ingest of a session.
- ❌ Never modify files in `raw/`.
- ❌ Never delete a wiki page without archiving it first.
- ❌ Never write a wiki page without YAML frontmatter.
- ❌ Never assert a fact without a citation or an explicit `(inferred)` marker.
- ❌ Never batch-ingest more than one source without explicit human confirmation.

---

## 10. Instantiation status

This wiki was instantiated on 2026-07-18 for Imperial MBBS Year 1 (`imperial-med-y1`). See `wiki/log.md` for the instantiation `meta` entry. Ready for first ingest per §5.1.
