# Note: LLMLog (VLDB 2025) — log TEMPLATE PARSING, NOT our runlog (relevance caveat)

- **Title:** LLMLog: Advanced Log Template Generation via LLM-driven Multi-Round Annotation
- **Authors:** Fei Teng, Haoyang Li, Lei Chen (HKUST / PolyU / HKUST-GZ) · **Venue:** PVLDB 18(9):3134-3148, 2025 · DOI 10.14778/3746405.3746433
- **Artifact (ACM badge):** github.com/XinTT/LLMLog
- **Local PDF (session-temp):** `.../tool-results/webfetch-1780599292395-0t79q7.pdf`

## RELEVANCE VERDICT (read first)
**Different sense of "log."** LLMLog parses UNSTRUCTURED operational system logs (HDFS/Spark/Apache stderr) into structured templates for anomaly detection. Our "runlog" is a PROVENANCE LEDGER of commands we emit on purpose. Shared noun, different problem. LLMLog never touches reproducibility/provenance/seeds/replay/orchestration; its lineage is LogMine/Drain/SwissLog/DivLog (log parsing), not Snakemake/PROV/MLflow.
**=> DO NOT cite as related work for our reproducibility thesis (category error a VLDB-literate reviewer catches).** Keep ONLY as (a) a method/tool option for Leg C, and (b) a one-clause design foil.

## What it does (accurate extraction)
Log template generation: `2024-11-14 192.168.1.1 GET /index.html 200 123ms` -> `[DATE] [IP] <GET> [RESOURCE] [STATUS] [LATENCY]` (each word -> word-type or kept as keyword). Three prior families: heuristic (Drain/LogMine, brittle rules), neural (transformers, need big annotated sets), LLM-based (DivLog: multi-round annotation + ICL). Fixes 3 limits of LLM approaches: embedding-cosine similarity overweights noise (timestamps/IPs) & misses keywords (POST); annotation ignores LLM confidence; fixed top-k demos misguide.
Contributions:
1. **SED (Semantic Edit-Distance)** similarity emphasizing keyword coverage, word-level cosine sets replacement cost; O(|si|*|sj|); beats embedding cosine for same-template ID.
2. **Adaptive multi-round annotation under budget B_r**: pick most representative (SED-coverage) + most challenging (low LLM confidence) logs for human labeling. NP-hard (reduction from Max Coverage), greedy 1-1/e (Thm 2). Adaptive per-round budget from word-increment (Eq 11).
3. **LLM confidence + word-consistency indicator** = hallucination detector (predicted word count vs input; avg word-probability).
4. **Adaptive demonstration selection**: minimum labeled-demo set covering all keywords of an input (greedy set-cover) vs fixed top-k -> cheaper, more relevant ICL.
Eval: 16 datasets (LogPai), beats SOTA accuracy while cutting compute + API cost.

## The ONE genuine use for us: Leg C (failure-mode taxonomy)
Our primary runlogs are structured JSON => no parsing needed. But THIRD-PARTY tool output we don't control IS unstructured: GENIE C++ stderr ("unphysical event ... rejected" x millions), OTEL KeyError traceback, spack SIGABRT/malloc_consolidate, jobsub hold reasons. Clustering THAT into failure templates with frequencies = log-template-generation; LLMLog is SOTA technique.
**Caveat:** for our ~6-8 known failure modes, a dozen regexes suffice. Use LLMLog only if the taxonomy genuinely explodes. Cite it then as a METHOD in the evaluation section, not as thesis related-work.

## The deeper point (argument FOR our design)
LLMLog exists because systems emit UNSTRUCTURED logs and someone reconstructs structure post-hoc. Our runlog emits **structure by construction** at execution time, so the parsing problem never arises. One-clause foil for the paper:
> "Rather than recover structure from unstructured logs post-hoc (as in log-template-generation [LLMLog]), our runlog emits structured, self-describing provenance at the point of execution -- structure by construction, not by inference."
This is the only framing in which to cite it.

## Minor transferable nuggets
- LLM-confidence + word-consistency hallucination check: a pattern for "detect when the LLM output is untrustworthy" (tangential to our verification theme; cf [[project-goal-reproducible-agentic-workflow]]).
- Similarity should weight meaningful tokens, discount noise (SED idea) — generic good practice.

## Relation to other notes
Unlike `notes/2510.25506-llm-reproducibility-se.md`, `notes/2604.14696-llm-codegen-from-hep-papers.md`, and `notes/klieo-runlog-prior-art.md` (all genuine related work / prior art for the runlog-reproducibility thesis), THIS one is a different research area kept for tooling + a single design-foil sentence. Do not over-weight it.
