# Prior-art note: klieo `runlog` (Rust agent framework) — closest published analog to our runlog

- **Source:** docs.rs/klieo (v1.0.0, MIT). Pages read: `klieo::runlog` module index + `klieo::runlog::struct.LlmIo`.
- **What klieo is:** "Open-source Rust agent framework — typed agents, durable inter-agent comms, local-first." The `runlog` module is its **"Tier 2 observability — RunLog projection + replay engine"** (feature-gated).
- **Why kept here:** klieo is essentially a production-grade Rust implementation of the runlog idea this project is building (see [[project-goal-reproducible-agentic-workflow]]); strong external validation + one mechanism we should adopt.

## klieo's model (event-sourcing: record -> project -> replay)
1. **Record** — durable truth is an append-only `Vec<Episode>` (raw events: each LLM call, each tool call).
2. **Project** — `projector` DERIVES an aggregate `RunLog` (list of `Step`s) from the episode stream. `project`, `project_with_llm_io`, `project_with_price_table`.
3. **Replay** — `replay` re-runs a recorded `RunLog` against caller-supplied **test doubles** (`LlmClient` + `ToolInvoker` stubs), returning the recorded final assistant text. **Deterministic-only.**

Key types: `RunLog` (aggregate), `Step` ("one unit of agent work — either an LLM call or a tool call"), `StepKind` (discriminator), `LlmIo` (sidecar, below), `Usage`/`Cost`/`Rates`/`PriceTable` (cost accounting), `InMemoryRunLogStore`/`SqliteRunLogStore`, `DeterministicCompaction`(default)/`LlmCompaction`.

## `LlmIo` — the piece we don't yet have
"Sidecar I/O record for a single `Episode::LlmCall`." The core `Episode::LlmCall` stores **only token counts + latency**; `LlmIo` attaches the actual text so projected logs become replayable.
Fields: `prompt: String`, `completion: String`, `model: Option<String>`, `provider: Option<String>`, `prompt_tokens/completion_tokens: Option<u32>` (all `#[serde(default)]`).
Docs, verbatim: **"Without this sidecar, projected LLM step input/output stay null and replay cannot reproduce the recorded prompt."**

## Three takeaways for OUR runlog
1. **Record-vs-project separation (validates + extends us).** klieo formalizes immutable event log vs derived view. We do this ad-hoc (`*.log`/`*.gridlog` = truth; `jq` = projection). Lesson: make **projection a first-class, reusable operation** — our planned committed run-manifest IS a projection; treat it as a named derived artifact, not a one-off script.
2. **`LlmIo` is the mechanism for our "captures WHAT ran, not WHY" gap.** Our runlog records the command but not the agent's decision/reasoning. klieo's answer: a **per-step prompt/completion sidecar** so replay reproduces reasoning, not just commands. This is the concrete shape for capturing the decision chain (cf. the verified review finding: no rationale/parent_jobid in make_initial_log).
3. **"Deterministic-only replay against test doubles" confirms our central invariant.** klieo's replay STUBS the LLM and returns recorded output — it does NOT re-run the live model. That is exactly our **replay-without-LLM invariant** built as code: you can't replay a live non-deterministic LLM, so replay = re-derive artifacts with the model mocked. Independent confirmation that "replay without the LLM" is the correct and only tractable definition.

## One caution to steal (trust model)
Docs admit `LlmIo` cost fields are "caller-supplied" and the projector "trusts the sidecar verbatim" — a compromised agent could spoof them; audit-grade fields should come "straight from the LLM client's response rather than the agent layer." General principle for us: **capture provenance as close to the source as possible** (binary stdout, API response, supervisor-computed hash), NOT from the orchestrator's self-report. This is why our supervisor-computed `output_sha256` is trustworthy and a self-reported field would not be.

## Borrowable design (fold into plan's runlog section)
- A typed **`Step` stream with `StepKind`** where command-runs AND llm-decisions are both Steps -> a study becomes ONE replayable ordered sequence, not two disconnected layers (commands in `*.log`, reasoning nowhere).
- A **per-step LLM-I/O sidecar** (prompt+completion+model+provider) = our `LlmIo` equivalent; the durable artifact for the decision chain.
- **Projection as a named operation** producing the committed run-manifest.

## Relation to other notes
- Convergent with `notes/2510.25506-llm-reproducibility-se.md` (report determinism knobs; SBOM = runlog+hashes) and `notes/2604.14696-llm-codegen-from-hep-papers.md` (bound non-determinism, human-in-the-loop). klieo adds the *engineering shape* (event-source -> project -> deterministic replay) those two motivate.

See plan: `.claude/plans/lucky-painting-nova.md`.
