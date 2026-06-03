# wiki/ — LLM-maintained physics knowledge base

This is a compounding, interlinked wiki of **neutrino-nucleus and
electron-nucleus cross-section measurements**. You (the LLM) own this whole
directory: you create and update pages, maintain cross-references, flag
contradictions, and keep the synthesis current as papers are ingested. The
human curates sources and asks questions; you do all the bookkeeping.

Read this file before any wiki operation.

## Three layers

- **Raw (immutable):** `papers/<arxiv_id>/` — produced by the `paper-extractor`
  subagent (tarball, tex, `figures/`, `paper_<arxiv_id>.md`, `keep_proposal.md`).
  You **read** from here; you never edit it. The canonical per-paper extraction
  is `papers/<arxiv_id>/paper_<arxiv_id>.md` — do not duplicate its content into
  the wiki, synthesize *across* papers instead.
- **Wiki (you own):** this `wiki/` tree — synthesis pages that compound across
  papers, plus `index.md` and `log.md`.
- **Schema:** this file.

## Page types (one entity/concept per file)

| Dir | Page = | Examples |
|-----|--------|----------|
| `source/` | thin node per paper (graph anchor + backlinks) | `2106.16210.md` |
| `experiment/` | a collaboration / facility | `minerva.md`, `t2k.md`, `jlab-hall-a.md`, `clas.md` |
| `target/` | a target nucleus | `c12.md`, `ar40.md`, `fe56.md`, `au197.md` |
| `channel/` | an interaction channel / observable | `ccqe.md`, `em-qe.md`, `mec-2p2h.md`, `cc0pi.md` |
| `concept/` | a physics concept or method | `axial-mass.md`, `fsi.md`, `rpa.md`, `unfolding-dagostini.md`, `spectral-function.md` |
| `model/` | a generator / model / tune | `genie-g18.md`, `neut.md`, `gibuu.md`, `susav2.md` |
| `comparison/` | a filed query answer (cross-paper synthesis) | `ma-ccqe-across-experiments.md` |

Slugs are kebab-case. Prefer one canonical page per entity; redirect synonyms
with a one-line stub linking to the canonical page.

## Page conventions

Every page starts with YAML frontmatter (drives Obsidian Dataview):

```yaml
---
title: <human title>
type: source | experiment | target | channel | concept | model | comparison
tags: [<short>, <tags>]
updated: YYYY-MM-DD
# type-specific, when applicable:
arxiv: <id>            # source pages
experiments: [minerva] # which collaborations touch this
targets: [c12, ar40]   # nuclei involved
channels: [ccqe]       # channels involved
sources: [2106.16210]  # arxiv ids this page synthesizes
---
```

Body rules:
- Link entities with Obsidian wikilinks: `[[c12]]`, `[[ccqe]]`, `[[minerva]]`.
  A link to a not-yet-created page is fine — it marks a page to write.
- **Cite every claim** with the arxiv id, e.g. `(2106.16210)`. Numbers must be
  verbatim from `papers/<id>/paper_<id>.md` — never invent or re-round.
- When a new source **contradicts** an existing claim, do not silently
  overwrite: keep both with a `> [!warning] Contradiction` callout naming both
  sources and the discrepancy, and flag it in `log.md`.
- `source/<id>.md` stays thin: 2-3 line scope (beam/target/channel), a link to
  `../../papers/<id>/paper_<id>.md`, and a "feeds" list of the wiki pages it
  updated. The full extraction lives in `papers/`, not here.

## Operations

### Ingest (a new paper)
1. If `papers/<arxiv_id>/paper_<arxiv_id>.md` doesn't exist yet, run the
   `paper-extractor` subagent on the arxiv id first.
2. Read that extraction. Discuss key takeaways with the human.
3. Create `source/<arxiv_id>.md` (thin node, frontmatter + scope + backlink).
4. Create or update every relevant `experiment/ target/ channel/ concept/
   model/` page: add the measurement, cross-link with `[[...]]`, note agreements
   and contradictions. One paper typically touches 5-15 wiki pages.
5. Update `index.md` (add the source row + any new pages).
6. Append one line to `log.md`: `## [YYYY-MM-DD] ingest | <title> (<arxiv_id>)`
   then 2-4 bullets of what changed.

### Query
Read `index.md` first to locate pages, drill in, synthesize an answer **with
citations**. If the answer is a reusable cross-paper synthesis (a comparison,
a discovered connection), **file it back** as a `comparison/` page and log it —
explorations should compound, not vanish into chat. For plots, use the
`plot-style` skill / `results/template/plot_style.py`.

### Lint (health check, on request)
Scan for: contradictions between pages, stale claims newer sources supersede,
orphan pages (no inbound links), important concepts mentioned but lacking a
page, missing cross-references, and data gaps a web search could fill. Report a
prioritized list; suggest new questions and sources to chase. Don't auto-fix
physics judgments — surface them for the human.

## Navigation files

- **`index.md`** — content catalog: every page with a link + one-line summary,
  grouped by category. Update on every ingest. Read it first when querying.
- **`log.md`** — append-only timeline; each entry begins
  `## [YYYY-MM-DD] <op> | <title>` so `grep "^## \[" log.md | tail` works.

## Invariants
- Never edit `papers/` (raw layer) or anything outside `wiki/` during a wiki op.
- Every number traceable to a source id; otherwise write `(not stated)`.
- New page → also add it to `index.md`. New ingest → also append to `log.md`.
- Commit only when the human asks.
