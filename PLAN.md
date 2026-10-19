# EZ-Redis — Implementation Plan (`PLAN.md`)

Task `rd-20261019-032903-bc12` · Author **backend_lead** · Plan revision **2** (approved by the user at `2026-10-19T04:32:58.010Z`) · Stage **implementing** · Status: **proposed plan — nothing in it has been built**.

**What this document is.** A high-level, multi-phase implementation plan for the whole EZ-Redis product, written from `docs/original-prompt.xml` (the authoritative product statement), `requirements.md` rev 3, `architecture.md` rev 2, `research_summary.md`, the six specialist plan inputs (`notes/*-plan-input.md`), and QA's `plans/qa_test_plan.md` Part A. All eleven original A–K sections are retained in the original order and titles; the numbered phase list lives in **§G**.

**Label key (FR-28 / NFR-6 / NFR-7).** Every capability, benchmark, integration, consultation and design statement in this document carries one of four labels:
`[verified]` — traced to a source or repository artifact actually read for this task · `[proposed]` — a recommendation that has not been built · `[assumption]` — a belief that needs confirmation · `[unresolved]` — open, with a recommended default named (FR-29).

**Nothing built, nothing measured, nothing integrated.** No component has been implemented; no dependency has been installed or pinned; no test, benchmark, load test, integration or measurement has been run; no Redis instance, MCP client, Jev or LangGraph integration has been executed; tree-sitter co-loading has not been executed; no validator, scanner or audit tool has been run. Every number in this document is a target, a threshold, an estimate or a research-cited fact — never a result. The two latency targets and the ≥ 90 % precision bar are **unmeasured** (§H). No code, test, configuration or scaffolding file was created by this task: `PLAN.md` is the only repository file it creates.

**How to read the estimates (FR-11 / D-7).** Every calendar estimate below is labelled **indicative**, states its assumptions, gives an uncertainty range, and is a *forecast — not a measurement and not a commitment*.

## Document control and consultation roster (FR-30 / AC-26)

The plan was made after consulting the specialists it leads. Each consulted specialist wrote an input file that I read and folded in; the table marks every entry exactly one of **`consulted`** or **`deliberately excluded with a reason`** (no third status). Nothing was measured or built in any consultation: a consultation is design review of this document, **not** verification of runtime behaviour, and it is never cited as evidence that code, tests or an integration works.

**What the `[verified]` label asserts on this roster — and what it does not (FR-30(d)).** On a **consulted** row, `[verified]` asserts exactly two checkable things: (i) the consultation demonstrably happened — the specialist's dispatch id is recorded; and (ii) its output is identifiable and traceable — the named note file (`notes/*-plan-input.md`), `architecture.md` rev 2 or `plans/qa_test_plan.md` exists, was written by that specialist, and was read for this plan. It does **not** assert that the design is correct, that any code works, that any number was measured, or that any runtime behaviour was observed. The specialists say the same themselves: `caching` §7 records "nothing in this note is `verified` about the product's behaviour — only about artifacts and cited sources", and `architecture.md` states "No benchmark, test, integration or measurement was performed". On a **deliberately excluded** row, `[verified]` asserts that the exclusion, its reason and its basis rest on the named artifact **and** that the absence of the review is disclosed in the row text — it never asserts that the review happened. No entry in this section carries `[verified]` for a review this document records as not performed (FR-28).

**How the alternative and risk entries below were populated (FR-30(c)) — and how to audit them.** Only `caching` wrote the literal phrases "strongest alternative" and "principal technical risk" (its §7). For every other entry those two items are a **selection** from what the specialist did record, and each row states its basis as either **own** (the specialist's own words, quoted or closely paraphrased, with the locating section named) or **selection** (the plan author chose which of several options the specialist recorded is the strongest — the options themselves are always the specialist's). Where the nearest recorded position is weaker than a stated alternative or risk, the row says so instead of inventing one. Nothing here was fabricated to fill a column.

### (a) The workflow specialists

| Specialist | Status | Input | Contribution folded in (attributed in §12-style detail at the phase and section it touches) |
|---|---|---|---|
| **data_processing** | **consulted** `[verified]` (`d-03b937`) | `notes/data_processing-plan-input.md` | adapter→IR interface with deterministic fact identity; rule interface `input_slices`/`cross_file`/`requires_config`; config model + defaults; run-manifest fields + accounting invariant; provenance levels and `unresolved` `impact`/`blocking`; `KeyExpr` deepenings; total ordering; bounded memory; encoding/malformed handling; incremental invalidation closure, drift refusal, slice sufficiency |
| **caching** | **consulted** `[verified]` (`d-243859`) | `notes/caching-plan-input.md` | analysis-category **assertion-ceiling** table; rule-id conventions and interaction/exclusion rules; derivable-vs-`needs_confirmation` table; ADR-D1…D7 (including the disclosed **missing rate-limiting skill**); recommendation expansion (`change_kind`, `constraints_applied`, `staleness_bound`, `questions`) and constraint catalogue **C-1…C-8**; per-axis trade-off rules; the three document outlines; the honest-claims table |
| **security** | **consulted** `[verified]` (`d-bf439b`) | `notes/security-plan-input.md` | B3/B4/B5 deepening; enforcement-point register **EP-1…EP-6**; two-axis allowlist as **five axes** and why `KEYS`/`INFO`/`CONFIG GET`/`CLIENT LIST` are special; the reason-code catalogue (`unf_*`/`wbf_*`/`aig_*`/`mcp_*`); the write-boundary contract; secret classes and invariants **I-S1…I-S8**; trust boundaries T1–T6; failure modes **FM-1…FM-23**; the operator ACL recipe; supply-chain/licence triage |
| **api_development** | **consulted** `[verified]` (`d-18e0b3`) | `notes/api_development-plan-input.md` | B6 thin-adapter rules **R-B6-1…R-B6-7**; **D-MCP-1…D-MCP-6** incl. the 128-tool cap and the deprecated `.vscode/mcp.json`; `ToolResult` envelope + RFC 9457 `Problem` with an **11-code** catalogue; cursor/pagination and fixed sort orders; confinement **W1–W6**; determinism **D1–D6** with the live-observation carve-out; no-mutation **N1–N6**; all six tool schemas |
| **resilience** | **consulted** `[verified]` (`d-3355a7`) | `notes/resilience-plan-input.md` | error/reason-code catalogue additions; the **deterministic-fallback contract as a named return value** (5 invariants); failure modes **F1–F24**; invariant **BF-1** (static completeness); Jev and live-Redis budgets with `429`/`529`/`retry-after`; the single-retry-layer decision; `recursion_limit ≤ 8` |
| **observability** | **consulted** `[verified]` (`d-6738ff`) | `notes/observability-plan-input.md` | the fixed 8-stage pipeline table and the run-directory-as-only-state seam; the **run-directory contract** (`RunManifest`/`StageRecord`/`run_summary.json`/`RunLogEvent`); reason codes + CLI exit codes; redaction rules; the FR-19 "no metrics backend / no tracing / no telemetry egress" statement; **R-14** |
| **systems_architect** | **consulted** `[verified]` (earlier, via `architecture.md` rev 2) | `architecture.md` | 14 components (C1–C14), six boundaries (B1–B6), the 28-phase/6-milestone decomposition, gates G1–G6, nine ADRs, the four field-level contracts, the traceability matrix |
| **qa** | **consulted** `[verified]` (in parallel, A2) | `plans/qa_test_plan.md` | §H content H.1–H.6 (corpus, labelling protocol, precision definition, rule disposition, latency procedure with cold/warm separated, reporting rules) — QA owns it and §H carries it verbatim |
| **database** | **deliberately excluded** `[verified]` | — | EZ-Redis owns **no datastore** in the target slice: the only state is a JSON run directory. The single trigger — P23 choosing a SQLite-backed index over JSON — is `[unresolved]` and conditional; if it fires, `database` activates then. *(Basis: `architecture.md` ADR-4/components — no server, queue or database; `observability` §1 C-5 records the conditional SQLite activation and confines it to the persisted symbol index and IR patch store.)* |
| **authentication** | **deliberately excluded** `[verified]` | — | There is **no authentication surface**: MCP is local stdio inheriting OS process identity, the CLI is local, and Redis/MCP credentials are operator configuration covered by `security`. A hosted/team mode (ADR-4 revisit) would activate it. *(Basis: `architecture.md` ADR-4 — stdio-only transport, no hosted mode in the slice; `security` §4.3 — credentials are operator ACL configuration and EZ-Redis never applies it.)* |
| **background_processing** | **deliberately excluded** `[verified]` | — | There is **no queue, worker, scheduler or asynchronous job**: the pipeline is synchronous and single-process. The optional agent belongs to `resilience` + `backend_lead`. *(Basis: `resilience` framing statement — "no server, no queue, no database, no collector", with a bounded-failure model instead of async machinery; `data_processing` bounded-memory table — "single-process synchronous loop … No queue, worker pool or async".)* |

### (a2) Strongest alternative and principal technical risk, per consulted entry (FR-30(c))

One row per consulted entry, so each of the three FR-30(c) clauses is decidable row by row. The **Basis** column follows the audit key above; an entry that is a *selection* rather than the specialist's own sentence says so.

| Consulted entry | Strongest alternative the plan did not take (and why) | Principal technical risk | Basis |
|---|---|---|---|
| **data_processing** | **The type-aware tier** (`api_tier="type_aware"`) — the TS compiler API for TS/TSX and LibCST for Python — the only tier of the four compared that resolves framework/DI-injected receivers and types, decorator semantics and cross-file data flow. Not taken: LibCST's type inference **needs a Pyre server plus watchman** (the note's own cell for DI-injected receivers), and the architect's ADR-1 records the TS API's Node-subprocess-and-npm cost; depth would also be language-asymmetric. The one-hop symbol index is kept instead. | **The baseline cannot resolve what most real call sites need**: framework/DI-injected receivers, keys built from a runtime value beyond a literal prefix, wrapper indirection past one hop and cross-file flow are `no`/`partially` at this tier, so many real call sites can only ever be `Unresolved`. The only honest defence is the note's own rule — nothing beyond the declared `never_resolves` ceiling may be asserted `resolved` — plus named ceilings (`parse_budget_ms_per_file` ⇒ `partial` + a reason code; `max_ir_facts`/`max_ir_bytes` ⇒ `limits_exceeded`) so the run degrades loudly rather than silently or by OOM. | **own** — §D.2 tier table (the `needs Pyre server + watchman`, `no`, `one hop`, `partially` cells) and its instruction that "the honest baseline claim is *syntax + heuristics + a one-hop symbol index*; anything beyond it is an `Unresolved`, never a resolved fact (B2)"; §"bounded memory" table rows `IR growth` and `Backpressure`. **selection** for ranking the type-aware tier "strongest" — the note compares four tiers without ranking them, and never uses the words "alternative" or "risk". |
| **caching** | **Derive caching and Redis-Search guidance from vendor documentation instead of reusing `redis/agent-skills`** (ADR-D1 option b). Not taken: duplication cost and a per-section attribution burden; retained as the fallback if the corpus's pinning/attribution proves impractical. | **The reuse corpus is generic maintainer prose**, so generated documents can restate general advice rather than the repository's observed usage. Mitigation: ADR-D6 plus the evidence-linked §F section rules and mandatory "not established" values. | **own, verbatim** — §7 consultation record, rows **"Strongest alternative considered"** and **"Principal technical risk from this specialist"**. The only entry where the specialist used FR-30(c)'s own vocabulary. |
| **security** | **A single-axis allowlist** — the `readonly` command flag alone, the simplest gate that could exist. Not taken because one axis is wrong in *both* directions: `KEYS` is `readonly` yet `@dangerous`, so an **axis-1-only allowlist over-permits** it; `INFO` has **no `readonly` flag at all**, so a flag-only axis cannot decide it and **under-permits**. | **The gate's decision inputs are server-version-dependent and partly unverified.** Pre-6.0 servers return no ACL categories, so the category axis cannot be evaluated (`unf_command_flag_axis_unavailable` — degrade and disclose, never assume safety); pre-7.0 cannot scope a subcommand safely, so granting the safe member grants the unsafe parent (`unf_subcommand_scoping_unavailable`); and the exact flag/category membership of `MONITOR`/`DEBUG`/`CLIENT KILL`/`SHUTDOWN` is **U-7 unresolved** — read from a live `COMMAND` at P22, never hard-coded — with `unf_command_capability_conflict` resolving drift **in the server's favour**. | **own** — §1.3's per-command table (`KEYS` and `INFO` rows, both sourced), §2.2a's reason-code rows and §4.3's U-7 item. **selection** for "single-axis allowlist" as the strongest alternative: the note states both axes and what each alone gets wrong, but never uses the word "alternative" and carries no "risk" row. |
| **api_development** | **A one-tool-per-rule surface (20+ tools)** — maximum discoverability and per-tool schema validation. Not taken: the client enforces a **hard 128-tool limit per request** shared with its built-in tools, and every tool definition is carried **on every turn**, so a fine-grained surface meets virtualization pressure and a per-turn context cost. Runner-up, also recorded and rejected: **one mega-tool with a `kind` switch**, which loses per-tool schema validation and discoverability. | **The surface's availability and invocation behaviour are the client's to decide, not EZ-Redis's.** Workspace Trust blocks workspace MCP configuration, so in restricted mode the server does not start at all; each invocation may require confirmation; sandboxing is unavailable on Windows. P21 therefore promises a reproducible walkthrough and troubleshooting, never silent or universal availability ("availability depends on client discovery, not EZ-Redis"), and makes **no token-count claim — none was measured**. | **own** — §D.1's **"Rejected alternatives (reason)"** column (D-MCP-1, D-MCP-6) and §D.2's cited client-behaviour rows with the P21 test line. **selection** for which of the six recorded rejections is "strongest"; the note's own vocabulary is "rejected alternatives" and it carries no "risk" row. |
| **resilience** | **Let the `typesafe-sdk` retry by default and disable our retry layer** — one fewer moving part, less code we own. Not taken: "a fallback must be taken *before* the deadline, and the SDK does not know the deadline." | **The provider SDK retries by default, so a naive design double-retries** — the note calls the SDK's default retry "a hazard (F17), not a convenience"; met by one retry layer on our side, the SDK pinned to a single attempt, and an attempt-count stub test asserting exactly two HTTP attempts on a persistent `529`. Residual: **no latency evidence exists** for Jev, live Redis or parsing, so every budget is a design allocation with a disclosed margin (RZ-A2), not a measurement. | **own, verbatim** — §3.4 "**Rejected alternative:** let the SDK retry and disable ours — rejected because…" and §9 row **RZ-A1** ("No latency evidence exists for Jev, live Redis or parsing"). **selection** for the double retry being "principal" over the other recorded hazards. |
| **observability** | **Put the run directory inside the analysed repository** at `<workspace>/.ezredis/runs/<run_id>/` — discoverable by the MCP client without a recorded run id. Not taken: it "pollutes the analysed repo and confuses the write-boundary story (B5/FR-21)"; the adopted default is the OS user cache directory with an explicit override. | **Instrumentation sits on the critical path, so the logger must be fail-open**: if the event stream cannot be written, the run still completes and reports the degradation through its exit behaviour, and **no logging call may raise into analysis** (asserted at P26). The specialist's own explicitly-labelled risk — **R-12**, run-directory location and lifetime, `[unresolved]` — is closed by adopting the note's recommended default. | **own** — §1 **C-4**'s option table (its own "Recommended? **no**/yes/no" column plus the quoted rejection reason), §3.5's last row ("the one observability non-negotiable that survives"), and R-12 in §0/§5. **selection** for the framing: the note uses "alternative" nowhere and "risk" only for R-12. |
| **systems_architect** | **Python depth via LibCST 1.9 plus the TS compiler API for TS/TSX as the primary depth strategy** (ADR-1 options b and c) — the only options offering real cross-file type resolution anywhere, and "real options that were genuinely available, not strawmen". Not taken as primary: LibCST type inference requires a Pyre server plus watchman ("operationally wrong for a CLI") and the TS API needs a Node subprocess and an npm dependency "for a result only TS needs"; both survive as recorded deepening fallbacks. | **Call-site resolution may prove insufficient**: if the four P08 measurements exceed ~20 s or show **more than ~60 % of call sites unrecoverable**, the design must pull the LibCST and TS-API tiers into earlier phases (ADR-1's rejected-alternatives fallback, U-1/U-2). Syntax-only depth means dynamic keys, wrapper indirection and cross-file flow are only partially resolvable — which is exactly why the IR carries `provenance.level` and `unresolved`. Every NFR figure is "plausible, unproven". | **own, verbatim** — ADR-1's **Options (a)–(e)**, **Decision**, **Consequences** and **Rejected-alternatives fallback**, introduced there by "Alternatives are real options that were genuinely available, not strawmen." **selection** for "strongest" and for "principal". *(Disclosure: `architecture.md`'s own "What this document does NOT claim" records that **it** consulted no specialists — that statement is about the architect's own inputs, not about whether the architect was itself consulted for this plan; it is the identifiable output the row above rests on, and the two statements do not contradict each other.)* |
| **qa** | **Count `needs_confirmation` findings as true positives in the headline precision number** — the lenient view, which flatters the tool at no cost to it. Not taken: "a `needs_confirmation` finding is reported but its truth is **not established**, so counting it as TP uses unearned credit"; both views are published, **the gate uses the conservative view**, and excluding them needs a recorded protocol revision carrying the alternative numbers. | **The ≥ 90 % bar rests on a hand-labelled corpus, so labellability is the weak link**: ambiguity is resolved conservatively ("ambiguity is an FP, never a TP"), a category's numbers are published only at **Cohen's κ ≥ 0.70**, "low agreement is a rule-quality defect, not a labelling nuisance", and any fixture/label/protocol change **invalidates every prior measurement** as stale. The corpus's language proportions are an `[assumption]` to confirm against expected target repositories. | **own, verbatim** — §H.3 "**`needs_confirmation` scoring rule (anti-inflation)**", "Tie-breaking", "Inter-labeller agreement" and §H.2 "Versioning & invalidation" plus "Representativeness". **selection** for calling these the strongest alternative and the principal risk: the note states rules with justifications and never uses the FR-30 vocabulary. |

**Reading the table honestly.** On wording: `caching` is **verbatim on both items**; `resilience`, `qa` and `systems_architect` are **verbatim or near-verbatim on both**; `security`, `data_processing`, `api_development` and `observability` are the specialist's own on the *content* of both items but required a **selection**, because their notes record options, rejections and consequences without ever using the words "alternative" or "risk". On ranking: every entry except `caching` involved a selection of *which* recorded option or consequence is the "strongest" or "principal" one, and each row's basis column says so. In no case was an option, a risk or a conflicting recommendation invented: where a note's nearest recorded position is weaker than a stated alternative or risk, the row reports that weaker position and names it as a selection rather than upgrading it.

### (b) The seven review roles `docs/original-prompt.xml` names — every one accounted for

| Prompt review role | Covered by | Status | Reason / evidence |
|---|---|---|---|
| Software architecture | **systems_architect** | **consulted** `[verified]` | `architecture.md` rev 2 (components, boundaries, ADRs, decomposition) |
| Static analysis | **data_processing** | **consulted** `[verified]` | `notes/data_processing-plan-input.md` |
| Redis engineering | **caching** | **consulted** `[verified]` | `notes/caching-plan-input.md` |
| Developer tooling and MCP | **api_development** | **consulted** `[verified]` | `notes/api_development-plan-input.md` |
| Security and quality | **security** + **qa** | **consulted** `[verified]` | `notes/security-plan-input.md`; `plans/qa_test_plan.md` |
| AI and decision systems | researcher's Jev findings + architect's ADR-6/ADR-7 | **deliberately excluded** `[verified]` | No dedicated AI specialist was consulted. The Jev capability/limits are research facts (`research_summary.md` RQ-4) and ADR-6 (deterministic orchestrator default) plus ADR-7 (agent-skills reuse) are the architect's. A dedicated AI review is deliberately not performed because the only AI phases (P27/P28) are **late-optional and droppable** behind G6 — reviewing optional, droppable work would be speculative effort. Disclosed as not performed (FR-28). |
| Agent orchestration | architect's ADR-6 + **resilience** | **deliberately excluded** `[verified]` | No dedicated orchestration specialist was consulted. P28 (LangGraph) is the final, explicitly **droppable** phase; its bounds (`recursion_limit ≤ 8`, bounded state, no-bypass guarantee, stopping conditions) come from **resilience**'s input, and its adoption criterion from ADR-6 — so a separate orchestration review is deliberately excluded. Disclosed as not performed. |

### (c) Reconciliation of the specialists' conflicting recommendations

| Conflict | How it was reconciled |
|---|---|
| `caching` proposed extending "never emit an empty document" from `IRIS.md` to **all four** documents; FR-22 literally says "include all four". | Adopted as a **disclosed deviation**: the four documents are *planned*, and each is generated only when its IR section is non-empty — FR-22 is satisfied by the phase existing plus the conditional rule, exactly as the plan already argues for `IRIS.md` (§F). |
| `caching` found `recommended_pattern` is cache-only, so rate-limiting (P12) and Search (P13) findings could not be recommended. | Adopted: a new `change_kind` field carries non-cache recommendations with `recommended_pattern: null` (§E). |
| `resilience` showed the naive 60 s stage allocation has **zero margin**. | Adopted: parse capped at 15 s and IR assembly at 12 s (Σ 52 s, 8 s margin), recorded as budget tension RZ-A2 (§I budget table). |
| `api_development` said `inspect_runtime_metrics` cannot satisfy "same `run_id` ⇒ same bytes". | Adopted as a **contract clarification**: the reproducibility guarantee applies to the five static tools and to *persisted* runtime evidence; a fresh live observation carries `observed_at` + `source="live"` (§E determinism D5). |
| `observability` and `api_development` disagreed on the run-summary field set. | Adopted: `run_summary.json` is the single truth and the MCP `summary` is a strict, identically-named subset — no renames (§E). |
| `api_development`'s problem-code set grew from 8 to 11; `resilience` and `observability` added reason codes. | Adopted as an additive contract revision: the catalogue is one closed table in §E; a 12th code needs a contract revision. |
| `caching` asked for four IR field additions (`ttl_form`, `atomic_group`, `cardinality_basis`, negative-evidence support). | Adopted as **additive** fields inside the IR contract (§E), with `atomic_group` deciding whether `rl.non_atomic_counter` is `static` or `needs_confirmation`. |
| `data_processing` flagged that §E could not absorb the five interfaces at field level inside its 200-line budget, and asked for the budget to be re-allocated **rather than compressing interfaces into prose** ("not to compress the interfaces into prose. Flagged; reconciliation is yours"). | Adopted in substance: §E carries all five interfaces at **field level** (§E.4–§E.8) and none was compressed into prose; the tension was paid by density in §C/§D rather than by cutting the interfaces. |
| `systems_architect` disclosed that FR-22's literal "record the meaning of IRIS as unresolved" collides with research having resolved it, and required the deviation to be **visible to the user** ("This is the one place where requirements and research collide"). | Adopted as a **disclosed** deviation: `IRIS.md`'s meaning is carried as a *sourced* finding attributed to `research_summary.md` (RQ-10) and never presented as `[unresolved]` (§F.1), with R-2 marked `settled` in §J; the deviation itself is stated openly at §F's "Disclosed deviation" block and §J's item 1, and the per-repository **contents** stay `[unresolved]` (U-13). |
| `qa` objected that P24 "owns the corpus" while P09–P14 already require corpus fixtures (circular), and that P25's 100 k-LOC benchmark cannot be measured from P24 alone ("architecture's `P07, P15` was wrong"). | Adopted: per-rule **developer fixtures** (rule owners, inside P09–P14) are separated from the **labelled measurement corpus** (qa, P24); P24's dependencies become **P08, P14, P15** and P25's become **P23, P24** — the corrected edges are the ones carried in §G. |

**Per-entry pointer, so the clause is decidable row by row.** `caching` → rows 1, 2 and 7 · `resilience` → row 3 · `api_development` → rows 4 and 6 · `observability` → row 5 · `data_processing` → row 8 · `systems_architect` → row 9 · `qa` → row 10. **`security` recorded no recommendation that conflicted with the design**: its input keeps ADR-8's two-axis doctrine and decomposes it into the five checkable axes A-flag / A-cat / A-sub / A-cap / A-bound, adopted additively in §I.3 and the §E.8e reason-code catalogue — recorded here as an **amendment, not a disagreement**, so there is nothing to reconcile. All eight consulted entries are therefore accounted for on this clause.

## A. Executive Summary

EZ-Redis is a **local developer tool** that statically analyses a codebase's Redis usage, reports evidence-backed findings, and generates a set of knowledge documents. This plan delivers a **high-level, phase-by-phase path** to build it; nothing here has been built.

**The recommended architecture is the simplest one that isolates the AI layer and the network from a deterministic core.** Fourteen components sit behind six boundaries. A single-process, synchronous pipeline walks a workspace, parses four languages, normalises Redis usage into one shared **Redis IR**, runs pure deterministic rules over that IR, derives recommendations, writes documents, and exports machine-readable results. The **run directory is the only state the tool has** — no server, no database, no queue.

**Locked target slice (FR-17 / D-8).** The deterministic core engine + the shared Redis IR + Python and JS/TS/TSX adapters + the CLI + an importable library + an MCP server. Deliberately **not** in the slice: a Java adapter, runtime telemetry correlation, a FastAPI service, an IDE extension and GUI work.

**Ordering guarantee (FR-19 / AC-14).** Core analysis runs with **no network access, no AI provider, no LLM and no live Redis**. Every phase that touches a model (P27, P28) comes after every deterministic phase; the only phase that opens a network socket to Redis (P22) is opt-in, after the whole core, the IR, both adapters, the findings model, recommendations and documents. **Jev is late-optional (P27); LangGraph is final (P28) and explicitly droppable without disturbing P01–P26.**

**Most consequential decisions.**

| # | Decision | Rationale | Rejected alternative (reason) |
|---|---|---|---|
| 1 | **tree-sitter 0.26.0 + three grammar wheels** as the primary parser, confirmation deferred to **P08** | One traversal model covers Python/JS/TS/TSX; MIT, no Rust toolchain; `tree-sitter-typescript` exposes both `language_typescript()` and `language_tsx()` | LibCST as primary (Python-only; type inference needs a Pyre server + watchman); TS compiler API as primary (Node subprocess + npm for a TS-only gain) |
| 2 | **pydantic v2** for all boundary contracts | `mcp` already requires `pydantic ≥ 2.12`, so it is a mandatory transitive dependency anyway; JSON Schema generation drives the MCP tool definitions | msgspec (a second validator for no saving); dataclasses (no validation, no schema) |
| 3 | **Bespoke pydantic JSON canonical, SARIF 2.1.0 as a secondary export only** | SARIF cannot natively carry evidence graphs, confidence or `unresolved` semantics | SARIF as canonical; `sarif-om` (frozen since 2019) |
| 4 | **MCP over stdio with a capped 6-tool surface; no FastAPI** | VS Code Copilot enforces a hard 128-tool per-request cap and tool definitions cost context every turn; stdio inherits OS process identity | Streamable HTTP/SSE (unsupported in workspace `.mcp.json`); FastAPI (a second public surface for a tool required to run offline) |
| 5 | **Two-axis read-only live-Redis policy** (`readonly` ∧ ¬`@dangerous`) + runtime `COMMAND` cross-check | `KEYS` is read-only **yet** dangerous; `INFO` has no `readonly` flag at all — a single-axis rule is wrong in both directions | "read-only commands only" literally; an ACL category grant (`+@read`) |
| 6 | **Write boundary: only EZ-Redis-generated files, never an existing file** | Prevents data loss in the analysed repository; the generated-file marker doubles as the staleness detector | Fully read-only (the user wants generated docs); editing existing source (needs approval gates far beyond the slice) |
| 7 | **Deterministic orchestrator as the default; LangGraph droppable** | Bounding and persistence are ~150 lines over the run directory; only cross-process resumable human approval would justify a checkpointing framework | Adopt LangGraph by default (a large transitive tree off the critical path); a hand-rolled agent loop (bespoke irreversible state machine) |
| 8 | **Reuse `redis/agent-skills` (MIT) as the domain-knowledge corpus** | Maintainer-authored prose on exactly the four documents' subjects; the differentiator stays static analysis + evidence-backed recommendation | Re-derive guidance in-house (duplication cost); official docs only (weaker coverage) |

**What to build first.** §G orders 28 phases across 6 milestones, each ending in exactly one go/no-go gate. The first three milestones (P01–P19) are the entire deterministic product and need no network. The quality bar is measured, not asserted: §H defines a corpus, a labelling protocol, a precision gate (Wilson 95 % lower bound ≥ 0.90) and a latency procedure with cold and warm separated.

**Honest limitations stated up front.** tree-sitter is syntax-only, so the IR carries explicit `provenance` and `unresolved` axes rather than claiming resolved semantics; the achievable call-site resolution rate is unmeasured and due at P08. The two latency targets and the precision bar are **unmeasured**. No benchmark, test, integration, measurement or specialist *runtime* review was performed; the consultations recorded above are design reviews of this document.

## B. Current Repository Assessment

**Verified state (read directly for this task).** The repository is greenfield. Nothing is assumed to exist that was not observed.

| Fact | Evidence | Label |
|---|---|---|
| Root holds only `.git/`, `.gitignore`, `.pi/`, `docs/` | `ls -a` output: `.` `..` `.git` `.gitignore` `.pi` `docs` | `[verified]` |
| No source, test or configuration file exists | `find` for `pyproject.toml`/`uv.lock`/`package.json`/`test_*.py`/`tests/**` returns nothing outside `.git/` and `.pi/` | `[verified]` |
| No `PLAN.md` (and no `PLAN.MD`) exists anywhere outside `.pi/` | `find . -iname 'PLAN*'` matches only task-artifact paths under `.pi/` | `[verified]` |
| `.gitignore` already anticipates a Python project | it lists `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `dist/`, `*.egg-info/`, coverage artefacts, `htmlcov/`, `.hypothesis/`, `logs/` | `[verified]` |
| `.gitignore` reserves an adversarial oversized-file fixture | entry `tests/fixtures/adversarial/python/adv_oversize.py` | `[verified]` |
| `.gitignore` ignores `/docs` | line `/docs`, so the reference documentation and `docs/original-prompt.xml` are **not** tracked repository content | `[verified]` |
| `docs/complete-redis-architecture.md` is empty (0 bytes) and unusable as a source | file size | `[verified]` |
| `.pi/` is untracked and **not** gitignored | raw `git status --porcelain` shows exactly `?? .pi/`; `git check-ignore -v .pi/` exits 1 (not ignored) | `[verified]` |
| Local toolchain | `uv`, `uvx`, `python3.11`, `python3.13`, `python3.14`, `ruff`, `node`, `npm`, `npx` present; `poetry` and `redis-cli` absent | `[verified]` |
| Git history | only initial and fresh-start commits | `[verified]` |

**What exists today.** No component, no dependency manifest, no test, no CI workflow and no documentation generator. Every one of the fourteen components in §D is **new** and `[proposed]`; every phase in §G is `[proposed]` and none has been started.

**Conventions and constraints this plan must respect.**
- **Greenfield freedom, bounded by the user's locked decisions** (D-1…D-18 in `requirements.md`): the plan commits to the target slice, adapter languages, safety boundaries, quality bar, latency targets and AI-layer placement, and marks everything else as proposal, assumption or unresolved.
- **`.gitignore` already names the fixture layout** the corpus phase will use, including the adversarial oversize fixture — the plan reuses it rather than inventing a new convention.
- **`docs/` is not tracked**, so the plan cites local reference material (`docs/Redis-cache-aside.md`, `docs/cache-consistency-strategies.md`, `docs/jev-docs.md`) as consultation inputs, not as repository content.
- **No existing conventions to preserve** — there is no lint config, no CI, no package manifest whose style must be followed. The plan therefore proposes one (`uv`, `ruff`, `mypy`, `pytest`, `hypothesis`) rather than inferring one.
- **The task's own workflow metadata (`.pi/`) is pre-existing untracked content** that this task must not touch; the repository-footprint check is therefore the filtered `git status --porcelain -- . ':!.pi'` (§K), and `.gitignore` is **not** edited to silence it (FR-3).

**Explicit statement required by FR-5 / AC-2.** **No component of EZ-Redis has been implemented.** This document is a plan: it recommends an architecture, a dependency set, a phasing and a set of contracts, and it states plainly which of its claims are verified, proposed, assumed or unresolved.

**Nothing to deploy (see §J).** There is no environment to provision, no service to deploy and no migration to run: the product is a local Python package plus an MCP stdio entry point, and this task creates a document only.

## C. Proposed Architecture

### C.1 Proposed repository layout and package name (FR-16 / AC-12 — planning material)

Package **`ezredis`** (distribution `ez-redis`). This is an illustration of the proposed tree, not a commitment to every file: phase boxes name packages, never individual modules (FR-12).

```text
pyproject.toml · uv.lock · PLAN.md
src/ezredis/
  __init__.py            # importable public API                              (P19)
  discovery/             # workspace walk, language detection, manifests     (P02)
  ir/                    # shared Redis IR — pydantic v2, the load-bearing contract (P03)
  adapters/python/       # tree-sitter-python → IR facts                     (P06)
  adapters/js/           # tree-sitter-javascript + tree-sitter-typescript (TS and TSX) → IR facts (P07)
  analysis/              # pipeline, rule registry, deterministic orchestrator, rules (P05, P09–P14)
  findings/              # finding record + evidence/confidence model        (P04)
  recommend/             # deterministic pattern selection, recommendation record (P15)
  documents/             # four document generators                          (P16)
  output/                # canonical JSON + secondary SARIF 2.1.0 exporter   (P17)
  policy/                # write boundary + two-axis Redis allowlist decisions (P16, P22)
  runtime/               # opt-in live-Redis inspector — the NETWORK BOUNDARY (P22)
  ai/                    # Jev adapter — the AI BOUNDARY (optional)           (P27)
  agent/                 # LangGraph orchestrator (optional, droppable)       (P28)
  mcp/                   # MCP server over stdio, capped tool surface         (P20)
  cli/                   # click CLI                                          (P18)
tests/fixtures/{python,js,ts,tsx,adversarial}/   # fixtures; labelled corpus lives under tests/fixtures/**
```

The tree separates the two genuinely dangerous capabilities (network egress and model calls) and the filesystem write capability into their own packages, which is what makes the offline guarantee checkable rather than aspirational.

### C.2 Components and responsibilities

| ID | Component | Status | Single responsibility | Needs zero network/AI? | Phase | Requirement |
|---|---|---|---|---|---|---|
| C1 | `discovery/` | new | Walk a workspace, apply ignore rules, detect supported languages, emit a deterministic path-only manifest | yes | P02 | FR-17 |
| C2a | `adapters/python/` | new | Parse Python to a CST and emit shared-IR facts for Redis client usage | yes | P06 | FR-17, FR-26 |
| C2b | `adapters/js/` | new | Parse JS, TS and TSX (two grammars) and emit the same IR facts | yes | P07 | FR-17, FR-26, R-6 |
| C3 | `ir/` | new | The single load-bearing contract: a validated, provenance-carrying model of Redis usage; no adapter types, no Redis connection | yes | P03 | FR-14, FR-19, FR-26 |
| C4 | `analysis/` | new | Deterministic rules over the IR producing findings | yes | P05, P09–P14 | FR-17, FR-19, FR-23 |
| C5 | `findings/` | new | The finding record: evidence classification, severity, confidence, limitations, `unresolved` | yes | P04 | FR-14, FR-28 |
| C6 | `recommend/` | new | Deterministic candidate-pattern selection and the recommendation record | yes (deterministic path) | P15 | FR-17, D-12 |
| C7 | `documents/` + `policy/` write path | new | Generate the applicable knowledge documents; enforce the write boundary | yes | P16 | FR-21, FR-22 |
| C8 | `output/` | new | Canonical pydantic-JSON export + secondary SARIF 2.1.0 export | yes | P17 | FR-22, AC-10 |
| C9 | `cli/` | new | click entry point; subcommands over the core; no business logic | yes | P18 | FR-17 |
| C10 | `__init__.py` public API | new | Stable importable surface: `analyze()`, `load_ir()`, `list_findings()`, `recommend()`, `generate_documents()` | yes | P19 | FR-17 |
| C11 | `runtime/` | new | Opt-in, read-only **live** Redis inspection; the only component that opens a Redis connection | network yes / AI no | P22 | FR-20 |
| C12 | `mcp/` | new | Thin MCP adapter (stdio, capped tools, documents as resources) over C10 | local stdio only | P20 | FR-17, A-5 |
| C13 | `ai/` | new, **optional** | Jev adapter: bounded questions over a reduced evidence summary; deterministic fallback | network + AI | P27 | FR-18, D-5 |
| C14 | `agent/` | new, **optional, droppable** | LangGraph orchestrator over the core; never replaces deterministic analysis | network + AI | P28 | FR-18, D-5, R-5 |

Every component traces to a named requirement; none is speculative. C13 and C14 exist only because D-5 keeps them as optional phases behind a gate, not because the product needs them to work.

### C.3 Boundaries — the smallest set that isolates the network and the AI

| Boundary | Inside | Must never leak across | Enforcement |
|---|---|---|---|
| **B1 Deterministic/static boundary** — surrounds C1–C10 | parsing, IR building, rules, findings, recommendations, documents, CLI, library | no LLM/AI call, no network call, no Redis connection, no `runtime/`, `ai/` or `agent/` import | an import-guard test (P01/P05) plus the phase ordering (all of M1–M3 precedes every network/AI phase). This makes FR-19 structural, not aspirational. |
| **B2 Adapter boundary** — C2a/C2b → C3 | shared IR facts plus per-fact provenance | adapter-specific types (CST nodes, grammar names, byte offsets) never appear in the IR; adapters may not import `analysis/` or `findings/`; an unrepresentable language feature becomes an IR `unresolved`, never a smuggled field | source-level guard (`ir/**` must not import `tree_sitter`) + the P08 conformance harness |
| **B3 Runtime boundary** — C11 | the only Redis socket/TLS/ACL code; the two-axis allowlist and `COMMAND` cross-check | static modules never import `runtime/`; `runtime/` may not import `analysis/` or `ai/`; keyspace notifications are never *enabled*; runtime facts enter only as `EvidenceItem(kind="runtime_metric")`, never as an authoritative replacement for static facts | EP-2 (single gate), table-driven gate tests |
| **B4 AI boundary** — C13 (and C14) | provider client, bounded question building, response validation, fallback | core never imports `ai/`; only a capped **reduced evidence summary** crosses outward — never a whole IR, whole repository or file contents; no model answer may authorise an action, set a threshold or bypass a rule (all arithmetic stays in code) | EP-3 (single egress builder) + import guard |
| **B5 Write boundary** — C7 + `policy/` | all filesystem writes for generated documents and the run manifest | writes only to EZ-Redis-generated paths identified by a provenance marker; never an existing repository file | EP-1 (one predicate consulted by the only writer) |
| **B6 Client boundary** — C9, C10, C12 | thin adapters: argument parsing, path confinement, single library call, response shaping, error→code mapping, cursor assembly | no rules, no IR mutation, no parsing, no discovery, no Redis socket, no AI call, no write, no threshold decision, no policy decision | seven checkable thin-adapter rules **R-B6-1…R-B6-7** below |

**R-B6-1…R-B6-7 (the thin-adapter contract).** Each is enforced at the boundary, because B6 is the only place a third-party caller can be wrong. **R-B6-1** one tool = one public-API call (a handler composing two library calls into new behaviour is a defect). **R-B6-2** no business logic in the adapter (no severity/confidence computation, no pattern choice, no TTL judgement, no ordering beyond the fixed sort keys). **R-B6-3** no domain constants in the adapter — every enum, default and bound comes from the shared models. **R-B6-4** CLI, library and MCP expose the **same** capability set, the only exceptions being documents-as-resources and the opt-in `inspect_runtime_metrics`. **R-B6-5** tool JSON Schema is **generated from the pydantic models**, never hand-written (a drift test regenerates and diffs). **R-B6-6** every error leaving B6 is a `Problem` — internal exceptions, stack traces, absolute host paths, file contents and secrets are never returned. **R-B6-7** B6 is read-only; `write_documents` is the single file-writing path, gated by `policy/`. Allowed dependency arrows: `cli/ → __init__` · `mcp/ → __init__` · `__init__ → {analysis, recommend, documents, output, ir, discovery}` · `runtime/ → policy/`; nothing imports `cli/` or `mcp/`.

**B6 is not an interception layer.** MCP availability depends on client discovery, Workspace Trust and per-invocation confirmation — not on EZ-Redis (ADR-4; §D).

### C.4 The analysis pipeline — eight fixed stages over one run directory

**The seam.** Analysis is a single-process, synchronous pipeline over **one run directory, which is the only state the tool has** (no server, no database, no queue). Every stage writes its own record into the run directory before the next stage starts, so an interrupted run is resumable and a completed run is auditable without re-parsing. **No stage talks to the network on the default path.**

| `stage_id` | Producer | Input → output | Per-stage emission (integers) | Failure semantics |
|---|---|---|---|---|
| `discover` | P02 | workspace → file manifest | `items_considered/processed/skipped`, `ceilings_hit` | skip-with-report; never abort |
| `parse` | P06, P07 | manifest → adapter candidates | `files_by_parse_status`, `parse_failures`, `unresolved_by_kind(parse_failure)`, `parse_timeout` | per-file degradation; run continues (F1) |
| `ir_assemble` | P03 | candidates → canonical IR | `ir_facts_total`, `ir_facts_by_kind`, `unresolved_count` | unresolved is recorded, never inferred away |
| `analyse` | P05, P09–P14 | IR → findings | `rules_run`, `rules_skipped`, `findings_total`, `findings_by_severity`, `rule_raised` | a raising rule is isolated; stage becomes `partial` |
| `recommend` | P15 | findings → recommendations + questions | `recommendations_total`, `questions_total`, `source` | insufficient evidence yields a question, not a failure |
| `documents` | P16 | IR+findings+recommendations → documents | `documents_written`, `documents_refused`, `documents_skipped_not_applicable` | refusal is reported, never overwritten (F12) |
| `export` | P17, P18 | findings → canonical JSON / SARIF | `artifacts_written`, `schema_validated` | schema drift fails the stage, not the run |
| `runtime_inspect` (**opt-in, absent by default**) | P22 | named connection profile → runtime evidence | `commands_attempted/allowed/refused`, `observations` | disabled ⇒ `skipped` (`runtime_disabled`); unreachable ⇒ `partial` (F5) |

**One event stream, two renderings.** A single structured event stream is the source of truth; the human CLI summary, the `--json` summary and `run.log.jsonl` are renderings of it, so a human line can never say something the JSON does not. **Invariant:** the durable JSON event stream goes to stderr and/or `run.log.jsonl`, and **stdout is reserved for the machine result** — piping `ezredis analyze --json` is never polluted by log noise. The run summary is produced whenever the run directory is writable, **even for a failed run**.

**B1/B2 stage contract (S0–S7 — parsing → IR, each separately testable).** **S0 discovery** (root → sorted path/size entries; no contents, no decode) · **S1 read** (entry → bytes + `content_hash` over exactly the bytes handed to the parser — the TOCTOU rule) · **S2 decode** (bytes → explicit encoding verdict; never a silent replacement character) · **S3 parse** (bytes, **not** decoded text → CST + `parse_status` + partial-parse ranges, so an undecodable file is still parseable) · **S4 extract** (CST → candidate facts; adapter types live only here) · **S5 normalise** (candidate facts → IR facts, each with one provenance and inline `unresolved`; a fact without provenance fails validation) · **S6 assemble** (per-file facts → one IR: merge, cross-file resolution, unresolved roll-up, total ordering) · **S7 persist** (IR → canonical JSON + emitted JSON Schema, atomic temp+rename). The "parse bytes, not text" choice at S3 is `[assumption]` about the py-tree-sitter binding.

**B1/B2 crossing rules (mechanical, not aspirational).** Adapters receive `bytes` + a frozen parse context and never read the filesystem, clock, environment, network or run directory (unit tests inject bytes and monkeypatch I/O to raise). No CST object is reachable from any IR field (`ir/**` must not import `tree_sitter`). Nothing tree-sitter-specific appears in the IR except byte ranges inside evidence. A language feature that cannot be represented becomes an `unresolved`, never a smuggled field.

### C.5 The four flows

**Flow 1 — full static analysis (zero network, zero AI).** CLI/library call validates arguments and creates a run directory with a run id and manifest → discovery writes a sorted path-only manifest → adapters parse each file and emit candidate IR nodes, each with provenance and explicit `unresolved` where the adapter cannot decide → IR assembly validates and merges into one IR, resolving cross-file references where the hand-built symbol index supports it and marking everything else `unresolved`; the IR is persisted so later phases and MCP read it without re-parsing → the analysis engine runs the rule registry in a fixed order, each rule reading IR facts only and emitting findings → the findings model attaches evidence items, an evidence class, severity and confidence as **separate axes**, limitations and unresolved lists → the recommendation layer groups findings by data flow, derives candidate patterns deterministically, applies compatibility policy in code, and emits recommendations with alternatives, trade-offs and uncertainty; insufficient evidence becomes a question, not a recommendation → document generators project IR+findings+recommendations into the applicable documents, every write through the boundary → the exporter writes canonical JSON (and optionally SARIF 2.1.0) → the library returns result objects and the CLI prints a summary and an exit code (non-zero only on error, never on "findings present").

**Flow 2 — incremental analysis (single changed file, ≤ 5 s target, unmeasured).** As Flow 1, but discovery is given a changed-file set (derived from `content_hash` against the manifest, never mtime), adapters re-parse only those files, IR assembly patches the persisted IR (operations, keys, TTLs, rate limiters, search and Iris usages are dropped and re-inserted; `cache_sites`, `invalidations` and `data_store_links` are rebuilt globally because they join across files), and only rules whose input slice changed plus cross-file rules are re-run. The **symbol-index rebuild is the identified risk** for the 5 s budget. Correctness is independent of speed: the patched result must be byte-identical to a full re-run (H.1a).

**Flow 3 — opt-in live-Redis inspection (network, no AI).** The operator explicitly enables the runtime module, supplies a named connection profile, and chooses an allowlist profile; the **default is disabled**. The inspector connects with TLS and username/password, issues `COMMAND` once and builds the effective policy from the reply, then requires every command to pass **both** axes; commands failing either axis are refused with a machine-readable refusal carrying its own `axis` and reason code. Diagnostic commands are reachable only from an explicit diagnostics sub-allowlist with per-command caps. Keyspace notifications are **consumed only if the operator already enabled them**; EZ-Redis never issues `CONFIG SET`. Runtime observations become `EvidenceItem(kind="runtime_metric")` attached to existing findings, promoting `evidence_class` to `combined`; they never create a claim the static analysis could not support.

**Flow 4 — optional AI path (Jev, then LangGraph).** Only if enabled and configured. Jev receives a **reduced evidence summary** built by deterministic code (bounded against the token/body ceilings), answers bounded questions over a **closed** pattern set, and EZ-Redis validates the response, discarding invalid or out-of-set answers; on any failure the deterministic recommendation path is returned — the fallback is the **default return value**, not an error path. All arithmetic, thresholds and comparisons stay in code. If the final gate passes, LangGraph orchestrates multi-step investigation and approval over the same core, may not bypass it, and keeps a bounded, inspectable run file. Repository content is untrusted **data** throughout: instructions found in an analysed README, comment or config value must never alter policy, prompts or thresholds.

**Synchrony.** All static work is synchronous and single-process; there is no queue, worker or distributed transaction. The run directory is the only state, written atomically per step; each step is idempotent given the same inputs and manifest, which is what makes the incremental path and the deterministic-output requirement testable.

### C.6 Analysis categories, rule families and assertion ceilings

A finding may only claim what static evidence supports. The **assertion ceiling** is a property of the rule *family*: the strongest honest claim it may make, given that the analysis is syntax-level with heuristics and a one-hop symbol index and has no server knowledge.

| # | Category | Family / rule ids (proposed) | Assertion ceiling (static) | Default evidence class | Phase |
|---|---|---|---|---|---|
| 1 | Missing/excessive TTLs | `ttl.*` | "no TTL-setting op reaches K on the analysed path"; "a literal TTL V exceeds the configured threshold T (T is config)" — **never** "this TTL is wrong for this data" | `static`; `needs_confirmation` from config/wrapper | P10 |
| 2 | Invalidation / stale risk | `inv.*` | "a write to S has **no resolved** invalidation link to K; `link_kind` is candidate/unresolved" — the **risk** is asserted, a stale value never | `static` (one scope) else `needs_confirmation` | P11 |
| 3 | Inconsistent cache-aside | `ca.*` | ordering **within one scope with resolved key identity**; a race is a **shape**, never an observed interleaving | `static`/`candidate` | P09 |
| 4 | Inefficient commands/structures | `cmd.*` | "`KEYS` is issued in application code"; "an unbounded structure read is issued on K" — a command shape, never a cost number | `static`/`candidate` | P14 |
| 5 | Serialization/payload | `ser.*` | "the whole object is rewritten where a partial-field structure exists in the same file" — **no byte-size claim** | `candidate` | P14 |
| 6 | Stampede/hot-key | `stamp.*` | "the read-miss-populate region has no single-flight/atomic mitigation"; "N sites share one TTL literal" — hotness never asserted | `static`/`needs_confirmation` | P12 |
| 7 | Unnecessary misses | `miss.*` | "template T is written but never read in this run"; "one entity cached under two templates" (the dedup claim is `candidate`) | `candidate` | P09/P11 |
| 8 | Memory/eviction | `mem.*` | "keys with no time bound and no resolved invalidation" — any magnitude requires P22 runtime data | `needs_confirmation` | P14 |
| 9 | Rate-limiting | `rl.*` | "increment and expiry are separate commands outside a transaction/script" — a **correctness** claim about the pattern | `static` | P12 |
| 10 | Redis Search/vector | `search.*` | consistency/omission between **two literal facts** in one run; **never** recall/latency/memory | `static`/`needs_confirmation` | P13 |
| 11 | Connections/transactions/pipelines | `conn.*` | "a client binding is constructed inside a per-iteration call site" (shape); "`group` is pipeline, not transaction, where the code depends on atomicity" | `static`/`candidate` | P14 |
| 12 | Application-level bottlenecks | **none — deliberate** | out of scope for static rules; every honest form is a question (workload/traffic/latency). Nearest static anchors are the `cmd.*`/`stamp.*`/`mem.*` shapes | `needs_confirmation` only | §C + P22 |
| 13 | Key naming/layout/cardinality | `key.*` | naming/layout claims about the **literal** template; cardinality only from a same-file enumerable literal set | `static`/`needs_confirmation` | P09 |

**Rule-id convention.** `<family>.<snake_case_rule>`, lowercase, stable forever, one rule per id, never a numeric suffix that encodes severity.

**Rule-family interaction and false-positive control.** `key.*` must **skip** every key referenced by a rate limiter (a per-identity dynamic segment is intended there); `ttl.missing`/`ttl.explicit_no_expiry` must not exceed `info` when a resolved invalidation link exists on the same key (delete-on-write is a legitimate strategy); `ttl.excessive` and `stamp.ttl_synchronized` may co-fire but must not duplicate the same evidence item; `search.no_pre_filter` must not fire when a filter is present; `mem.*` must cite the absence produced by the TTL/invalidation families rather than re-deriving it; severity is an axis and is never derived from `evidence_class`; one finding per `(rule_id, sorted location set)`.

**Statically derivable vs must become a question.** Derivable: that a command is issued (with a resolved binding); the canonical command name (literal); the literal key template; the TTL value (literal); read/write/invalidate ordering in one scope; index↔query consistency (both literals in one run). **Never derivable** (each becomes a `Question` on the recommendation record): key cardinality except from an in-file literal set; TTL appropriateness; that a race occurred; that a value is currently stale; hotness/stampede occurrence; a limiter's configured limit; which store is authoritative without a same-file link; `FT.HYBRID` availability; module command flags; whether notifications are enabled; **any performance or memory improvement**.

### C.7 The run directory is the only state

The run directory holds the manifest, the machine-readable summary, the append-only JSON event stream, the canonical IR, findings, recommendations and the generated documents. It is written atomically per stage (temp file + fsync + rename), so a reader sees either the previous stage's complete state or the next one's, never a torn file. Content hashes are authoritative; mtime is at most a fast-path hint. The proposed location is the **OS user cache directory** rather than `<workspace>/.ezredis/...`, which would pollute the analysed repository and confuse the write-boundary story (R-14; §E config model). A **SingleDecision** rule applies: if P23 later chooses a SQLite-backed index, SQLite replaces only the persisted symbol index and IR patch store — the manifest, summary and log stay JSON, so the diagnostics surface never depends on a database.

### C.8 Determinism — what "byte-identical" actually means

Every list has a **total order** with no ties (files by path in Unicode code-point order, no locale collation; operations by path, line, column, ordinal-within-span, id; unresolved by subject, kind, id; findings by severity rank desc, category, first-location path, line, id). Canonical serialisation is sorted-key JSON with a single trailing newline, stable under `PYTHONHASHSEED=0` and `1`. **No float appears in a sort key, an id derivation or a digest input.** No dict/set iteration produces output order, no filesystem walk order is relied upon, and there is no parallelism in v1.

**Fields excluded from the canonical comparison** `[proposed]` — without them "two runs are byte-identical" is unsatisfiable, because a run id must stay unique per run: the IR's `repo.generated_at`, every record's `provenance.run_id`, and the whole `manifest.json`. The declared volatile set for a determinism test is exactly: `run_id`, `started_at`, `updated_at`, `finished_at`, `duration_ms`, `environment`, `exit_code`, `seq`, `at`, `event_id`, `redactions_applied`. Declaring this set is what makes the determinism test decidable.

**Bounded memory.** At most one file's bytes and one CST are live at a time; the IR retains paths, hashes and spans but **no source text**; query matches are iterated lazily; memory is O(IR facts) + O(one file), with `max_ir_facts`/`max_ir_bytes` aborting via `limits_exceeded` rather than an out-of-memory kill; the sequential file loop is the backpressure.

## D. Component and Dependency Decisions

### D.1 Architecture decision records (ADRs)

Nine ADRs from `architecture.md` rev 2, each with the alternatives that were genuinely available. Source tags (`[S-n]`) refer to `research_summary.md`.

| ADR | Decision | Deciding facts | Rejected alternative (reason) |
|---|---|---|---|
| **ADR-1** Parser | **tree-sitter (core `>=0.25,<0.27`) + `tree-sitter-python` + `tree-sitter-javascript` + `tree-sitter-typescript` (both TS and TSX grammars)**; decision confirmed by four measurements at **P08** | wheel matrix covers cp310–cp314 for all three grammars on macOS arm64/x86_64 and Linux, MIT, no Rust needed, so A-1 holds; the ABI window (core ≥ 0.25 loads parser ABI 13–15) means the 0.23.2 TypeScript grammar (ABI 14) and the 0.25.0 Python/JS grammars (ABI 15) co-load; `tree-sitter-typescript` exposes **two** grammars, so one family covers JS/TS/TSX but **two parsers must be wired** (this resolves R-6); 0.26.0 **removed** `Language.version`, `Language.query()` and `*_timeout_micros`, so the adapter must target the 0.26 API or pin 0.25.x; grammar/core ABI drift has broken releases before, so a load smoke test is mandatory | LibCST 1.9 as primary (Python-only; its type inference requires a Pyre server plus watchman — operationally wrong for a CLI); TypeScript compiler API as primary (a Node subprocess plus an npm dependency for a gain only TS needs); `tree-sitter-language-pack` (third-party grammar bundling for no baseline capability); `tree-sitter-languages` (unmaintained); stdlib `ast` (retained internally as a fast prefilter only) |
| **ADR-2** Contract library | **pydantic v2 (`>=2.12,<3`)** for all boundary contracts; plain dataclasses for internal non-serialised objects | `mcp` 2.3.0 already requires `pydantic>=2.12`, so pydantic is a mandatory transitive dependency of the MCP phase regardless; pydantic v2 generates JSON Schema, which drives the MCP tool definitions; dataclasses have neither validation nor schema generation | msgspec (a second validator in the tree for no saving; retained only as a profiled-hotspot alternative — its vendor speed claims are **not verified here**); stdlib dataclasses; no validation |
| **ADR-3** Canonical output | **Bespoke pydantic JSON is canonical; SARIF 2.1.0 (+ Errata 01) is a secondary export only**, validated with `jsonschema` in tests | SARIF 2.1.0 is the current OASIS standard with no 2.x successor, and it carries locations/rule ids/levels but **cannot natively carry evidence graphs, confidence or `unresolved` semantics**; `sarif-om` 1.0.4 (2019) is effectively frozen and `sarif-tools` is a rendering CLI, not a validator | SARIF as canonical (loses fidelity); adopting `sarif-om` |
| **ADR-4** MCP surface | **stdio only; a capped surface (6 tools); documents as resources; zero prompts; no FastAPI** | the current MCP spec revision defines only stdio and Streamable HTTP and removed protocol-level sessions; workspace `.mcp.json` supports stdio and HTTP but **not SSE**, and `.vscode/mcp.json` is deprecated; VS Code Copilot enforces a hard **128-tool limit per request** including built-in tools; tool definitions cost model context every turn; FastAPI would add little dependency weight but a **second public surface** for a tool whose requirement is offline operation | SSE (legacy; unsupported in workspace `.mcp.json`); HTTP (adds auth/TLS/deployment for no slice need); FastAPI (recorded as a later candidate tied to a hosted/team mode); `generate_patch`/`validate_patch` (FR-22 excludes patch generation and verification entirely) |
| **ADR-5** RedisVL | **Excluded from the target slice** | RedisVL is an AI-native runtime client for vector search and RAG pipelines — not a static-analysis aid; EZ-Redis never needs to build or query a vector index to produce `REDIS-SEARCH.md` (it reads source) | including RedisVL (a runtime dependency for no analysis capability) |
| **ADR-6** Orchestration | **The deterministic orchestrator is the default and the only required path; LangGraph is the last phase, gated and droppable** | LangGraph's load-bearing features are durable resumable human approval across process restarts, bounded loops and persisted state; bounding and persistence are ~150 lines over pydantic plus a run directory, so only **cross-process resumable approval** justifies a checkpointing framework; adopting LangGraph pulls `langchain-core`, `langgraph-checkpoint*`, `langgraph-prebuilt`, `langgraph-sdk` and `xxhash`; `recursion_limit` defaults to 25 and exceeding it raises | adopting LangGraph by default (expensive dependency off the critical path); a hand-rolled agent loop (an irreversible bespoke state machine with no ecosystem) |
| **ADR-7** Domain knowledge | **Reuse `redis/agent-skills` (MIT) as the reference corpus**, pinned to a commit with attribution and the licence retained | it ships eight Agent-Skills-format skills covering `redis-core`, `redis-connections`, `redis-search`, `redis-semantic-cache`, `redis-security` and `iris-development` — maintainer-authored prose on exactly the four planned documents' subjects; `iris-development` explicitly scopes itself to Redis Agent Memory | re-deriving guidance in-house (duplication cost); official docs only (weaker coverage). **Disclosed gap:** **no rate-limiting skill exists**, so `RATE-LIMITING.md` must cite `redis-core`/`redis-connections` plus vendor command pages, and that gap is stated in the document itself (§F) |
| **ADR-8** Live-Redis policy | **Two-axis allowlist (`readonly` ∧ ¬`@dangerous`) + a runtime `COMMAND` cross-check; keyspace notifications are never enabled** | `KEYS` is `readonly` **and** `@dangerous` (O(N) over the whole keyspace), while `INFO`/`CLIENT LIST`/`SLOWLOG GET`/`LATENCY LATEST`/`CONFIG GET` do not mutate but carry `@admin`/`@dangerous`, and `INFO` has **no `readonly` flag at all** — so a category rule both over-permits and under-permits; `COMMAND` returns per-command flags and ACL categories, so the policy can be derived from and cross-checked against the live server; keyspace notifications are disabled by default and enabled via `CONFIG SET`, i.e. **enabling them is a configuration write** | "read-only commands only" as literally worded (wrong in both directions); an ACL category grant alone (`+@read`); assuming a modern server |
| **ADR-9** `IRIS.md` | **Generated conditionally on detection of IRIS / Agent Memory evidence and never emitted empty**; otherwise the run records an explicit "not applicable, with evidence" outcome and writes nothing | Iris is Redis's AI-product umbrella, materialised today as Redis Agent Memory (a store addressed by a store identifier plus a store API-key bearer credential); a randomly chosen analysed repository will almost never use it; the prompt forbids creating empty or irrelevant documents to satisfy a list | always emitting `IRIS.md` (an empty placeholder); never emitting it (loses the case where it applies) |

Two further choices are recorded here rather than as standalone ADRs: **`click` 8.5.0 for the CLI** (with `argparse` as the zero-dependency fallback), and **uv with `requires-python = ">=3.12,<3.14"` plus a universal `uv.lock`** synchronised by `uv sync --frozen` in CI.

### D.2 Parser decision detail — API-version tier and semantic-depth tier

**API-version tier.** Exactly **one** internal shim module may touch the py-tree-sitter API (it exposes `language_abi_version`, `make_query` and `parse_with_budget`), so a fallback to a 0.25.x pin is a one-module change. Adapters must not use the symbols 0.26.0 removed (`Language.version`, `Language.query()`, `*_timeout_micros`). The load smoke test must show all four languages loading with `abi_version ≤ 15`, a one-line query compiling, and a one-line parse producing a root without an error node. Fallback triggers: a grammar fails to load, `abi_version > 15`, or the shim cannot express the parse budget on 0.26.

| Question about a call site | tree-sitter CST (baseline) | + hand-built symbol index | LibCST tier (Python only) | TS compiler API (TS/TSX) |
|---|---|---|---|---|
| Redis-looking command token; arity; literal TTL; pipeline/transaction shape | yes | yes | yes | yes |
| Literal key prefix / full literal key | yes | yes | yes | yes |
| Import alias or constructor binding for a receiver | naming convention only | yes (in-workspace) | yes | yes |
| Receivers injected by a framework/DI; types | no | no | **no** (needs a Pyre server + watchman) | yes |
| Key built from a runtime value beyond a literal prefix | no | no | no | partially |
| Decorator / wrapper semantics | naming convention only | one hop | one hop | yes |
| Cross-file data flow | no | one hop via the index | one hop | yes |

**Honest baseline claim:** *syntax + heuristics + a one-hop symbol index*; anything beyond it is an `unresolved`, never a resolved fact. Raising a tier changes the adapter's declared `api_tier` and is recorded at P08.

### D.3 The MCP surface decision (D-MCP-1…D-MCP-6)

| ID | Decision | Deciding facts | Rejected alternative (reason) |
|---|---|---|---|
| **D-MCP-1** | **Six tools, fixed and frozen in the slice** | the 128-tool per-request cap includes built-in extension tools, and large servers are deferred behind `activate_*` stubs; 6 of 128 leaves room for language servers and built-ins | one tool per rule (virtualisation pressure); one mega-tool with a `kind` switch (loses per-tool schema validation and discoverability) |
| **D-MCP-2** | **Documents are MCP resources, never tools** | the four documents are read-only, argument-free, side-effect-free context; resources add no per-turn invocation surface; `resources/list` is non-varying per connection in the current spec revision | a `generate_documents` tool (writes inside a tool call; duplicates `analyze_project(write_documents=true)`); a `get_document(name)` tool (resources already express a parameterised read) |
| **D-MCP-3** | **stdio is the only transport in the slice** | the current spec revision defines only stdio and Streamable HTTP and removed protocol-level sessions; the SDK still speaks SSE for compatibility but the spec no longer uses it for deployment | SSE (unsupported in workspace `.mcp.json`); HTTP (adds auth/TLS/deployment) |
| **D-MCP-4** | **Zero MCP prompts** in the slice | a prompt is a tool-shaped surface with the same per-turn context cost and no coverage in any contract; nothing in the requirements needs one | a slash-command prompt per document (surface without a contract) |
| **D-MCP-5** | **Config target is workspace `.mcp.json`**; `.vscode/mcp.json` is documented as deprecated | the client reads workspace `.mcp.json` directly; `.vscode/mcp.json` is listed among deprecated destinations and the agent does not read it directly | documenting `.vscode/mcp.json`; a per-user config (not shareable) |
| **D-MCP-6** | **Tool-definition cost is a first-class cap driver** | tool definitions are model context carried on every turn, so surface size trades directly against model budget; consolidation (`analyze_project` with a `scope` parameter rather than five analysis tools) is the lever | no cap (context growth per turn); ultra-fine tools |

**Surface budget.** tools **6** of the 128-per-request cap shared with built-in tools · resources **1 template → 3–4 documents per run** · prompts **0** · transports **1 (stdio)**. **No token count is claimed** — none was measured.

**What a real client does (stated, not assumed).** Workspace `.mcp.json` supports stdio and HTTP servers; SSE, working directory, environment files and IDE input variables are **not** supported there, so the config example must use a stdio `command`/`args` pair and must not rely on a working directory or `.env`. The client may ask the user to **confirm each tool invocation**; with sandboxing enabled local stdio calls are auto-approved, and sandboxing is **not available on Windows**. Workspace MCP servers **inherit Workspace Trust**: in restricted mode workspace MCP configuration is blocked and the server does not start — so "server not started → check Workspace Trust" is the first troubleshooting step.

### D.4 Domain-knowledge ADRs (ADR-D1…ADR-D7)

| ID | Decision | Deciding facts | Consequence / risk |
|---|---|---|---|
| **ADR-D1** Domain guidance source | Use `redis/agent-skills` (MIT), pinned and attributed, cited per generated section | eight MIT skills in Agent-Skills format cover exactly the document subjects; **no rate-limiting skill exists** | the corpus is generic maintainer prose, so a document can degrade into restated advice. Mitigation: every section is evidence-linked and omitted when unevidenced (§F). Disclosed gap: `RATE-LIMITING.md` cites `redis-core`/`redis-connections` + vendor command pages |
| **ADR-D2** Assertion ceiling per rule family | Family-level ceilings as §C.6 (13 families) | the ≥ 90 % bar is measured per **rule** (P24 labels per rule), but the ceiling is a **family** property | a new rule must declare its family and cannot exceed the ceiling |
| **ADR-D3** No threshold value enters the plan or a rule from a model | Numeric thresholds exist only as labelled config defaults computed in code | a model's confidence score must not substitute for measured correctness, and the model is not a calculator | every threshold (an excessive-TTL threshold, an avalanche site count) is surfaced as an `[assumption]` in the finding text and the document, never as a fact |
| **ADR-D4** Version-/module-dependent semantics leave the static path | Treat every version-dependent behaviour as a `needs_confirmation` question | the tool has no server knowledge statically (FR-19), the target version is unknown, and some commands need a specific server version | some rules can never reach `resolved` without P22 — the honest outcome, recorded as a limitation |
| **ADR-D5** Which live commands the Redis domain justifies | A minimal set behind the diagnostics profile: `SCAN` (cursor-bounded, capped), `TYPE`, `TTL`/`PTTL`, `MEMORY USAGE` (capped samples), `OBJECT ENCODING`, `INFO`, `SLOWLOG GET` (capped), `LATENCY LATEST` | statically unanswerable questions are key-space size, memory per key, eviction policy, a live key's TTL and notification state | each is gated by the two-axis policy and refused with a reason code; `KEYS` stays denied in favour of `SCAN`; module commands are deny-by-default pending confirmation |
| **ADR-D6** Documents are projections, not advice generators | Each document cites the IR/finding ids it was derived from and has mandatory "not established" sections | the write boundary permits only generated files, and a document stating an unevidenced recommendation is indistinguishable from a model answer | documents are longer and less chatty; a document with nothing to report is **not generated** |
| **ADR-D7** The tool never asserts an application's failure mode from its shape alone | Assert fail-open/fail-closed only when an explicit fallback path is in the same scope | cache-down behaviour is a stated design choice or an accident, and only the latter is visible in code shapes | most caches report "failure behaviour: not established" — the honest value, which must not read as an omission |

### D.5 Dependency inventory, groups and compatibility constraints

**Python baseline (FR-25 / AC-19).** `requires-python = ">=3.12,<3.14"` managed with **uv** and a **universal `uv.lock`**; CI runs `uv sync --frozen`, lint, types and tests on **Python 3.12 and 3.13 explicitly**. The locally installed **3.14 interpreter is explicitly not the baseline** and must not float into CI: 3.12 and 3.13 are pinned deliberately because their support windows are long (both are security-only for part of their life, with end-of-life dates far out), and floating to the newest interpreter would trade reproducibility for novelty.

**Dependency groups (FR-27 / AC-21).**

| Group | Package | Purpose | Compatibility / note |
|---|---|---|---|
| **core (mandatory)** | `tree-sitter >=0.25,<0.27` | the one traversal model for all four languages | ABI window 13–15; 0.26.0 API changes documented (ADR-1) |
| **core** | `tree-sitter-python` 0.25.0 · `tree-sitter-javascript` 0.25.0 · `tree-sitter-typescript` 0.23.2 | grammar wheels; TS and TSX are two grammars in the one TypeScript package | MIT; abi3 wheels for cp312/cp313; no Rust toolchain |
| **core** | `pydantic >=2.12,<3` | validated, JSON-Schema-bearing contracts | also required transitively by `mcp` (ADR-2) |
| **core** | `click` 8.5.0 | CLI entry point | `argparse` is the zero-dependency fallback |
| **optional `mcp`** | `mcp` 2.3.0 | MCP server over stdio | MIT; pulls `starlette`/`uvicorn`/`httpx`/`jsonschema` and a CLI extra, which is why it is **not** in core |
| **optional `agent`** | `langgraph` + a SQLite checkpoint package | the droppable orchestrator | large transitive tree; **default is not adopted** (ADR-6) |
| **optional `telemetry`** | *(none)* | reserved and empty | there is no collector, so this group must not be filled speculatively (FR-19) |
| **dev** | `pytest`, `hypothesis`, `ruff`, `mypy`, `jsonschema` 4.26.0, coverage | tests, property tests, lint, types, schema validation | dev-only. `pytest-timeout` and a fake-clock library are **not yet in the approved set** — `[unresolved]`, requested before P26 |
| **excluded** | RedisVL · FastAPI · `sarif-om`/`sarif-tools` · `tree-sitter-languages` · `tree-sitter-language-pack` · `pylint`/`astroid` | — | ADR-3/ADR-5/ADR-1/ADR-7; `astroid` is LGPL and must not enter a distributed tool |

**Supply-chain and licence triage.** The review is recorded at P26; **no audit tool has been run here**. The facts below are research findings to be re-verified at the pinned versions in P26 (`[unresolved]`). `tree-sitter` + grammars, `pydantic`, `click`, `redis-py`, `mcp`, `langgraph`, `jsonschema`, `pytest`, `hypothesis`, `ruff`, `mypy` are permissive with no recorded advisory at the evaluated versions. Two flags matter: **`libcst`'s licence metadata is inconsistent** across registries, so the actual `LICENSE` must be read before any adoption and "unknown" is treated as unresolved, **not** permissive; and **`astroid` (which arrives with `pylint`) is LGPL-2.1-or-later**, so `pylint`/`astroid` must not be added to any group. Triage rules: any advisory in the shipped set blocks the phase gate until upgraded or removed; any obligation-bearing licence needs a recorded legal decision (attribution is not a substitute); inconsistent licence metadata means "read the actual LICENSE"; an unpinned or non-locked install is prohibited (`uv sync --frozen` against a committed lock); and a version without a published attestation is a recorded note, not a block.

## E. Data Contracts and Interfaces

Section E carries the **four field-level contracts** (the shared Redis IR, the finding record, the MCP tool input/output contract, the recommendation record) **and five interface-level specifications** (the adapter→IR interface, the pure rule interface, the configuration model, the run manifest / run-directory contract, and the error and reason-code catalogue). No tenth schema is introduced: component sub-objects such as `Page`, `EvidenceItem` and `RunSummary` are **fields of** these nine interfaces, not new interfaces. **No algorithm and no per-rule pseudocode appears anywhere** in this section (FR-14 rev 2 / AC-10(d)); interface signatures without bodies, directory-layout illustrations and configuration illustrations are the permitted forms.

**Plumbing rules that bind every contract.** pydantic v2 models (ADR-2); `snake_case` field names; RFC 3339 UTC timestamps with `Z`; durations in **integer milliseconds**; **no floats** in ids, sort keys or digests; ids are opaque strings matching a lowercase-prefixed hex shape; every contract carries a `schema_version` (semver, additive-only within a major, removing a field or reusing a code name requires a new major); an unknown config key is a hard error (`extra="forbid"`, `frozen=True`). **Excluded from every canonical digest:** the IR's `repo.generated_at`, every record's `provenance.run_id`, and the whole `manifest.json` (§C.8).

### E.1 Field-level contract 1 — Shared Redis IR (P03)

The single load-bearing contract. Top-level sections: `schema_version`, `repo`, `files`, `clients`, `operations` (each with `key: KeyExpr`), `ttl_policies`, `cache_sites`, `invalidations`, `rate_limiters`, `search_usages`, `iris_usages`, `data_store_links`, `unresolved`, plus the shared `AnalysisProvenance`, `FileSpan`, `EvidenceItem` and `ConfigRef` objects.

| Element | Type | Invariant |
|---|---|---|
| `files[]` | `SourceFile{path, language, parse_status, encoding, content_hash, size_bytes}` | `language ∈ {python, javascript, typescript, tsx}`; `parse_status ∈ {parsed, partial, failed, skipped}`; **no `text` and no `bytes`** — the IR never retains source |
| `clients[]` | `RedisClientBinding{client_id, language, library, binding_kind, provenance}` | `binding_kind ∈ {constructor, module_singleton, injection, wrapper, unknown}`; a `wrapper`/`unknown` binding is **never asserted** as a Redis client |
| `operations[]` | `RedisOperation{op_id, client_ref, command, command_source, data_structure, key, is_read, is_write, ttl_ref, location, group, atomic_group, provenance}` | `command` is canonical upper-case (`"UNKNOWN"` permitted); `command_source ∈ {literal, fstring_prefix, variable, unknown}`; `group ∈ {single, pipeline, transaction, script}`; **`atomic_group: bool \| null`** distinguishes a plain pipeline (not atomic) from `MULTI/EXEC` and a script (atomic) — without it the flagship rate-limiting rule must downgrade to `needs_confirmation` |
| `KeyExpr` | `{raw_expr, pattern, segments[], is_literal, literal_prefix, literal_suffix, segment_count, dynamic_segment_count, cardinality_class, cardinality_basis, match_norm, unresolved[]}` | `pattern` is literal text with one `{}` per dynamic/unknown segment in source order, literal braces escaped so rendering is injective; `segments` is source-ordered and **never sorted**, each `{kind ∈ literal\|dynamic\|unknown, value, dynamic_kind}`; **`dynamic_kind ∈ {variable, fstring_expr, function_call, template_placeholder, concat, unknown}`**; `literal_prefix`/`literal_suffix` are the longest leading/trailing literal runs, with `""` = "ends dynamic" and `null` = "unknown" (three distinct cases); **`cardinality_basis ∈ {literal_only, enumerable_literal_set, datastore_identity, time_bucket, runtime_value, unknown}`**; `match_norm` is a casefolded matching key, for matching only, never displayed or used to reconstruct |
| `ttl_policies[]` | `TtlPolicy{ttl_ref, op_ref, seconds, source, ttl_form, provenance}` | `seconds = null` means explicit no-expiry; `source ∈ {literal, config, inferred, absent}`; **`ttl_form ∈ {set_ex, set_px, set_exat, set_keepttl, expire, pexpire, expireat, persist, none, unknown}`** distinguishes "no TTL argument" (Redis default = no expiry) from `KEEPTTL` (TTL inherited → **unknown**) from `PERSIST` |
| `cache_sites[]` | `CacheSite{site_id, pattern_kind, read_ops[], write_ops[], invalidation_ops[], authoritative_source, provenance}` | `pattern_kind ∈ {cache_aside, read_through, write_through, write_behind, prefetch, manual, unknown}`; `authoritative_source` is best-effort |
| `invalidations[]` | `InvalidationLink{from_op, to_keys[], mechanism, link_kind, provenance}` | `mechanism ∈ {delete, expire, overwrite, pubsub, unknown}`; `link_kind ∈ {resolved, candidate, unresolved}`; a `pubsub` link is `candidate` **at best**, never `resolved` (delivery is fire-and-forget and lost while disconnected) |
| `AnalysisProvenance.level` | `enum {syntax, resolved, inferred, runtime}` | `syntax` = read off the CST (receiver identity not certain); `resolved` = confirmed by a mechanism the tool owns **and can cite**; `inferred` = a heuristic that can be wrong; `runtime` = a P22 observation only. The static pipeline **never** emits `runtime`; only `resolved` may carry a defect without a caveat |
| `Unresolved` | `{unresolved_id, subject_ref, kind, reason, impact, blocking, evidence[]}` | `unresolved_id` is a content hash of `(subject_ref, kind, reason, sorted evidence refs)`; **`impact ∈ {changes_verdict, degrades_confidence, informational}`** and `blocking = (impact == "changes_verdict")`. This makes the "unresolved downgrades a defect to a question" rule mechanical: a finding supported by a fact with `impact="changes_verdict"` **must** be `needs_confirmation` |
| `Unresolved.kind` | `enum {dynamic_key, unknown_client, wrapper_indirection, cross_file_flow, unsupported_syntax, parse_failure, oversize, binary_content, encoding_undecodable, encoding_unsupported, parse_budget_exceeded}` | the last five are additive `[proposed]` values that currently map to no existing kind; if refused, `oversize`/`binary_content` collapse into `parse_failure` and that collapse is stated |
| `unresolved` carriage | inline `fact.unresolved[]` + a global `RedisIR.unresolved[]` **roll-up** | the roll-up is the **union**; a validator asserts roll-up ⊇ the flattened inline set by `subject_ref`; the roll-up is the only source of `counts.unresolved_by_kind` |
| `EvidenceItem` | `{kind ∈ source_span\|ir_fact\|absence\|runtime_metric, ref, note}` | **`absence`** (with `ref = "<subject_ref>#<predicate>"`) is what lets a rule cite a *negative* fact — no TTL op on K, no invalidation link, no lock in the populate region — without inventing a location; without it the strongest honest findings become unrepresentable and the "no finding without evidence" invariant would force weaker wording |
| `ConfigRef` | `{path, symbol, redacted}` | a secret is referenced with `redacted=true` and its **value is never stored** (I-S1) |
| Round-trip invariant | — | for an all-literal key `k`: `pattern == k`, `is_literal`, `render(segments) == pattern`, counts conserved |
| Total order (every list) | — | no ties, no locale collation, no dict/set iteration, no filesystem-walk order, no parallelism in v1 (§C.8) |

**Load-bearing IR invariants:** (a) no adapter types; (b) provenance on every fact; (c) `unresolved` is first-class and never inferred away; (d) deterministic ordering (byte-identical modulo the documented exclusions).

### E.2 Field-level contract 2 — Finding record (P04)

Fields: `finding_id`, `rule_id`, `category`, `severity`, `evidence_class`, `confidence`, `locations[]`, `evidence[]`, `affected_operations[]`, `limitations[]`, `unresolved[]`, `recommendation_ref`, `provenance`.

| Element | Rule |
|---|---|
| `evidence_class ∈ {static, runtime, combined, needs_confirmation}` | `needs_confirmation` is **required** whenever a supporting fact is `unresolved` with `impact="changes_verdict"` |
| `severity ∈ {info, low, medium, high}` vs `confidence{score, basis, limits}` | **separate axes, contractually**: severity is never derived from confidence, and a rule may not improve a measured precision by down-grading severity |
| `provenance{ir_schema_version, analyzer_version, run_id, rule_version}` | present on every finding; `run_id` is **excluded from the digest** |
| `finding_id` | a content hash; stable under reordering; dedup is one finding per `(rule_id, sorted location set)` |
| ≥ 1 evidence item | a rule that cannot cite at least one evidence item must not emit |
| No numeric performance claim | no latency/memory/hit-rate improvement figure may appear in a finding, a document or the CLI summary — only in a P25 measurement |
| Total order | `severity_rank desc (high>medium>low>info)`, `category asc`, `locations[0].path asc`, `locations[0].start_line asc`, `finding_id asc` |

### E.3 Field-level contract 3 — MCP tool input/output (P20)

Transport **stdio only** (ADR-4); surface **6 tools**, documents as **resources** (not tools), **zero prompts**. Every tool's input/output models are pydantic v2; the published JSON Schema is produced by the model generator, never hand-authored, so tool definitions and library types cannot drift.

**Envelope.** `ToolResult{ok: bool, data | problem, schema_version}` — `ok=true` implies `data` present and `problem` null; `ok=false` implies `problem` present and `data` null. `Problem` follows RFC 9457 with the standard members `type` (URI), `title`, `status` (HTTP-analogue integer), `detail` (non-leaking), `instance` (URI) plus the extension member **`code`** — the closed enum clients branch on — and an optional `run_id`. The envelope's shape, as generated schema:

```json
{"$defs":{"ToolResult":{"type":"object","additionalProperties":false,
  "required":["ok","schema_version"],"properties":{
    "ok":{"type":"boolean"},"data":{"type":["object","null"]},
    "problem":{"$ref":"#/$defs/Problem"},"schema_version":{"type":"string"}},
  "oneOf":[
    {"required":["data"],"properties":{"ok":{"const":true},"data":{"type":"object"},"problem":{"type":"null"}}},
    {"required":["problem"],"properties":{"ok":{"const":false},"data":{"type":"null"},"problem":{"$ref":"#/$defs/Problem"}}}]},
 "Problem":{"type":"object","additionalProperties":false,
  "required":["type","title","status","detail","code","instance"],"properties":{
    "type":{"type":"string","format":"uri"},"title":{"type":"string"},
    "status":{"type":"integer","minimum":400,"maximum":599},"detail":{"type":"string"},
    "code":{"enum":["validation_error","not_found","permission_denied","unsafe_command_refused",
                    "runtime_disabled","runtime_unavailable","run_expired","limits_exceeded",
                    "run_in_progress","resume_conflict","ir_schema_mismatch"]},
    "instance":{"type":"string","format":"uri"},"run_id":{"type":["string","null"]}}}}}
```

**The 11-code catalogue** (closed; a 12th code needs a contract revision). The three codes sharing status 409 have three different remedies — wait, discard, rebuild — which is precisely why `code`, not `status`, is the field clients branch on.

| `code` | HTTP analogue | Raised when | Retryable |
|---|---|---|---|
| `validation_error` | 400 | malformed/unknown parameter, bad enum, out-of-range limit, unparseable or foreign cursor, a rejected filter value | no |
| `not_found` | 404 | a `finding_id` not in the named run; a run that never existed in this workspace; an unknown `view` | no |
| `permission_denied` | 403 | a `path` resolving outside the workspace root; `write_documents=true` while the write boundary refuses the target | no |
| `unsafe_command_refused` | 403 | the two-axis Redis gate refused the request's *candidate command set* at policy level (distinct from `permission_denied` so a client can tell operator policy from its own path/permission) | no |
| `runtime_disabled` | **412** | live inspection is not configured/enabled — the **default state**; the server precondition is unmet, not the caller's privilege | no (needs operator opt-in) |
| `runtime_unavailable` | 503 | live inspection **is** enabled but Redis is unreachable / TLS / auth failed, or `COMMAND` could not be issued | yes (bounded) |
| `run_expired` | **410** | the named run existed and its run directory was purged/aged out — deliberately not `not_found`, because the remedy differs (re-run vs fix the id) | no |
| `limits_exceeded` | 429 | a configured file/size cap, a `SCAN` iteration cap, a `SLOWLOG`/`MEMORY USAGE`/`observations` cap, or a page limit above max — the cap is **named** in `detail` | yes (narrow the request) |
| `run_in_progress` | 409 | a run for this workspace is being written and the caller asked to read or resume it | yes (after the writer finishes) |
| `resume_conflict` | 409 | an incremental resume whose arguments (workspace root, languages, config digest) differ from the existing run's manifest | no (re-run full or discard) |
| `ir_schema_mismatch` | 409 | the persisted IR's `schema_version` differs from the running analyser's; the cached IR is stale and must be rebuilt rather than read | no (re-run full) |

**The six tools (input → `data` payload).** **T1 `analyze_project`** — `{path (workspace-confined), scope: full|incremental = full, languages? = all, include_runtime? = false, write_documents? = false}` → `{run_id, summary: RunSummary, diagnostics[]}`; the only tool with side effects, and only through the write boundary. `include_runtime=true` with runtime unconfigured proceeds static-only and reports a diagnostic — it does not fail the run. **T2 `list_findings`** — `{run_id, category?, min_confidence?, severity?, evidence_class?, limit? (default 50, max 200), cursor?}` → `{findings: FindingSummary[], page}`; filtered on `confidence.score`, never on `severity`. **T3 `explain_finding`** — `{finding_id, include_recommendation? = true}` → `{run_id, finding, evidence[] (≥1), rationale, alternatives[], limitations[], unresolved[]}`; the only tool keyed by `finding_id`. **T4 `recommend_caching_pattern`** — `{run_id, op_ids?, max_recommendations? = 5 (max 20)}` → `{recommendations[], questions[], truncated}`; `questions` is **not** an error channel — insufficient evidence yields a question, never a recommendation. **T5 `inspect_redis_usage`** — `{run_id, view ∈ {clients, keys, ttl, invalidation, rate_limiting, search, iris}, limit?, cursor?}` → `{view, summary{count, iris_applicable, unresolved_count}, items[], page}`; a **static IR projection** (no socket) — one tool with seven views rather than seven tools. **T6 `inspect_runtime_metrics`** — `{connection_ref (a **named profile**, never a URL), diagnostics? = false, caps{scan_max_iterations, slowlog_count, memory_samples}?}` → `{observations[], refused[{command, axis, reason}], observed_at, source: "live", applied_caps}`; the only network-touching tool, opt-in, disabled by default.

**Pagination and fixed sort order.** `cursor` is **opaque** (clients must not parse or construct it); its payload is base64url of a canonical tuple of `(collection, run_id, filter_digest, schema_version, last_sort_key)`; an invalid, filter-mismatching or foreign cursor is `validation_error`; a cursor whose run was purged is `run_expired`; `next_cursor` is `null` on the last page and never an empty string. Pages are stable for a fixed `run_id` because runs are immutable once finalised. **No client-chosen sort is exposed** — the fixed total orders are: findings by severity rank desc, category, first-location path, line, id; the IR projection by the per-view key then item id; recommendations by id; runtime observations by command, key pattern, ref.

**Workspace path confinement (W1–W6).** **W1** `path` is accepted workspace-relative or absolute **inside** the root, and the response always reports the workspace-relative form. **W2** resolution is `realpath`-based then prefix-checked; `..` segments, symlinks escaping the root, `/`, `$HOME`, UNC paths and non-`file` schemes are refused. **W3** a non-existent or non-source path is `validation_error`, while a path outside the root is `permission_denied` — the distinction matters for the client's remedy. **W4** file/size caps are configuration and exceeding them is `limits_exceeded` with the cap named. **W5** no response echoes an absolute host path, and the IR's confinement root is never returned. **W6** `inspect_runtime_metrics` takes a **named profile**, never a URL/hostname/credential, so no connection detail can be injected through the tool surface.

**Determinism per `run_id` (D1–D6).** **D1** `run_id` is a deterministic content hash over the workspace root, manifest content hashes, tool version, IR schema version, scope and config digest — **no wall-clock in the id**. **D2** for a fixed `run_id` the same call with the same parameters returns byte-identical output across processes and machines. **D3** no response contains wall-clock or host-dependent values. **D4** document listings are ordered `CACHING.md`, `RATE-LIMITING.md`, `REDIS-SEARCH.md`, `IRIS.md`, present only when applicable. **D5 carve-out** — `inspect_runtime_metrics` observes live state and therefore **cannot** be reproducible; its response carries `observed_at` and `source="live"`, and it is deterministic again only once persisted as runtime evidence. The architecture's "same `run_id` ⇒ same bytes" therefore applies to the five static tools and to persisted runtime evidence, not to a fresh live observation. **D6** `run_summary.json` in the run directory is the single machine-readable truth; the MCP `summary` is a **strict, identically-named subset** of it, with timing and exit code **excluded from tool responses** (so D2/D3 hold) and reachable as a resource.

**No-mutation invariant (N1–N6).** **N1** no tool mutates Redis data or configuration (EZ-Redis never issues `CONFIG SET` and never enables keyspace notifications). **N2** no tool modifies an existing repository file — the only writes are EZ-Redis-generated documents, reached solely via `analyze_project(write_documents=true)` and accepted solely by the write boundary. **N3** tools never write outside the run directory; run writes are atomic and a run is immutable once finalised. **N4** a refused write is reported and is **not an error**: the run succeeds and the summary omits the document from the generated list. **N5** every tool is idempotent in the sense that repeating it changes no input and no state, except a first-time run creation and document regeneration through the boundary. **N6** no tool returns patch text and no patch tool exists.

**Resources.** URI template `ezredis://run/{run_id}/documents/{name}` with `name` one of the four documents; `resources/list` returns 3 documents, or 4 when Iris usage is detected, and **`IRIS.md` is absent — never empty — when not applicable**; MIME `text/markdown; charset=utf-8`; each document body begins with the generated-file marker (IR schema version, analyser version, run id, source hashes) — the same marker the write boundary uses to decide overwrite-vs-refuse. When Iris is not detected the run reports "not applicable, with evidence" through `analyze_project.diagnostics`; no resource and no file exist. A second resource `ezredis://run/{run_id}/run_summary.json` exposes the full run summary including the timing fields withheld from tool responses.

**CLI / library / MCP parity (R-B6-4).** `analyze_project` ↔ `analyze(...)` ↔ `ezredis analyze <path> [--incremental] [--write-documents]`; `list_findings` ↔ `list_findings(...)` ↔ `ezredis findings <run_id> …`; `explain_finding` ↔ `explain_finding(...)` ↔ `ezredis explain <finding_id>`; `recommend_caching_pattern` ↔ `recommend(...)` ↔ `ezredis recommend <run_id>`; `inspect_redis_usage` ↔ an IR projection helper ↔ `ezredis inspect-usage <run_id> --view <v>`; `inspect_runtime_metrics` ↔ `inspect_runtime(...)` ↔ `ezredis inspect-runtime --profile <name>`. Also `generate_documents(run_id)` is reachable by CLI and library but is exposed over MCP as **resources, not a tool** — the single documented parity exception.

**`runtime_disabled` vs `run_expired`.** `runtime_disabled` (412) is **static configuration and the default state**: no connection attempt is made and no credential is touched, and static analysis stays fully usable. `run_expired` (410) means the run existed and was purged or is unreadable, as opposed to `not_found` (never existed here, or malformed). Run-directory retention is configuration and belongs to the run-manifest contract — `[unresolved]`, default: keep runs until an explicit purge.

### E.4 Interface-level spec 1 — adapter → IR (P06/P07)

Signature: `parse(path: str, source: bytes, ctx: ParseContext) -> AdapterResult` — **pure**; the same `(source, ctx)` yields a byte-identical result. `AdapterResult{language, path, content_hash, encoding, text_available, parse_status, partial_parse_ranges[], byte_offsets_transcoded, capabilities, facts[], diagnostics[], unresolved[], adapter_version, schema_version}`.

| Element | Type | Invariant / meaning |
|---|---|---|
| `content_hash` | `str` | sha256 hex over the **bytes parsed** — the identity of the parse, which makes the read TOCTOU-safe |
| `encoding` | `enum {utf8, utf8_bom, utf16_le, utf16_be, non_utf8, binary, unknown}` | explicit verdict; `text_available=false` means decoding failed but bytes were still parsed, so text heuristics degrade |
| `parse_status` | `enum {parsed, partial, failed, skipped}` | `skipped` = a policy decision; `failed` = an I/O or parse-level failure |
| `partial_parse_ranges[]` | byte ranges of error/missing subtrees | empty iff `parsed` |
| `byte_offsets_transcoded` | `bool` | true only when UTF-16 was transcoded before parsing; spans are then transcode-relative and this is stated in the run summary |
| `capabilities` | `AdapterCapabilities{language_ids, dialects, api_tier, resolves, never_resolves, unresolved_kinds, grammar[]}` | **the tier is data, not prose**: `api_tier ∈ {cst, cst_plus_index, type_aware}`; `dialects` must declare both `typescript` and `tsx`; `never_resolves` is the honesty list; `grammar[]` carries `{name, version, abi_version}` per wired grammar. The P08 harness fails if a fact claims an undeclared capability, and the union of both adapters' `unresolved_kinds` must cover every `never_resolves` capability |
| `facts[]` | local facts with local ids | global identity is assigned by the assembler |

**Deterministic fact identity.** local id = sha256 of `(path, start_byte, end_byte, kind, ordinal_within_span)`; global `op_id` = sha256 of `(path, start_byte, end_byte, command, ordinal_within_span)`; `client_id` = sha256 of `(binding_path, binding_symbol_name)`. `ordinal_within_span` is the 0-based index among facts sharing that exact byte span, ordered by kind then source position. **No counters, no hash-object iteration, no randomness** — this is what fixes "two facts at one span still need stable ids".

### E.5 Interface-level spec 2 — the rule interface (P05, P09–P14)

Signature: `Rule.evaluate(ir: RedisIR, config: RuleConfig) -> list[Finding]` — **pure**; no I/O, clock, environment, randomness or logging side effect.

| Element | Type | Invariant / meaning |
|---|---|---|
| `rule_id` / `rule_version` | `str` | `rule_id` matches a stable two-letter-plus-three-digit shape, one rule per id (the corpus labels per rule); a behaviour change bumps `rule_version` and forces a full re-run |
| `category` / `severity_default` | enum | severity is a default only and is never derived from confidence |
| `input_slices` | `frozenset[IRSectionName]` | the IR sections the rule reads; the incremental path re-runs `{r : r.cross_file} ∪ {r : r.input_slices ∩ changed_sections ≠ ∅}` |
| `cross_file` | `bool` | whether the rule depends on cross-file joins |
| `requires_config` | `frozenset[str]` | names the config fields it reads |
| `requires_provenance` | provenance level or null | below it a finding must be `needs_confirmation`, not a defect |
| Registry | `RULES: tuple[Rule, ...]` in **one** single-owner shared module | a **tuple literal**, never a dict or set; declaration order is the deterministic secondary sort key. P09–P14 must not be parallelised across two rule authors editing the registry |

**Rule-side invariants** (each has a test): purity and purity of timing (same `(ir, config)` twice ⇒ identical findings and ids; durations are recorded only in the run log, never inside a finding, so byte-stability holds); no I/O and no mutation (monkeypatched `open`/socket/environment raise; IR models are frozen); ≥ 1 evidence item or no emit; every `affected_operations` id resolves inside the same IR; no numeric performance claim; a raising rule is isolated (recorded as a diagnostic, the run continues) and its exception message never enters output text.

The **assertion ceilings** for the rule families are in §C.6 — the rule contract here is the seam, the ceiling is the family's honest limit.

### E.6 Interface-level spec 3 — configuration model with defaults

| Field | Type | Default | Note |
|---|---|---|---|
| `languages` | `list[LanguageId]` | `["python","javascript","typescript","tsx"]` | empty is a validation error |
| `ignore_globs` | `list[str]` | `.git/** .venv/** node_modules/** **/__pycache__/** dist/** build/** htmlcov/**` | plus `.gitignore` honouring; POSIX globs on workspace-relative paths |
| `follow_symlinks` | `bool` | `False` | `True` requires every resolved target to stay inside the workspace root |
| `max_file_bytes` | `int` | `5_242_880` (5 MiB) | checked by `stat` **before** reading; exceeded ⇒ `skipped` with reason `oversize` |
| `max_files` / `max_total_bytes` | `int` | `50_000` / `2_147_483_648` | exceeded ⇒ abort with `limits_exceeded`, never a silent truncation |
| `parse_budget_ms_per_file` | `int` | `10_000` | exceeded ⇒ `partial` + a reason code |
| `encoding_policy` / `binary_policy` | `strict\|transcode` / `skip\|attempt` | `strict` / `skip` | `transcode` allows UTF-16 → UTF-8 and sets `byte_offsets_transcoded`; a NUL in the first 8 KiB ⇒ `binary` |
| `run_dir` | path | the OS user cache directory `<cache>/ezredis/runs/<run_id>` | **R-14 recommended default** (avoids polluting the analysed repository); on the write boundary's allow-list as EZ-Redis-generated content |
| `incremental` | `bool` | `False` | behind `--incremental` (P18/P23) |
| `max_ir_facts` / `max_ir_bytes` | `int` | `2_000_000` / `536_870_912` | exceeded ⇒ abort with `limits_exceeded` rather than exhausting memory |
| `runtime_enabled` | `bool` | `False` | §I/P22; listed so the config file is complete |

**Precedence (highest first):** CLI flag → environment variable → a project config file at the workspace root → defaults. The model is strict and frozen: an unknown key is a hard error, so a typo cannot silently disable a limit. **Drift coupling:** the IR-affecting subset of this config hashes into the manifest, and a change forces a full run.

### E.7 Interface-level spec 4 — run manifest / run-directory contract (P05/P16/P17/P23)

Directory layout (an illustration, not pseudocode):

```text
<run_dir>/
  manifest.json          # run state, provenance, resume point — written last, atomically
  run_summary.json       # machine-readable run summary
  run.log.jsonl          # structured event stream, one object per line (append-only)
  ir.json                # canonical Redis IR
  ir.schema.json         # emitted JSON Schema (drift guard)
  findings.json          # canonical findings
  recommendations.json   # recommendation records
  documents/             # generated documents only (write boundary)
```

**`RunManifest` fields.** `manifest_schema_version`; `run_id` (unique, sortable by start, filesystem-safe, containing **no absolute path, user name or hostname**); `run_kind ∈ {analyze_full, analyze_incremental, documents, inspect_runtime}`; `tool_version` / `ir_schema_version` / `ruleset_version`; `workspace_root` (a local-only resume precondition, **never emitted**) and `workspace_display` (basename, used everywhere else); `args_digest` (a resume whose digest differs is refused); `scope{kind, languages, changed_files}`; `status ∈ {in_progress, completed, partial, failed, aborted}`; `last_completed_stage` (the resume cursor); `stages: StageRecord[]`; `input_fingerprint` / `output_hashes` (**content hashes authoritative; mtime a hint only**); `documents: [{path, generated_at, source_hashes, marker_version, status: fresh|stale|refused}]`; `refusals: [{stage_id, subject, axis, reason_code, detail_redacted}]`; `started_at` / `updated_at` / `finished_at` (RFC 3339 UTC, `updated_at` non-decreasing, `finished_at` set exactly once); `exit_code`; `environment{python_version, platform, cpu_count, warm_run}` (volatile); `redactions_applied` (an integer count, never the values). **The manifest is replaced atomically at every stage boundary**, so no partially written manifest is observable.

**`StageRecord` fields.** `stage_id` (the closed 8-stage enum); `stage_attempt ≥ 1`; `started_at` / `finished_at`; `duration_ms` (**integer milliseconds — the measurement instrument for the latency targets**); `outcome ∈ {ok, partial, failed, skipped, refused}`; `reason_code` (required whenever the outcome is not `ok`, never free text); `items_considered` / `items_processed` / `items_skipped` / `items_refused` with conservation `considered = processed + skipped + refused`; `ceilings_hit: string[]` (a cap is always a count + named ceiling, never a silent truncation); `stage_counts`; `dependency` / `dependency_health` (external stages only); `retryable` / `attempts_planned` / `attempts_made` / `retry_budget_remaining`; `retry_after_s`; **`fallback ∈ {none, deterministic, omitted_degraded}`** (a fallback is `outcome="ok"` **with** a reason code, **not** `failed`); `source`; `redactions_applied`.

**`run_summary.json`** reuses and extends the tool summary's field names (the MCP summary is a strict identically-named subset, D6): files analysed and by parse status / language; IR facts total and by kind; findings total, by severity and by evidence class; `unresolved_count` / `unresolved_by_kind`; `parse_failures` (a bounded list plus `parse_failures_truncated`, with the count authoritative); `refusals[]`; `documents_generated` / `documents_refused` / `documents_stale`; `degraded`; `stages[]`; `ceilings_hit[]`; `environment`; `exit_code`. Every list is capped with an explicit truncation flag so the response cannot grow without bound.

**`RunLogEvent`** (`run.log.jsonl`, one object per line, the human rendering produced from the same object): `log_schema_version`, `seq` (monotonic), `at`, `level ∈ {debug, info, warning, error}`, `event` (a closed snake_case enum), `message` (**constant per event — never interpolated with data**; variable content lives in `data`), `run_id`, `stage_id` / `stage_attempt`, `event_id` / `parent_event_id`, `reason_code`, `data` (a closed per-event key list, redaction-scrubbed), `redactions_applied`. Level rules: `info` = normal lifecycle; `warning` = degraded/partial/skipped/refused (output exists but is incomplete); `error` = the run cannot produce its documented output; **user/usage errors are `warning` with a documented exit code, never `error`**. **Log-once rule:** the stage that fails logs exactly one `warning` with its reason code; the CLI boundary logs exactly one `error` with the same reason code and event linkage; inner layers return and never log.

**Accounting invariant.** `counts.discovered = counts.analysed + counts.skipped_by_rule` **and** `counts.analysed = counts.parsed + counts.partial + counts.failed`; a violation sets `status="failed"` with a diagnostic, because it means the pipeline lost a file. Per-file errors never abort; a broken count invariant does.

**Resume, staleness and idempotency invariants.** Atomic step writes (a torn file is unreadable, never adopted). Resume requires `status="in_progress"` **and** the same `args_digest`, workspace root and IR schema version, else `resume_conflict` with **no implicit re-analysis**. An interrupted run is visible, not guessed (`last_completed_stage`). Version drift on load is refused (no migration in the slice). A document whose recorded source hashes no longer match is marked **stale**, never silently trusted. Idempotent re-runs: a re-run on unchanged input yields the same run id and is a no-op; a completed run directory is never mutated. Conservation is enforced per stage.

### E.8 Interface-level spec 5 — error and reason-code catalogue

One closed vocabulary is reused by the run log, the manifest, the summary, the CLI and (as the RFC 9457 `code`) the MCP envelope. A reason code is never reused with a different meaning; renaming is a visible version bump requiring an ADR.

**(a) Envelope codes** (see §E.3 for the 11) plus the run-level additions: `schema_version_mismatch` (stored IR/manifest schema or analyser version differs from the current one — refuse to interpret, never migrate silently), `dependency_unavailable` (an optional dependency exhausted its budget), `ai_disabled` (Jev not enabled — not an error state), `degraded` (a **marker**, not an error: a stage returned partial/skipped/refused/fallback; must never be mapped to a non-zero exit by default), `internal_error` (the only condition that aborts a run; the partial manifest is still written). Invariants: exactly one code per failure, no compound codes; a code is either an error or a marker; every code is defined once in one table and referenced, not re-spelled, by the log, the CLI and the MCP envelope; a code not in this table may not be emitted.

**(b) CLI exit-code map.** `0` run completed (findings may exist, including a degraded run and a deterministic fallback) — **non-zero only on error, never merely "findings present"**; `1` internal error; `2` usage/validation error; `3` a schema-version mismatch on a run the caller asked to read (refusal to interpret); `4` nothing useful produced (a run in progress, or every requested dependency refused / limits exceeded); `5` **only with `--strict`** — `degraded=true`, so CI can opt in while the default stays 0 and degradation is visible but not breaking.

**(c) Run/stage reason codes.** `file_skipped_oversize` / `file_skipped_undecodable` / `file_skipped_symlink_escape` / `file_skipped_ignored`; `parse_failed`; `parse_timeout`; `rule_raised`; `rule_skipped_input_unchanged` (incremental); `attempt_timeout`; `deadline_exceeded`; `iteration_cap_exceeded`; `size_cap_exceeded`; `document_not_applicable`; `run_interrupted` / `run_resumed`; `count_invariant_violation`; `ir_schema_drift` / `ruleset_drift` / `config_drift`.

**(d) External-boundary codes.** `dependency_unreachable` / `_tls_failed` / `_auth_failed`; `dependency_throttled_429` / `_overloaded_529`; `dependency_error_5xx`; `dependency_timeout`; `response_invalid` / `response_out_of_set` (discarded, never repaired); `payload_over_limit`; `budget_exhausted` (**our** retry cap stopped retrying — distinct from the dependency refusing); `no_candidate_satisfies_constraints`; `recursion_limit_reached`; `command_refused_by_gate` (**must carry its axis**).

**(e) Live-Redis refusal codes, by axis** (one axis per code so a test asserts the *right* refusal reason, not merely a refusal; refusal is **fail-closed**):

| Axis | Codes |
|---|---|
| A-flag (`readonly`) | `unf_command_not_readonly`, `unf_command_notifications_enable`, `unf_evaluation_error_fail_closed` |
| A-cat (¬`@dangerous`) | `unf_command_dangerous`, `unf_command_both_axes_missing` |
| A-sub (subcommand scope) | `unf_subcommand_not_allowed`, `unf_subcommand_scoping_unavailable` (pre-7.0), `unf_diagnostics_profile_required` |
| A-cap (capability) | `unf_command_unknown_capability`, `unf_command_flag_axis_unavailable` (pre-6.0), `unf_command_capability_conflict` (**server wins on drift**) |
| A-bound (cost/volume) | `lim_scan_iterations_exceeded`, `lim_slowlog_count_exceeded`, `lim_memory_samples_exceeded`, `lim_response_bytes_exceeded` |
| observation (not a refusal) | `obs_keyspace_notifications_unknown`, `obs_runtime_facts_degraded` |

**(f) Filesystem write-boundary codes, by axis** (one axis per record):

| Axis | Codes |
|---|---|
| W (target / provenance) | `wbf_target_not_allowlisted`, `wbf_generated_marker_missing`, `wbf_generated_marker_mismatch`, `wbf_owner_mismatch`, `wbf_run_id_mismatch`, `wbf_ir_schema_version_mismatch`, `wbf_no_run_id` |
| P (path) | `wbf_output_dir_outside_workspace`, `wbf_path_escapes_workspace`, `wbf_symlink_not_followed` |
| S (secret) | `wbf_secret_in_payload` |

**(g) AI-egress codes** (axis E): `aig_ai_disabled`, `aig_untrusted_content_excluded`, `aig_egress_budget_exceeded`, `aig_secret_in_payload`, `aig_response_invalid`, `aig_response_out_of_set`, `aig_provider_unavailable`, `aig_numeric_question_refused`.

**(h) MCP-surface codes** (axis M): `mcp_path_outside_workspace`, `mcp_profile_not_configured`, `mcp_problem_code_unknown` — and the envelope codes reused; **MCP invents no parallel codes**.

**Naming and disclosure rules (N-1…N-6, binding on every code above).** N-1 `snake_case`, stable, additive-only within a major; **the code is the contract and `detail` is human text**. N-2 exactly one axis per code, stated in the catalogue. N-3 refusal is **fail-closed** — unknown capability, parse error or drift refuses, never allows. N-4 **never echo** connection strings, credentials, secret values, raw Redis key values, absolute realpaths outside the workspace, or other clients' addresses. N-5 **do echo** the command/subcommand name, the axis, the confinement root, and the cap name and value — the operator must be able to fix it. N-6 one code per condition; compound facts go in `detail`.

**The deterministic-fallback contract (a named return value, not an exception).** Fields: `fallback` (the only legal value today is `deterministic`), `source` (always `deterministic` on a fallback), `reason_code` (from the catalogue above — names *which* failure, not "unknown error"), `dependency ∈ {jev, redis_runtime, filesystem}`, `attempts_made` / `attempts_planned`, `retry_after_s`, `degraded` (always true), `deterministic_result_ref` (**the fallback always carries the deterministic result**). Five invariants, each asserted by a test: (1) **never an exception** — a fallback returns through the normal channel; (2) the deterministic answer is computed **first**, then optionally improved, never replaced; (3) a fallback is `ok`, not `failed`; (4) a fallback is **never silent** — the reason code and `degraded` reach the log and the summary; (5) a model answer can never authorise an action, set a threshold or change policy, so a fallback can never change correctness, only confidence — and an out-of-set or invalid answer is **discarded, not repaired**.

## F. Repository Documentation Lifecycle

### F.1 Which documents, and when each applies

Four documents are planned: **`CACHING.md`**, **`RATE-LIMITING.md`**, **`REDIS-SEARCH.md`** and **`IRIS.md`**. Each is a projection of the IR, findings and recommendations produced by one run — never generic advice prose.

**The applicability rule, extended to all four documents** `[proposed, disclosed deviation]`. A document is generated only when its corresponding IR section is non-empty; otherwise the run reports "**not applicable, with evidence**" and writes nothing.

| Document | Precondition to emit | If the precondition is unmet |
|---|---|---|
| `CACHING.md` | ≥ 1 cache site, or any write path touching a key with a TTL policy | report "CACHING not applicable, with evidence"; write nothing |
| `RATE-LIMITING.md` | ≥ 1 rate limiter | same |
| `REDIS-SEARCH.md` | ≥ 1 search usage | same |
| `IRIS.md` | IRIS / Agent Memory usage detected (`iris_usages` non-empty) | report "IRIS not applicable, with evidence"; write nothing |

**Disclosed deviation.** FR-22 says the plan shall "include all four knowledge documents"; this section additionally applies the prompt's own rule — *do not create empty or irrelevant documents merely to satisfy a predetermined list* — to all four, exactly as ADR-9 applies it to `IRIS.md`. FR-22 is satisfied by the phase existing **and** the conditional rule being written down. The alternative (always emitting a placeholder) is rejected because an empty document is indistinguishable from a document claiming "no findings".

**`IRIS.md` — the sourced finding (ADR-9).** Iris is Redis's AI-product umbrella, materialised today as Redis Agent Memory: a store addressed by a store identifier plus a store API-key bearer credential. **This is a research finding carried from `research_summary.md` (RQ-10), attributed there — the plan does not assert it as verified by this document.** The per-repository contents of `IRIS.md` (SDK detection, session vs long-term tiers, TTL/promotion configuration, retrieval call sites, redacted credential references) remain an implementation step `[unresolved]`, with that default named. Store API keys are referenced redacted and never copied into the document.

### F.2 How content is derived and maintained

**Derivation.** Each document is assembled from IR sections, findings and recommendations by a generator in `documents/`, with **one** writer function. Every section cites the run id, the rule ids and the IR references it was derived from; a section with no evidence is omitted or says **"not established"**, never filled with generic advice; no numeric performance claim may appear anywhere. Guidance prose, where used, comes from the pinned `redis/agent-skills` corpus (§D, ADR-D1/ADR-7) and is attributed to the section that uses it.

**Provenance marker.** Every generated document begins with a generated-file provenance header: tool, tool version, IR schema version, run id, owner identity and the source hashes it was derived from. **The marker is two things at once** — the write guard (it is how the boundary recognises an EZ-Redis-generated file) and the **staleness detector**.

**Staleness.** A later run compares the marker's recorded source hashes against the current manifest input fingerprint; a mismatch marks the document `stale` in the run summary and the document list. Documents are re-validated against source, never consumed as instructions.

**Refresh, write boundary, user-edit preservation.** Re-generation overwrites **EZ-Redis-generated files only** (marker present and matching); a pre-existing file without the marker, or a generated file a user has edited (marker present, provenance mismatch), is **refused and reported** — never overwritten. A refusal appends to the run's `refused` list and does not abort the run. Secrets are referenced redacted and never copied. Git conflicts, merge conflicts and concurrent changes are handled the same way: anything not provably EZ-Redis-generated is refused, so the tool can never clobber a hand-authored file, and the developer resolves the rest with normal version control.

**Additional documents considered and deferred.** Vector-search, data-structure, cache-invalidation, connection-management, transactions/pipelines and key-convention documents are **evaluated but not planned in the slice**: they would overlap the four documents above, and the prompt's rule against empty or duplicative documents applies. They are recorded here as later candidates.

**Layout question (recorded, with a default).** Whether the documents belong at the repository root or in a dedicated documentation directory is an open prompt question. **Default: the repository root**, preserving the filenames the prompt names, with the output directory configurable; a dedicated directory is the recorded alternative. The trade-off is discoverability and filename fidelity (root) versus a cleaner tree (subdirectory).

### F.3 `CACHING.md` — section outline (14 sections)

| § | Heading | Content | Evidence source | Emitted when |
|---|---|---|---|---|
| 1 | Scope and evidence basis | run id, IR schema version, files analysed, parse-status counts, global unresolved roll-up, and the list of what was **not** established | repo, files, unresolved | always |
| 2 | Cache boundaries and clients | each client binding, its library and binding kind, and the key prefixes it touches | clients, literal prefixes | ≥ 1 client binding |
| 3 | Patterns in use | per cache site: pattern kind, read/write/invalidation op ids, best-effort authoritative source | cache sites, data-store links | ≥ 1 cache site |
| 4 | Key design and layout | per template: pattern, segment classes, delimiter, prefix, cardinality class **and its basis**, plus the explicit list of unknown-cardinality keys | operations' key exprs | ≥ 1 key template |
| 5 | TTL policy inventory | per key/operation: value, source and TTL form; grouped into missing / excessive (threshold stated as config) / explicit-no-expiry / different-key / config-derived | TTL policies | always (may say "no TTL-setting operation observed") |
| 6 | Invalidation mechanisms and linkage | per write path: mechanism and link kind, with candidate/unresolved reasons | invalidations | ≥ 1 write path |
| 7 | Freshness assessment | per cache site: the staleness bound (`time` + V / `invalidation`-derived / `none` / `unknown`), with a question on every `none`/`unknown` row | recommendation `staleness_bound` | ≥ 1 cache site |
| 8 | Stampede and hot-key exposure | detected shapes (no single-flight protection, shared TTL literal count, lock TTL absence, contention shape) and the mitigation present | `stamp.*` findings | ≥ 1 populate region or ≥ 2 identical TTLs |
| 9 | Consistency as observed | the write/read orderings actually found, and which race shapes remain unobservable | `ca.*`, `inv.order` | ≥ 1 write path |
| 10 | Design decisions carried forward | recommendation ids with current pattern, change kind, constraints applied and alternatives | recommendation records | ≥ 1 recommendation |
| 11 | Open questions | the question rows with why-needed and what they affect, ordered by blast radius | recommendation uncertainty | always (may be empty) |
| 12 | Findings summary | by rule id, with severity and confidence shown as **separate** columns | findings | ≥ 1 finding |
| 13 | Not established | the forced disclosure list: no traffic, hit-rate, latency or memory; no server configuration; no cross-instance behaviour | §F.5 | always |
| 14 | Provenance and staleness | the generated-file marker, source hashes, IR/analyser versions, refresh instructions | run manifest | always |

### F.4 `RATE-LIMITING.md` (11 sections) and `REDIS-SEARCH.md` (11 sections)

**`RATE-LIMITING.md`.** The document's scope section **discloses the guidance-source gap**: no rate-limiting skill exists in the reuse corpus, so sections 5–8 cite `redis-core`/`redis-connections` plus the vendor command pages, and say so. Sections: **(1)** scope and evidence basis, including that gap; **(2)** limiter inventory — each limiter's classification, the signals that produced it and the confidence basis; **(3)** commands and data structures — counter/expiry/set/zset operations and whether the counter and expiry are separate commands; **(4)** atomicity assessment — single-command / script / transaction / **non-atomic**, with the crash-window consequence stated in words and no numbers; **(5)** key design — window key templates, per-identity segments, time-bucket expressions, cardinality basis, and the explicit statement that per-identity cardinality is **intended** here; **(6)** expiry semantics — window reset mechanism, the reset-on-every-request shape, limits with no expiry, and config-derived TTLs as questions; **(7)** windowing strategy — algorithm classification and the boundary-burst property of fixed windows (stated as an algorithm property, cited); **(8)** limits and enforcement — where the limit literal lives and where the comparison happens, with fail-open/fail-closed stated **only** if an explicit fallback path is in scope; **(9)** correctness concerns — the non-atomic counter, the non-unique sliding-window member, reset-on-each-request, unresolved limit — each with its evidence and its `needs_confirmation` siblings; **(10)** performance considerations — **shapes only**, command count per limiter path counted from IR operations in the analysed path (never traffic), unbounded key growth, extra round trips implied by non-atomicity, no millisecond figures; **(11)** open questions and provenance.

**`REDIS-SEARCH.md`.** Sections: **(1)** scope and evidence basis, including the module-availability caveat; **(2)** index inventory — each index-definition site: index name, `ON HASH|JSON`, prefixes, and whether application code creates indexes at runtime; **(3)** schema inventory — field names, types, `SORTABLE`/`UNF`, JSON paths and aliases, plus field-type-versus-access-pattern observations cited to the skill corpus, not asserted as measurements; **(4)** vector configuration — per vector field: algorithm (`HNSW`/`FLAT`), type, dimensions, distance metric and tuning parameters, reported as **configured**, never as a quality verdict; **(5)** query inventory — per query site: command, index, dialect presence/value, filters, sort, limit, return shape, and parameter shape; **(6)** vector and hybrid query shapes — the KNN form, pre-filter presence, hybrid combine/yield legs, and the **version question** when the target version is unknown; **(7)** aggregation and pagination — pipeline stages present, cursor/count use versus an unbounded limit, and load-all; **(8)** result handling — no-content/return/with-scores and JSON-vs-hash decoding shapes seen in the same file; **(9)** consistency with the index definitions — query field absent from a resolved schema, literal dimension/metric mismatch, parameter-count mismatch; **(10)** performance considerations — **shapes only** (unbounded limit, missing pre-filter, load-all, dialect absence, index created at request time), each phrased as a shape with its evidence; **(11)** not established and open questions — module/server version, production-index equality, recall and latency — plus the provenance marker.

### F.5 What the documents must never claim

| Claim family | Honest form | Forbidden form |
|---|---|---|
| staleness, a write path with a resolved invalidation link | "the write path invalidates K (`delete`, resolved link at span X)" | "the cache is consistent" |
| staleness, a write path with no link | "no invalidation link to K was found; no time bound is set; the staleness bound is `none`" | "the cache is stale" / "users see stale data" |
| staleness bound | "`time` + V seconds" only when V is a literal; "invalidation-derived, pending confirmation of completeness" only with a resolved link; `unknown` with a config/wrapper TTL | a bound derived from a config value or a wrapper default |
| TTL expiry semantics | "the TTL is set to V; when the entry is removed depends on server expiry, which is not instantaneous with the TTL value" | "the entry is removed exactly at V" |
| notification/pubsub invalidation | "the application publishes to channel C; delivery is fire-and-forget, events are lost while disconnected, and cluster mode needs per-node subscription, so completeness cannot be established" | "invalidation is guaranteed via pub/sub" |
| keyspace notifications | "not enabled by this tool; whether the operator enabled them is unknown" | "notifications are enabled" / enabling them |
| races / stampede / hot key | shape only ("the ordering allows a concurrent reader to repopulate a stale value"; "the populate region has no atomic single-flight protection") | "this race occurs in production"; any request-rate figure |
| rate-limiter correctness | "the increment and the expiry are separate commands outside an atomic scope; a crash between them leaves the key without an expiry" | "this limiter is broken / allows N extra requests" |
| Search behaviour | "no dialect argument is present and the target version is unknown, so query semantics are unverified" | "queries return wrong results"; any recall or latency figure |
| application failure behaviour (cache down) | "not established" unless an explicit fallback path is in scope | fail-open/fail-closed asserted from shape |
| any improvement | only inside a P25 measurement | "this reduces latency by X" in any finding, document or CLI summary |

## G. Detailed Implementation Phases

**28 phases (P01–P28) in 6 milestones (M1–M6), each milestone ending in exactly one go/no-go gate (G1–G6).** Milestone map: **M1 Foundation, contracts and deterministic core** (P01–P05) · **M2 Adapters and static analysis breadth** (P06–P14) · **M3 Findings, recommendations and outputs** (P15–P19) · **M4 Developer integrations and opt-in runtime** (P20–P23) · **M5 Evaluation, quality bar and hardening** (P24–P26) · **M6 Optional AI layers, droppable** (P27–P28). Nothing in M4–M6 begins before M1–M3 have landed. Every phase is `[proposed]`; none has been started.

**Sequential spine.** P01 → {P02, P03, P04} → P05 → (P06 ∥ P07) → P08 → P09…P14 → P15 → {P16, P17} → P18 ∥ P19 → P20 → P21 ∥ P22 → P23 → P24 → P25 → P26 → P27 → P28.
**Approved dependency corrections.** **P24 ← P08, P14, P15** (every rule family must exist before it can be labelled; P14 is the last rule phase) and **P25 ← P23, P24** (the 100 k-LOC end-to-end benchmark needs the complete path, including the CLI and the incremental wiring).
**Parallel-safe groups** (disjoint paths, no data dependency): (P06, P07); (P16, P17); (P18, P19); (P21, P22). Rule families P09–P14 are mostly disjoint files but **share the rule registry**, so at most two rule authors run concurrently — or one author for all six.
**Fixture split.** P09–P14 author **per-rule developer fixtures** in-phase; only **P24** owns the **labelled measurement corpus**. This is what stops the corpus phase from blocking M2.

**Every phase box carries all nine fields:** Objective · Scope / non-goals · Key deliverable · Dependencies · Relative size · Calendar estimate · Serves (FR/NFR/AC ids) · Tests / acceptance criteria · Definition of done. A `Rollback:` clause appears inside the last field for state-changing phases only. Sizes: **S ≈ 1–2 sessions, M ≈ 3–5, L ≈ 6–10** (a session ≈ 4 h).

**Calendar-estimate baseline (A0) and the honesty rule.** **A0:** one implementer, **~10 h/week**, strong Python, **moderate** Redis, **low/none** tree-sitter, MCP-SDK, Jev and LangGraph familiarity (those phases widen their ranges). Every estimate below is labelled **indicative**, states its assumptions, gives an uncertainty range, and is **a forecast — not a measurement and not a commitment** (FR-11/D-7).

**Total calendar estimate (indicative): ~40–100 weeks at 10 h/week, midpoint ≈ 60 weeks (~600 h).** This is the sum of per-phase forecasts; it is **not a measurement and not a commitment**.

### G.1 M1 — Foundation, contracts and deterministic core (P01–P05)

#### P01 — Repository skeleton and pinned toolchain · Milestone M1 · Size S
- **Objective:** Stand up the uv-managed package skeleton and CI so every later phase builds on the pinned 3.12–3.13 baseline.
- **Scope / non-goals:** In: manifests, `requires-python = ">=3.12,<3.14"`, ruff/mypy/pytest wiring, package layout, console entry point, CI matrix on 3.12 + 3.13, the no-network import guard, an offline CI check. Non-goals: any analysis code; any dependency in the optional agent or telemetry groups; publishing.
- **Key deliverable:** a manifest + a universal lockfile + CI that runs `uv sync --frozen`, lint, types and an empty test suite on both pinned interpreters.
- **Dependencies:** —.
- **Relative size:** S (1–2 sessions).
- **Calendar estimate (indicative):** ~0.5 wk (range 0.3–1 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-25, FR-27; AC-19, AC-21; ADR-1 note.
- **Tests / acceptance criteria:** `uv sync --frozen` succeeds on 3.12 and 3.13; ruff and mypy are clean on the empty package; the import guard fails if `runtime/`, `ai/` or `agent/` is imported from the core; a network-disabled run passes.
- **Definition of done:** both interpreters install, lint, type-check and run the empty suite in CI, and the 3.14 interpreter is used nowhere.

#### P02 — Deterministic file discovery and language detection · Milestone M1 · Size M
- **Objective:** Walk a workspace and emit a deterministic manifest of analysable files with detected languages.
- **Scope / non-goals:** In: ignore rules including the `.gitignore` conventions, symlink and `..` escape refusal, size and iteration caps, non-UTF-8 handling, a sorted manifest; explicit encoding verdicts (BOM, UTF-16, Latin-1, binary), the file-size and file-count caps, and hashing the bytes actually parsed. Non-goals: parsing; language semantics; retaining content.
- **Key deliverable:** the discovery package + a manifest model + a synthetic fixture tree, all paths-only (no contents kept).
- **Dependencies:** P01.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-19; AC-14; F1, F3.
- **Tests / acceptance criteria:** unit tests on a synthetic tree (ignored directories, symlinks, oversize, undecodable); the manifest is byte-identical across two runs; a symlink escaping the workspace is refused; all four languages are detected; one fixture per encoding class; a skipped file appears in the counts with a reason code.
- **Definition of done:** discovery is deterministic, bounded and refuses escapes, with the four languages detected and no file content retained.

#### P03 — Shared Redis IR · Milestone M1 · Size M
- **Objective:** Define the single validated, provenance-carrying Redis-usage contract.
- **Scope / non-goals:** In: the pydantic model set, JSON Schema, deterministic ordering, provenance and unresolved invariants, IR fixtures and a versioning policy; provenance-level semantics; the unresolved roll-up with `impact`/`blocking`; the key-expression deepenings (`dynamic_kind`, `literal_suffix`, `cardinality_basis`); total-order keys. Non-goals: rules, adapters, runtime data, algorithms.
- **Key deliverable:** the IR models + generated JSON Schema + round-trip, ordering and roll-up tests.
- **Dependencies:** P01.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-14, FR-19, FR-26; AC-10, AC-14; contract 1 (§E.1).
- **Tests / acceptance criteria:** the schema round-trips; a fact without provenance fails validation; ordering is byte-stable, including under two different hash seeds; the schema feeds the MCP tool definitions; the unresolved roll-up is a superset of the inline set; the IR contains no source text.
- **Definition of done:** the IR validates, the schema is frozen at v1, and adapters can target it unchanged.

#### P04 — Finding record with evidence classification and confidence · Milestone M1 · Size M
- **Objective:** Define the finding contract that carries evidence, severity, confidence and unresolved as separate axes.
- **Scope / non-goals:** In: the model, severity ≠ confidence, the evidence class including `needs_confirmation`, content-hash ids, the at-least-one-evidence invariant, limitations and the provenance spine; negative (`absence`) evidence support. Non-goals: any rule that produces findings; recommendation logic.
- **Key deliverable:** the findings package + tests + a hand-written fixture finding.
- **Dependencies:** P01.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-14, FR-28; AC-10, AC-22; contract 2 (§E.2).
- **Tests / acceptance criteria:** a finding without evidence fails validation; ids are stable under reordering; severity and confidence vary independently; a fact with `impact="changes_verdict"` forces `needs_confirmation`; an `absence` evidence item validates.
- **Definition of done:** the finding contract validates and enforces its two invariants (evidence required; deterministic id).

#### P05 — Analysis engine, rule registry, run directory and run log · Milestone M1 · Size M
- **Objective:** Build the deterministic pipeline that runs pure rules over the IR and records an inspectable run.
- **Scope / non-goals:** In: the eight fixed stage ids, the pure `Rule.evaluate(ir, config)` seam, the rule registry, the run-directory contract (manifest, summary, event stream), atomic per-stage writes, per-stage timing and counting, the reason-code enum, fail-open logging, and the resume/idempotency predicates. Non-goals: any concrete rule (P09–P14); incremental patching (P23); any I/O beyond the run directory.
- **Key deliverable:** the analysis engine + the three run-directory artefacts + a no-op rule proving the seam + emitted JSON Schema for the manifest, summary and log event.
- **Dependencies:** P02, P03, P04.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-19, FR-28; AC-14, AC-10(b); §C.4; F13, F14.
- **Tests / acceptance criteria:** a fixture-IR run emits a schema-valid manifest, summary and event stream with per-stage durations and counts satisfying `considered = processed + skipped + refused`; a re-run is idempotent; resume predicates refuse a mismatched args digest and a schema mismatch; a raising rule yields one `rule_raised` and a `partial` stage, not an abort; the declared determinism carve-out is asserted; the import guard still passes.
- **Definition of done:** the engine seam, registry and run directory are proven by the no-op rule, an idempotent re-run and a schema-valid event stream.

**Gate G1 (M1) — go/no-go.** **Evidence to pass:** (a) the IR and finding schemas validate and their JSON Schema is emitted; (b) discovery runs on the synthetic tree and the manifest is deterministic; (c) all four languages are **detected**; (d) the import guard proves `runtime/`, `ai/` and `agent/` are unreachable from the core; (e) the no-op rule proves the engine seam, with an idempotent re-run. **Action if it fails:** revise the IR and finding schemas and the engine scope **before any adapter work** — do not start M2 with an unstable IR, because both adapters and all rules are built on it.

### G.2 M2 — Adapters and static analysis breadth (P06–P14)

#### P06 — Python adapter · Milestone M2 · Size L
- **Objective:** Parse Python to a CST and emit honest IR facts for Redis client usage.
- **Scope / non-goals:** In: client detection, command/key/TTL/pipeline extraction, provenance levels, `unresolved` for dynamic keys, wrapper indirection and cross-file flow; the `parse(path, source, ctx) -> AdapterResult` seam; a capability declaration; per-fact provenance only (no resolution claims). Non-goals: type inference (no Pyre server or watchman); full dataflow; any rule.
- **Key deliverable:** the Python adapter + Python fixtures with expected-IR snapshots.
- **Dependencies:** P05.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **low tree-sitter familiarity widens the range**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-26; AC-20; ADR-1; F1, F2; contract spec 1 (§E.4).
- **Tests / acceptance criteria:** an f-string key yields a command and a key expression with a literal prefix plus a dynamic segment and **no** resolution claim; a parse failure degrades to `partial` with an `unresolved` entry; snapshots assert provenance and unresolved entries, not only recovered facts; the adapter takes bytes; partial-parse ranges appear on a broken fixture.
- **Definition of done:** the adapter emits provenance-tagged IR facts and explicit unresolved entries on the fixture set, with snapshot tests green.

#### P07 — JS/TS/TSX adapter (two grammars) · Milestone M2 · Size L
- **Objective:** Parse JavaScript, TypeScript and TSX and emit the same IR facts.
- **Scope / non-goals:** In: JS/TS/TSX wiring with **both** the typescript and the tsx grammar, `ioredis`/`node-redis` shapes, dialect routing for `.js/.jsx/.ts/.tsx`, provenance and unresolved. Non-goals: the TypeScript compiler-API deepening tier; Node subprocess management.
- **Key deliverable:** the JS/TS adapter + JS/TS/TSX fixtures with expected-IR snapshots (including a TSX-only fixture and a JSX fixture).
- **Dependencies:** P05.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **two-grammar wiring adds risk**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-26, R-6; AC-20; ADR-1; F1, F2.
- **Tests / acceptance criteria:** a TSX-only test exists so the second grammar cannot be forgotten; a JSX fixture exists; the same IR invariants as P06 hold; both adapters share one IR conformance diff.
- **Definition of done:** both grammars are exercised by fixtures and the adapter holds the same provenance and unresolved invariants as P06.

#### P08 — Parser decision confirmation, conformance harness, four-language load smoke test · Milestone M2 · Size M
- **Objective:** Execute ADR-1's four confirmation measurements and record the parser decision (or its documented fallback).
- **Scope / non-goals:** In: a conformance harness (both adapters against one IR contract), the four ADR-1 measurements, an ABI/load smoke test, a recorded decision plus its fallback (pin the tree-sitter core at 0.25.x, or escalate the LibCST/TS-API tiers). Non-goals: rule implementation.
- **Key deliverable:** a recorded decision artefact + harness + smoke test + measured numbers (labelled measured, hardware noted).
- **Dependencies:** P06, P07.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-26, A-1; AC-20; ADR-1; U-1, U-2.
- **Tests / acceptance criteria:** record four measurements with hardware, dataset revision, cold/warm, iterations and percentiles: (1) 100 k-LOC parse-plus-query wall clock leaves headroom inside 60 s; (2) the fraction of Redis call sites whose key expression resolves to a literal prefix is recorded **as a number**, per language; (3) all four languages load with `abi_version ≤ 15`; (4) single-file re-parse is recorded. The API-tier smoke test uses the 0.26 accessors; the fallback is the 0.25.x pin behind the shim. Out-of-threshold results trigger ADR-1's fallback.
- **Definition of done:** all four measurements are recorded and the parser decision plus fallback is written into the plan's decision log.

#### P09 — Cache-aside usage and key-construction rules · Milestone M2 · Size M
- **Objective:** Detect consistent/inconsistent cache-aside usage and key-design problems deterministically.
- **Scope / non-goals:** In: cache-aside detection, key naming and layout, dynamic/unbounded key cardinality as a *question* when unresolved; the `ca.*`/`key.*`/`miss.*` rule id families; the assertion ceiling and evidence minimum per family. Non-goals: recommendations (P15); other categories; any network; the labelled measurement corpus (P24 owns it).
- **Key deliverable:** rules + unit tests on hand-built IR fixtures + **per-rule developer fixtures authored in-phase**.
- **Dependencies:** P08.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-23; AC-17; ADR-1 depth limits.
- **Tests / acceptance criteria:** ≥ 1 positive and ≥ 1 negative **developer** fixture per rule id; a cross-scope ordering case asserts `link_kind="candidate"`, never `resolved`; a dynamic key asserts `needs_confirmation` and severity at most `info`; unresolved input never yields a defect; no rule performs I/O (enforced by test).
- **Definition of done:** the category's rules have positive/negative developer fixtures and never emit a defect on unresolved input.

#### P10 — TTL policy and expiry rules · Milestone M2 · Size M
- **Objective:** Detect missing, excessive or inappropriate TTL and a TTL set on a different key than the one written.
- **Scope / non-goals:** In: missing/excessive TTL, explicit-no-expiry, TTL on a different key, TTL from config, and `KEEPTTL` as a distinct unknown case; the `ttl.*` rule ids; the assertion ceiling per family. Non-goals: invalidation correctness (P11); the labelled corpus (P24).
- **Key deliverable:** rules + tests + **per-rule developer fixtures (in-phase)**.
- **Dependencies:** P08.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-23; AC-17.
- **Tests / acceptance criteria:** developer fixtures for every rule id; a config-sourced TTL yields a question, not a defect; a `KEEPTTL`/`PERSIST` pair yields two distinct findings; `ttl.missing` never fires above `info` when a resolved invalidation link exists on the key; the negative-TTL/flag-semantics row is recorded as an assumption with its confirmation route.
- **Definition of done:** the TTL rules meet the quality bar and never assert a defect from inferable-only evidence.

#### P11 — Invalidation and stale-data rules · Milestone M2 · Size L
- **Objective:** Detect write paths without a corresponding invalidation and the resulting stale-read risk.
- **Scope / non-goals:** In: writes lacking invalidation, invalidation-to-cache-site linkage (`resolved`/`candidate`/`unresolved`), overwrite versus delete, partial invalidation and ordering; the `inv.*` rule ids. Non-goals: runtime staleness verification (P22 only observes); consistency-proof claims; the labelled corpus (P24).
- **Key deliverable:** rules + tests + **per-rule developer fixtures (in-phase)**.
- **Dependencies:** P08.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **cross-file flow is only partially resolvable** (U-1). *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-23; AC-17; F4.
- **Tests / acceptance criteria:** developer fixtures per rule id; cross-file invalidation produces `link_kind="candidate"` with limitations, never a false `resolved`; a pubsub case asserts "completeness cannot be established"; a test asserts no performance claim can appear in a finding, and the same assertion extends to the recommendation path.
- **Definition of done:** invalidation rules report candidate links honestly and pass the no-performance-claim test.

#### P12 — Stampede/hot-key and rate-limiting rules · Milestone M2 · Size L
- **Objective:** Detect thundering-herd/hot-key shapes and rate-limiter implementation defects.
- **Scope / non-goals:** In: missing jitter or lock, thundering-herd shapes, fixed/sliding/token/leaky implementations, non-atomic increment-plus-expire, missing window, limiter key cardinality; the `stamp.*`/`rl.*` rule ids. Non-goals: measuring traffic; choosing a limiter algorithm (that is a P15 recommendation); the labelled corpus (P24).
- **Key deliverable:** rules + tests + **per-rule developer fixtures (in-phase)**.
- **Dependencies:** P08.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **`atomic_group` must exist in the IR or the flagship rule downgrades**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-23; AC-17.
- **Tests / acceptance criteria:** developer fixtures per rule id; a non-atomic limiter (an increment without an atomic expiry) is detected from the operations' grouping, or is downgraded to `needs_confirmation` when `atomic_group` is absent; the limiter window key is excluded from the key-cardinality family; limiter key cardinality is reported at `info`; hot-key rules emit a risk finding with the triggering evidence and no numeric impact claim.
- **Definition of done:** both rule families detect their shapes on developer fixtures and make no numeric impact claim.

#### P13 — Redis Search and vector-usage rules · Milestone M2 · Size M
- **Objective:** Analyse index definitions and query shapes sufficiently to power `REDIS-SEARCH.md`.
- **Scope / non-goals:** In: index definitions, index/search/aggregate/hybrid command shapes, dialect presence, field and schema extraction, vector query shapes, and anti-pattern shapes (no dialect, unbounded limit, missing filter, load-all); the `search.*` rule ids. Non-goals: constructing or querying a live index; RedisVL (ADR-5); the labelled corpus (P24).
- **Key deliverable:** rules + tests + the data source for `REDIS-SEARCH.md` + **per-rule developer fixtures (in-phase)**.
- **Dependencies:** P08.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-22, FR-23; AC-17; ADR-5, ADR-7.
- **Tests / acceptance criteria:** developer fixtures cover index, query, aggregate, vector and hybrid shapes; a literal dimension mismatch is a defect while an unresolved index name is a question; the hybrid finding carries the version question; consistency claims hold only between two literals resolved in the same run; the outputs render `REDIS-SEARCH.md` without re-parsing.
- **Definition of done:** the search developer fixtures pass and the outputs are sufficient to render the document.

#### P14 — Connection, pipeline, transaction, serialization and memory/eviction rules · Milestone M2 · Size M
- **Objective:** Cover the remaining analysis categories over the connection, grouping, payload and memory signals. (Last rule phase — P24 depends on it.)
- **Scope / non-goals:** In: pipelines/transactions and MULTI shapes, connection and pooling patterns, payload/serialization red flags, eviction and memory risk signals; the `cmd.*`/`ser.*`/`mem.*`/`conn.*` rule ids. Non-goals: judging capacity; byte-size, cost or performance claims; the labelled corpus (P24).
- **Key deliverable:** rules + tests + **per-rule developer fixtures (in-phase)**.
- **Dependencies:** P08.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-23; AC-17.
- **Tests / acceptance criteria:** developer fixtures per rule id; a `KEYS` call in application code is a defect; a pipeline-versus-transaction case asserts against `atomic_group`; every memory/eviction finding carries its limitation string when memory data is unavailable and stays `needs_confirmation` unless P22 supplies runtime evidence.
- **Definition of done:** the remaining categories have at least one honest rule each, passing the quality bar; the rule set is frozen so P24 can label it.

**Gate G2 (M2) — go/no-go.** **Evidence to pass:** (a) both adapters pass the conformance harness, and snapshots assert provenance and unresolved entries; (b) the four ADR-1 measurements are recorded with hardware; (c) a TSX-specific test passes; (d) each of the 13 categories has at least one implemented rule with positive and negative **developer** fixtures, with total rule count and per-category coverage reported; (e) the rule-purity test passes (no I/O; unresolved input ⇒ `needs_confirmation`, never a defect); (f) the engine runs with the network disabled. **Action if it fails:** if measurement (1) exceeds ~20 s or measurement (2) shows more than ~60 % of call sites unrecoverable, pull the LibCST (Python) and TS compiler-API tiers forward per ADR-1; if a category cannot be analysed honestly with syntax-only depth, narrow its rules and report the gap as `unresolved` rather than emitting weak findings. **Do not** proceed to M3 with a rule set that cannot state its own limitations.

### G.3 M3 — Findings, recommendations and outputs (P15–P19)

#### P15 — Deterministic recommendation layer · Milestone M3 · Size L
- **Objective:** Derive recommendations and explicit questions deterministically from IR facts and findings.
- **Scope / non-goals:** In: grouping by data flow, candidate-pattern derivation in code, compatibility and decision policy, trade-offs, at least one alternative, uncertainty and questions, `decision_state`; the non-cache `change_kind` for rate-limiting and Search recommendations; the named constraint catalogue. Non-goals: any AI path (P27); latency or memory improvement claims; patch generation.
- **Key deliverable:** the recommendation package + tests + fixture recommendations.
- **Dependencies:** P09–P14.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, D-12; AC-10; contract 4 (§E, recommendation record).
- **Tests / acceptance criteria:** every recommendation carries ≥ 1 alternative, cites evidence and names the constraints it satisfies plus the evidence that would flip it; `latency`/`memory` trade-offs are `"not established"` absent a measurement; insufficient evidence yields a question; a data flow with a resolved invalidation and no TTL yields an invalidation-derived staleness bound; a config TTL yields a question and no bound; `write_behind`/`prefetch` are rejected by constraints C-4/C-6 with the constraint id recorded; non-cache findings carry `recommended_pattern: null`; `measurement_absent` is non-empty on the default path; `source` is `deterministic`.
- **Definition of done:** recommendations always carry an alternative and evidence, and insufficient evidence becomes a question, not a recommendation.

#### P16 — Four document generators and the enforced write boundary · Milestone M3 · Size L
- **Objective:** Generate the applicable knowledge documents and guarantee that no existing file is ever modified.
- **Scope / non-goals:** In: the four document generators (with `IRIS.md` conditional and never empty), the generated-file marker, the target allow-list, refuse-and-report on conflict, provenance for staleness, secret redaction; a single write predicate consulted by the only writer, with owner-identity and marker matching, workspace and output-directory confinement with symlink refusal, and the write-boundary reason codes. Non-goals: overwriting any existing file or a non-generated path; patch generation; writing outside the output directory; writing to the reserved coordinator channel; any secret in any document.
- **Key deliverable:** the document generators + the write path + a fixture repository producing every applicable document, plus the write report structure.
- **Dependencies:** P15.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-21, FR-22; AC-16; ADR-7, ADR-9; F12; T4, T6.
- **Tests / acceptance criteria:** a fixture repository with Iris usage produces four documents, and one without produces three plus a "not applicable with evidence" report; a pre-existing edited `CACHING.md` is **not** overwritten and appears in the refused list with the right code; a symlink escape and an out-of-workspace output directory are refused; no secret string appears in any output (document-scan returns zero hits); every refusal carries a code from the catalogue.
- **Definition of done:** the write boundary refuses every non-generated target, the conditional IRIS rule is demonstrated both ways, and the secret scan is clean. **Rollback:** the generators and the boundary are additive; disabling the document phase leaves the analysis path intact.

#### P17 — Canonical JSON export and secondary SARIF 2.1.0 exporter · Milestone M3 · Size M
- **Objective:** Provide canonical machine-readable output and a secondary SARIF interoperability export.
- **Scope / non-goals:** In: canonical pydantic JSON with versions; SARIF 2.1.0 (+ Errata 01) with locations, rules and levels plus vendor properties for confidence and unresolved; schema validation in tests. Non-goals: adopting `sarif-om` (ADR-3); schema drift from the models.
- **Key deliverable:** the output package + golden-file tests + a SARIF validation test.
- **Dependencies:** P04, P05.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-22; AC-10; ADR-3; U-8.
- **Tests / acceptance criteria:** canonical output validates against its JSON Schema; the SARIF export validates with a schema validator; both are byte-stable across two runs; a drift test fails if a model changes without regenerating the schema.
- **Definition of done:** both exports validate and are byte-stable, with the schema-drift guard in CI.

#### P18 — CLI (click) over the library API · Milestone M3 · Size M
- **Objective:** Provide the human command surface with stable exit codes and no business logic.
- **Scope / non-goals:** In: analysis, incremental analysis, documents, findings, explain, an opt-in inspect-runtime command, an MCP launcher and version; the documented exit-code table; human and JSON renderings of the run summary, with the JSON event stream on stderr and the machine result on stdout; the redaction rules. Non-goals: business logic in the CLI; FastAPI; network-dependent default behaviour.
- **Key deliverable:** the CLI + the exit-code table + `CliRunner` tests + a network-disabled end-to-end run on a fixture repository.
- **Dependencies:** P15, P16, P17.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-19; AC-14, AC-10(b).
- **Tests / acceptance criteria:** a network-disabled end-to-end run produces IR, findings, documents and JSON and exits 0; each non-zero exit code is exercised by a named fixture; `--json` output equals the run-summary projection; the JSON event stream on stderr never pollutes stdout; a degraded run exits 4 with `degraded=true` unless `--strict` is given; `--incremental` is accepted (behaviour lands in P23).
- **Definition of done:** a network-disabled end-to-end CLI run succeeds and every exit code is documented and exercised.

#### P19 — Importable library API (stable public surface) · Milestone M3 · Size M
- **Objective:** Expose the same capability programmatically with no hidden state.
- **Scope / non-goals:** In: the analysis, IR-loading, findings-listing, recommendation and document-generation functions; typed returns; a documented stability policy; no I/O beyond the run directory. Non-goals: MCP-specific code; hidden global state.
- **Key deliverable:** the public surface + API documentation + import tests.
- **Dependencies:** P15, P17.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17; AC-14; B6 (§C.3).
- **Tests / acceptance criteria:** the public surface imports with no side effects; the same calls the CLI makes are available programmatically; importing the package does not import `runtime/`, `ai/` or `agent/`.
- **Definition of done:** the public API is import-clean, side-effect-free, and provably reachable without network or AI modules.

**Gate G3 (M3) — go/no-go.** **Evidence to pass:** (a) a full run on a fixture repository produces the applicable documents, with the conditional `IRIS.md` behaviour demonstrated **both ways**; (b) the write-boundary test proves no existing file is modified; (c) canonical and SARIF outputs validate and are byte-stable; (d) the CLI and library both complete a run with the network disabled; (e) the recommendation invariants hold (≥ 1 alternative and evidence; insufficient evidence yields a question). **Action if it fails:** narrow the document set or fix the write boundary **before exposing anything over MCP** — an MCP server that can overwrite files is a worse failure than a missing document.

### G.4 M4 — Developer integrations and opt-in runtime (P20–P23)

#### P20 — MCP server over stdio (capped tool surface) · Milestone M4 · Size L
- **Objective:** Expose the library over MCP stdio with a capped tool surface and documents as resources.
- **Scope / non-goals:** In: the six tools only; model-generated JSON Schemas; the tool-result envelope with the 11-code problem catalogue; opaque cursors and fixed sort orders; workspace path confinement; documents as resources; `runtime_disabled` and `run_expired` semantics; the thin-adapter rules. Non-goals: a seventh tool; MCP prompts; SSE or HTTP; any mutating tool; patch generation or verification; business logic in the adapter.
- **Key deliverable:** the MCP server + generated tool schemas + in-process client tests + the two-call and import-guard tests proving the client boundary.
- **Dependencies:** P19.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **low MCP-SDK familiarity widens the range**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-17, FR-22; AC-10, AC-13; ADR-4; F10, F11; contract 3 (§E.3).
- **Tests / acceptance criteria:** a seventh tool fails the registry test; schemas regenerate byte-identically from the models; each tool exercises success and the `validation_error`, `permission_denied`/`unsafe_command_refused`, `not_found`/`run_expired`, and `run_in_progress`/`resume_conflict`/`ir_schema_mismatch` paths; an out-of-workspace path is refused; page 2 via a cursor equals the same slice of a full listing; documents are listed as resources with `IRIS.md` absent when inapplicable; `inspect_runtime_metrics` returns `runtime_disabled` when unconfigured; no tool mutates a file or Redis state.
- **Definition of done:** six tools register with model-generated schemas, every catalogue code is reachable by a test, and no tool can write outside the run directory except through the document-write boundary.

#### P21 — MCP verification: Inspector, client walkthrough, config documentation · Milestone M4 · Size M
- **Objective:** Verify the MCP surface against real tooling and document setup honestly.
- **Scope / non-goals:** In: an Inspector session, a documented real-client walkthrough, workspace `.mcp.json` documented **as the** config file, the explicit note that the legacy per-IDE location is deprecated and not read directly, Workspace Trust and per-invocation-confirmation troubleshooting, and the six-tool surface justified against the 128-tool cap. Non-goals: claiming universal interception; a bespoke protocol harness; assuming the in-memory transport class name (confirmed here).
- **Key deliverable:** a verification record + user-facing setup documentation.
- **Dependencies:** P20.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0; **client availability is an external dependency**. *Forecast — not a measurement and not a commitment.*
- **Serves:** A-5, R-3, R-8; AC-13; ADR-4; U-9.
- **Tests / acceptance criteria:** the Inspector session succeeds and lists exactly six tools; the walkthrough is documented **as proposed**; the docs reference the workspace config file only and name the deprecated one only as deprecated; a recorded statement that availability depends on client discovery, not on EZ-Redis; no doc claims a measured token or latency figure.
- **Definition of done:** the Inspector session and a real-client walkthrough are recorded (labelled per FR-28) and the config-based setup docs are published.

#### P22 — Opt-in read-only live-Redis inspector · Milestone M4 · Size L
- **Objective:** Provide opt-in, read-only live inspection with a gate that cannot be bypassed.
- **Scope / non-goals:** In: opt-in configuration; a TLS connection with username/password; the pure gate function supporting both axes plus a runtime capability cross-check; fail-closed handling of unknown or drifting capability; the diagnostics sub-allowlist with per-command caps; refusals carrying their axis and reason code; consume-only keyspace notifications; secret-safe logging; an operator ACL recipe. Non-goals: any mutating, administrative or unbounded command; enabling notifications; the administrative/admin families; hard-coding command flag sets; logging connection strings or key values.
- **Key deliverable:** the runtime package + the policy gate + integration tests + operator guidance.
- **Dependencies:** P05.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **a supplied or local Redis instance is a prerequisite**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-20, FR-21; AC-15; ADR-8; F5–F8; T3.
- **Tests / acceptance criteria:** table-driven gate tests refuse `KEYS`, `CONFIG SET`, `CONFIG GET`, `CLIENT LIST`, `MONITOR` and `DEBUG` with the **right axis**; `INFO` is reachable only via the diagnostics profile; a pre-6.0 capability set degrades with a reason code; the gate refuses a command even when the ACL would permit it; an opt-in integration test against a supplied Redis is **skipped-and-reported** when absent; a log scan proves no connection string or key value is logged.
- **Definition of done:** every mutating, administrative or unbounded command is refused with the correct axis, the gate is pure and table-tested, and the secret-scan log test passes. **Rollback:** the runtime package is additive; disabling it leaves static analysis complete (FR-19 holds).

#### P23 — Incremental analysis and safe result caching (≤ 5 s single file) · Milestone M4 · Size L
- **Objective:** Re-analyse a single changed file fast, without changing full-run semantics.
- **Scope / non-goals:** In: hash-based changed-file detection, IR patching with an invalidation closure (the cross-file joins are rebuilt globally), selective rule re-run, a persisted symbol index, cold-start disclosure, cache invalidation on schema/version drift, and drift refusal on schema, ruleset, config and tool version. Non-goals: distributed caching; a durable job queue; changing the full-run path.
- **Key deliverable:** the incremental path wired into the CLI and library, with a measurement.
- **Dependencies:** P18, P19.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **the symbol-index rebuild is the identified risk (U-3)**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-24; AC-18; F14; U-3, R-9.
- **Tests / acceptance criteria:** a single-file change re-analyses in the recorded time, with cold/warm stated and measured-versus-estimated labelled; a stale IR is refused on a schema-version mismatch; **the incremental result equals a full re-run on the same input** (the correctness bar, independent of speed); the slice-sufficiency property holds (perturbing an IR section outside a rule's declared inputs does not change its output); drift refusal fires for each of the four version fields; change detection is hash-based (mtime is not authoritative).
- **Definition of done:** the equivalence test passes; the timing is recorded with its cold/warm condition, or the target is renegotiated with the user. **Rollback:** the incremental path is behind a flag; the full-run path is unchanged.

**Gate G4 (M4) — go/no-go.** **Evidence to pass:** (a) the Inspector session and a documented client walkthrough are recorded, and the tool surface is ≤ 8 (it is 6); (b) the live-Redis gate refuses every mutating and administrative command in the table with the correct reason and axis; (c) incremental analysis meets the target on the fixture with the cold/warm condition stated, **or** the target is renegotiated with the user and the condition documented; (d) the incremental-equals-full equivalence test passes; (e) the opt-in Redis integration passes **or** is a reported skip (never a pass). **Action if it fails:** reduce or split the tool surface further; if the safety tests fail, **disable the runtime module entirely and ship static-only** (FR-19 still holds) rather than shipping a gate with an escape hatch; if the 5 s target is missed only because of cold start, document the condition rather than weakening correctness.

### G.5 M5 — Evaluation, quality bar and hardening (P24–P26)

#### P24 — Labelled measurement corpus and labelling protocol · Milestone M5 · Size L
- **Objective:** Build the measurement instrument QA needs: a versioned corpus and an unambiguous labelling protocol (owns §H.2/H.3 content).
- **Scope / non-goals:** In: representative Python/JS/TS/TSX repositories; adversarial fixtures (injection in README, comments and config; oversize; malformed; symlink escape; secrets in config); labels per rule and category; the labelling protocol (who labels, tie-breaking, what is a true positive, how `needs_confirmation` is scored); corpus versioning; the held-out split. Non-goals: measuring precision yet (P25); self-generated code; the per-rule developer fixtures owned by P09–P14.
- **Key deliverable:** a versioned **labelled** corpus + the protocol document + labelling fixtures.
- **Dependencies:** **P08, P14, P15** (every rule family must exist before it can be labelled; P14 is the last rule phase).
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **corpus sourcing may add wall-clock (R-9)**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-23, A-9; AC-17; U-11, R-4; F4.
- **Tests / acceptance criteria:** the labelled corpus covers every rule with positives and negatives, including the "looks like a violation but is correct" case; the protocol defines precision unambiguously enough that two independent labellers agree; adversarial fixtures exercise the injection, size, malformed and non-UTF-8 paths, reusing the `.gitignore`-reserved oversize fixture; a test asserts every fixture has a provenance record and none was produced by the tool under test; inter-labeller agreement is reported per category.
- **Definition of done:** a versioned labelled corpus and protocol exist and independently reproduce the same labels on a spot-check set.

#### P25 — Measure precision (≥ 90 %) and benchmark both latency targets · Milestone M5 · Size L
- **Objective:** Replace every estimate with a measurement — or report honestly that it could not be measured (owns §H.4/H.5/H.6 content).
- **Scope / non-goals:** In: per-rule and overall precision against the labels; rule tightening or withdrawal below the bar; the 100 k-LOC end-to-end benchmark and the single-file benchmark; hardware, corpus revision and interpreter recorded; every number labelled measured; disclosed limitations; the rule-outcome register. Non-goals: claiming a target is met before measuring it; tuning on the test set without recording it; redefining a metric that was missed.
- **Key deliverable:** a measurement report + withdrawn/tightened rules + the recorded gate decision.
- **Dependencies:** **P23, P24** (the 100 k-LOC benchmark needs the complete path, including the CLI and the incremental wiring, on top of the corpus).
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **a 100 k-LOC fixture and a suitable machine may not be immediately available**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-23, FR-24; AC-17, AC-18; U-3, U-11, R-4.
- **Tests / acceptance criteria:** precision is reported overall **and** per rule, with corpus revision and protocol revision, with a Wilson interval (the gate uses the **Wilson 95 % lower bound ≥ 0.90**, and `needs_confirmation` findings count as false positives); any rule below the bar is tightened or withdrawn and recorded in the rule-outcome register; both latencies are reported with hardware and conditions, cold and warm separated, ≥ 5 repetitions and a spread; if measurement was impossible, the metric is reported as **unmeasured**, never as passed; the ≤ 5 s number is quoted only if the equivalence test passed.
- **Definition of done:** a measurement report exists with hardware and conditions, sub-bar rules withdrawn, and unmeasurable items labelled unmeasured. *Rollback: not applicable — evidence-only.*

#### P26 — Hardening: limits, timeouts, adversarial resilience, security review, observability · Milestone M5 · Size M
- **Objective:** Make the deterministic core robust under adversarial input and bounded failure.
- **Scope / non-goals:** In: timeouts and cancellation at every external boundary; file-size, iteration, depth and recursion caps expressed as named ceilings; a per-file parse budget with a cancellable parse; atomic manifest write and a run lock; graceful partial failure; adversarial-input handling end-to-end; document and log secret-leak scans; supply-chain review of the pinned set (including the inconsistent `libcst` licence metadata and avoiding the LGPL `astroid`); the observability surface with its redaction suite; the reason-code completeness matrix; and the bounded-failure invariant BF-1. Non-goals: new capability; tuning beyond the measured bar; any network dependency; adding a circuit breaker, bulkhead or outbound rate limiter (there is no volume for them to work on, and Jev calls are batched into one request).
- **Key deliverable:** hardening changes + a security review record + a failure-injection test run + the reason-code completeness matrix + the redaction scan report.
- **Dependencies:** P18, P22.
- **Relative size:** M (3–5 sessions).
- **Calendar estimate (indicative):** ~1.5 wk (range 1–2.5 wk). Assumptions: A0. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-28, NFR-6, NFR-7; AC-22; OWASP LLM01; F1–F24; BF-1; §I; FR-14(e).
- **Tests / acceptance criteria:** adversarial fixtures produce no side effect and no policy change; every cap and timeout is asserted as a `(ceiling, items_considered, ceilings_hit)` record, never a silent truncation; BF-1 holds with `runtime/`, `ai/` and `agent/` unimportable and with the network disabled; every external boundary has a deadline-nesting test naming the bound that fired; the log, document and JSON secret scans return **zero hits** on a planted-secret fixture; a logging failure cannot fail a run; every reason code in the catalogue is reachable and asserted; determinism excludes only the declared volatile fields; the dependency review records advisory status, licence and triage for every pinned package.
- **Definition of done:** the adversarial and failure-injection suites pass, timeouts are tested at each boundary, the dependency review is recorded, and each unrun row is reported with its reason — never as passed.

**Gate G5 (M5) — go/no-go.** **Evidence to pass:** (a) measured precision overall and per rule against the frozen revisions, with rules below the bar withdrawn or tightened and disclosed, and inter-labeller agreement reported; (b) both latency targets measured with hardware and conditions, or explicitly reported as **unmet with a renegotiation request** to the user; (c) the adversarial and failure-injection suites pass; (d) the secret-leak scans are clean; (e) the dependency/licence/advisory review is recorded; (f) determinism is proven. **Action if it fails:** **do not ship a rule set whose precision is unknown** — withdraw or tighten the failing rules and report the reduced scope honestly; if the ≥ 90 % bar is unreachable within the planned phases, return to the user with the measured numbers and a proposed renegotiation rather than silently redefining precision.

### G.6 M6 — Optional AI layers (P27–P28) — late, optional, droppable

#### P27 — Jev decision layer behind an internal interface (late-optional) · Milestone M6 · Size L
- **Objective:** Optionally consult Jev over a bounded evidence summary under a bounded call budget, with the deterministic answer computed first and never replaced.
- **Scope / non-goals:** In: a bounded question builder over a reduced evidence summary; the provider SDK behind an interface; a pinned model in config; response validation; all arithmetic in code; the deterministic fallback as a first-class return value; a total stage budget with 2 attempts, full-jitter backoff, `retry-after` honoured only if it fits, one retry per run and the SDK's own retry policy set to a single attempt so exactly one layer retries; pre-send payload reduction against the body and token ceilings; cost and token accounting; adversarial-content filtering; the go/no-go on cost, licence and zero-data-retention. Non-goals: whole-repository or whole-IR dumps; free-text generation; letting an answer authorise an action, set a threshold or bypass the deterministic path; making the product depend on Jev.
- **Key deliverable:** the AI package + stubbed tests + a cost estimate + the gate record.
- **Dependencies:** P25.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk). Assumptions: A0; **no local Jev/SDK experience and unresolved cost/licence widen the range**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-18, D-5; AC-13; ADR-6; U-4, U-5, U-6; F4, F9.
- **Tests / acceptance criteria:** stub tests cover out-of-set answers, invalid responses, timeouts, `429` with `retry-after`, `529` and no-candidate — **each asserts `fallback=deterministic`, `source="deterministic"`, zero exceptions and a still-complete run**; a persistent `529` makes exactly 2 attempts, never 4; the payload stays inside the body and token ceilings, and exceeding them is a pre-send reduction rather than a send; no numeric question is sent to the model; BF-1 holds with `ai/` unimportable; the cost estimate and licence/retention decision are recorded **and user-approved** before enabling.
- **Definition of done:** every documented failure mode returns the deterministic path as a value (never an exception), and the phase is enabled only after recorded user approval of cost, licence and retention. **Rollback:** the AI layer is behind an interface; disabling it returns the shipped deterministic product unchanged.

#### P28 — LangGraph orchestrator over the core (final-optional, explicitly droppable) · Milestone M6 · Size L
- **Objective:** Decide — and if adopted, implement — a bounded agent over the core, without bypassing deterministic analysis.
- **Scope / non-goals:** In: the gate decision against the explicit criterion (durable, cross-process, resumable, multi-step, human-approved tool execution); if adopted — bounded graph state, node responsibilities, routing, stopping conditions, bounded retries, approval gates, persisted run state, an explicit recursion limit (well below the provider default) and at most one tool execution per declared tool, plus the guarantee that it never replaces or bypasses the core. Non-goals: autonomy over high-risk changes; silently applying changes; replacing the core; being required by any other phase.
- **Key deliverable:** either a recorded **"not adopted"** decision with the deterministic orchestrator shipped, or an agent implementation with bounded, inspectable state.
- **Dependencies:** P27.
- **Relative size:** L (6–10 sessions).
- **Calendar estimate (indicative):** ~3 wk (range 2–5 wk) if adopted; **0 wk if dropped (expected)**. Assumptions: A0; **no LangGraph experience**. *Forecast — not a measurement and not a commitment.*
- **Serves:** FR-18, D-5; AC-13; ADR-6; R-5, U-12.
- **Tests / acceptance criteria:** the gate decision is recorded with evidence; if adopted, tests cover tool failure, invalid recommendations, retries, approval requirements and **recursion exhaustion returning partial results rather than raising**; a test proves the agent path never bypasses the deterministic engine; BF-1 holds with `agent/` absent; recursion and tool-execution caps are asserted as named ceilings with a `limits_exceeded` record for every cap that fires.
- **Definition of done:** the adoption decision is recorded with its evidence; if adopted, the no-bypass test passes; if not, the deterministic orchestrator is recorded as the shipped answer. **Rollback:** dropping the phase costs no other phase anything — nothing upstream depends on it.

**Gate G6 (M6) — go/no-go.** **Evidence to pass:** (a) a recorded cost plus licence/retention decision (user-approved); (b) the deterministic fallback demonstrated on every Jev failure mode; (c) the LangGraph criterion evaluated and the decision recorded. **Action if it fails — the expected outcome:** drop the Jev phase and/or the LangGraph phase and ship the deterministic product, which is complete without either (FR-19, ADR-6). Dropping these phases costs no other phase anything, because nothing upstream depends on them.

### G.7 A–K ↔ phase mapping (FR-15 / AC-11)

**Per-phase → A–K sections.** P01→B,D,K · P02→C,K · P03→C,D,E · P04→E,G · P05→C,I,K · P06→C,D,K · P07→C,D,K · P08→D,G,H · P09→C,G · P10→C,G · P11→C,G · P12→C,G · P13→C,F,G · P14→C,G · P15→C,E,G · P16→F,I,K · P17→C,E,K · P18→C,I,K · P19→A,C,D · P20→A,C,E · P21→C,I,J · P22→G,I,J · P23→G,H,J · P24→H,J · P25→H,J,K · P26→H,I,J · P27→D,G,J · P28→D,G,J.

**Reverse mapping — nothing orphaned.** **A**←P01,P19,P20 · **B**←P01 · **C**←P02,P03,P05,P06,P07,P09–P15,P17–P21 · **D**←P01,P03,P06,P07,P08,P19,P27,P28 · **E**←P03,P04,P15,P17,P20 · **F**←P13,P16 · **G**←all 28 · **H**←P08,P23,P24,P25,P26 · **I**←P05,P16,P18,P21,P22,P26 · **J**←P21–P28 · **K**←P01,P02,P05,P06,P07,P16,P17,P18,P25.

## H. Evaluation and Benchmarking

> The content below is folded in **verbatim** from `plans/qa_test_plan.md` **Part A** (QA-owned; the agreed heading contract is H.1–H.6). QA owns this material; the phases that implement and measure it are **P24** (corpus and labelling protocol) and **P25** (precision and latency measurement), verified at gate **G5**. Everything in it is a target, a threshold, a method or a rule — **never a result**: both latency targets and the ≥ 90 % precision bar are **unmeasured**.

> *[Verbatim block begins: `plans/qa_test_plan.md` Part A — §H content, heading contract H.1–H.6.]*

## H.1 What is measured, and what is not

| Measure | Target/threshold | How decided | Status today |
|---|---|---|---|
| **Precision** of reported findings | **≥ 90 %** true positives (micro-average) | formula over the **labelled measurement corpus** (§H.3/H.4) | **unmeasured** — default target requiring validation (FR-23, A-9, R-4, U-11) |
| **Full analysis, 100 k LOC** | **≤ 60 s** | end-to-end CLI/library run over the pinned ≈100 k-LOC corpus; cold + warm reported separately (§H.5) | **unmeasured** (U-3) |
| **Incremental, single changed file** | **≤ 5 s** | `analyze --incremental` after one file change, warm run directory, cold start reported separately (§H.5) | **unmeasured** (U-3) |
| **Incremental-equals-full equivalence** | exact equality | incremental result is byte-identical to a full re-run on the same input (§H.1a) | correctness bar for P23, independent of speed |
| **Determinism** | byte-identical across runs | same input ⇒ identical IR/findings/documents | design requirement, testable |
| **Correctness of refusals / safety** | specified | gate + write-boundary + failure-injection suites (§Part E) | specified, not yet run |

**H.1a Incremental-vs-full equivalence (P23 correctness bar).** Given input I and a single changed file Δ, assert `analyze_incremental(I, Δ)` is **byte-identical** to `analyze_full(I with Δ applied)` in IR, findings and documents. Speed without equivalence is a wrong answer delivered fast; this is a G4 pass condition.

**Unmeasurable in this task (explicit list — `PLAN.md` must not read as if verified):**
1. **≤ 60 s / 100 k-LOC** — unmeasured.
2. **≤ 5 s single file** — unmeasured; cold-start condition unresolved.
3. **≥ 90 % precision** — unmeasured; corpus (§H.2) and protocol (§H.3) not built.
4. **tree-sitter 0.26.0 co-load with grammar wheels 0.25.0/0.25.0/0.23.2 on 3.12/3.13** — ABI table says yes, **not executed** (U-2); confirmed by the P08 load smoke test (`abi_version ≤ 15`).
5. **Redis integration behaviour** — no instance connected (A-3, R-9); F5–F8 unexecuted.
6. **Jev cost and behaviour** — no call made (U-4/U-5/U-6); SDK version, cost acceptance and DPA/ZDR unresolved.
7. **MCP client walkthrough** — not performed; documented manual step (R-3, A-5).
8. **The four ADR-1 parser measurements** — parse headroom, call-site resolution rate, single-file re-parse — **not taken** (U-1); due at P08.

**Baseline suite.** Repository is greenfield (no `pyproject.toml`, no tests) **[verified: root holds only `.git/`, `.gitignore`, `.pi/`, `docs/`]**, so `qa/baseline.json` records `not_executed` with reason "no test/lint/type-check commands exist" — there are **no pre-existing failures** to blame, and any future failure is by definition newly introduced.

## H.2 Fixture corpus and versioning

**Owner: qa** (`tests/fixtures/**`, `tests/integration/**`, `tests/adversarial/**`).

**Two artefacts, never conflated** (also resolves objection O-1):
| Artefact | Author | When | Purpose |
|---|---|---|---|
| **Per-rule developer fixtures** | rule owners | **inside P09–P14** | unit inputs: ≥1 positive + ≥1 negative per rule; keeps M2 unblocked |
| **Labelled measurement corpus** | qa | **P24** | the instrument from which precision is computed |

**Representativeness.** Languages **Python / JavaScript / TypeScript / TSX**, file-count proportions **≈ 45 / 20 / 20 / 15 %** [assumption — confirm against expected target repos]. Every language carries ≥1 Redis-using repo and ≥1 **true-negative** repo (no Redis). Redis call shapes that must appear:
| Language | Client libraries / call shapes |
|---|---|
| Python | `redis-py` (`redis.Redis`, `redis.asyncio`, `.get/.set/.setex/.expire/.delete/.hset/.lpush/.incr`, `.pipeline()`, `.multi()`), connection pools, f-string keys, `redis-agent-memory` call sites |
| JS/TS/TSX | `ioredis` (`new Redis()`, `.multi()`, `.pipeline()`, `.setex`), `node-redis` v4+ (`createClient()`, `.multi()`); the same shapes in **TS and TSX** (second grammar, R-6) |
| All | literal keys; template/f-string keys with literal prefix + dynamic segment; keys from variables/config; wrapper/decorator indirection; cross-file cache-aside (read vs write/invalidate in different files) |

**Positives and negatives per rule:** every rule family (H.2a) has ≥1 fixture that **should** fire and ≥1 that **should not**, including the "looks like a violation but is correct" case.

**H.2a Rule families (P09–P14, 8+):** cache-aside/key-construction; TTL policy; invalidation/staleness; stampede/hot-key + rate-limiting; Redis Search/vector; connection/pipeline/transaction + serialization + memory/eviction; plus key-naming/layout and redundancy/miss categories.

**Adversarial set** (`tests/adversarial/**`, authored at P24, re-executed end-to-end at P26):
| Case | Fixture / path |
|---|---|
| Injection in `README.md`, comments, config values | injected directives must be treated as **data**; policy unchanged |
| Oversized file | **`tests/fixtures/adversarial/python/adv_oversize.py`** (reserved in `.gitignore` line 12) |
| Malformed syntax | truncated/unbalanced → `parse_status=partial/failed`, no abort |
| Symlink escape | symlink outside workspace root → refused |
| Secrets in config | Redis password, Iris store API key → never logged/written |
| Non-UTF-8 | invalid byte sequences → handled/skipped with diagnostic |
| Unsupported/new syntax | PEP 701 f-strings, TS decorators → `Unresolved`, never a silent miss |

**Versioning & invalidation.**
- **Corpus revision** = hash of (fixture tree + labelling-protocol revision + held-out split) **[proposed]**. Recorded in every measurement report.
- **A fixture/label/protocol change invalidates all prior measurements** and changes the revision; a previous number may not be quoted against a new revision and is treated as **stale**.
- **Fixtures are never generated by the tool under test.** Sources are hand-written or vendored from real OSS repos pinned to a commit with licence retained; a test asserts each fixture has a provenance record and none was produced by an EZ-Redis run.
- **100 k-LOC latency corpus** is a **separate**, pinned, ≈100 k-LOC fixture used only for H.5 (need not be labelled).

## H.3 Labelling protocol and precision definition

**Who labels / how many.** **≥ 2 independent labellers** label every finding on the frozen revision without seeing each other's labels; a **third adjudicator** (qa) resolves disagreements. A rule author **may not label their own rule's** output for the headline number (conflict of interest).

**True positive (TP)** iff, on the frozen fixture: (a) the asserted pattern is present and the evidence spans point at it; (b) the asserted defect is real **under the rule's own stated semantics** (not a stronger claim it did not make); (c) no unstated assumption is required. Otherwise **FP** (an over-claim is an FP and is additionally recorded for §H.4).

**`needs_confirmation` scoring rule (anti-inflation).** A finding with `evidence_class == "needs_confirmation"` (or whose `unresolved` list could change the verdict) is **counted as a FALSE POSITIVE** in the headline number unless and until the protocol justifies otherwise per category. **Justification:** precision claims "reported findings are true positives"; a `needs_confirmation` finding is reported but its truth is **not established**, so counting it as TP uses unearned credit. A **secondary view** reports `needs_confirmation` separately, so both **earned** precision (excluded) and **conservative** precision (included as FP) are shown; **the gate uses the conservative view**. Excluding them requires a recorded protocol revision with rationale and the alternative numbers (invalidation applies). Low-confidence **defect** findings are also conservative — scored on their asserted claim; confidence never rescues a finding (severity ≠ confidence).

**Severity handling.** Precision is computed **independently of severity**; a rule may not improve precision by down-grading severity, and a category is not measured only on high-severity findings. Precision by severity band is an extra reporting slice, not the gate.

**Tie-breaking.** Disagreement → adjudicator decides TP / FP / `needs_confirmation`. If undecidable, the label is **`needs_confirmation` ⇒ FP**. **Conservative default: ambiguity is an FP, never a TP.**

**Inter-labeller agreement.** Report **Cohen's κ per category**; publish a category's numbers only when **κ ≥ 0.70 [proposed]**; below that, revise the category's definitions and re-run. Low agreement is a rule-quality defect, not a labelling nuisance. Report per category, not only overall.

**Precision formula (machine-applied).** On corpus revision `c`, protocol revision `p`:
```
Precision(rule r)  = TP_r / (TP_r + FP_r)          # needs_confirmation_r ⊂ FP_r
Precision(overall) = Σ_r TP_r / Σ_r (TP_r + FP_r)  # micro-average, the GATE metric
Precision_macro    = mean over rules of Precision(rule r)
```
Both micro and macro are reported; **the gate uses micro** (matches "≥ 90 % of reported findings") and macro is reported so a high-volume rule cannot mask a weak one. An unlabelled finding is **not** a pass; unlabelled findings are a coverage gap and cap the verdict at **incomplete**.

## H.4 Precision measurement and rule disposition

**Computed:** per `rule_id`, per category, and overall (micro + macro), each with a **Wilson 95 % interval**, against the exact corpus + protocol revisions.

**Minimum fixture counts for the number to mean anything [proposed].**
- A rule's precision is publishable only at **n ≥ 30 reported findings** on the frozen corpus; below 30, report **low-confidence** and pool at category level.
- The **gate passes a rule only if the Wilson 95 % lower bound ≥ 0.90** (stricter than the point estimate). Overall is qualified by total labelled-finding count and by how many rules individually meet the bar.

**A rule below the bar is tightened or withdrawn — and the decision is recorded.**
- If point estimate < 0.90 **or** Wilson lower bound < 0.90: **tighten** (narrow the claim to what the evidence supports, or route ambiguous inputs to `needs_confirmation`) or **withdraw** (deregister). A caveat-in-place is not allowed.
- Recorded in a **rule-outcome register**: `{rule_id, corpus_revision, protocol_revision, TP, FP, precision, wilson_low, n, decision: tightened|withdrawn|meets_bar, rationale, evidence_ref}`.
- A tightened rule is **re-measured on the same frozen revision**; the old number is superseded, not deleted.
- If a category loses its last meeting rule, the category is **withdrawn with reason** (G5): the plan does not ship a category whose precision is unknown.

**Prohibition on tuning against the labelled set.**
- Measuring → editing rules → re-reporting the **same** frozen-revision number **without recording the iteration is prohibited**. Any post-result rule change is recorded as **corpus-informed tuning** with the corpus revision used, the change, and re-measurement on the **same revision** (iteration count disclosed) or on a **held-out split / next revision**.
- The corpus carries a **held-out split**; the **held-out** numbers are those quoted for the gate, the tuning-split numbers are reported separately. Reporting tuning-split numbers as held-out is the specific dishonesty this rule prevents.

**Claim discipline.** Overall and per-rule precision are labelled **measured** only after P25 runs, with corpus revision, hardware, interpreter and date. Until then every precision statement is **proposed/unmeasured**.

## H.5 Latency benchmark procedure

**Common to both targets:** record **CPU model + core count, RAM, OS + version, disk type, filesystem, idle-ness**; **Python 3.12 and 3.13** (the baseline; 3.14 is **not** a target); **tool commit hash, corpus revision, date/time**; **≥ 5 repetitions**, report **median + min + max + stddev** and state variance. A target is "met" only if the **median** meets it **and** max is disclosed; a pass on the min alone is not a pass.

| Target | Setup | Reporting |
|---|---|---|
| **≤ 60 s / 100 k LOC** | end-to-end `ezredis analyze <100k corpus>` (discovery→adapters→IR→rules→findings→recommendations→documents→output, incl. run-dir writes) | wall-clock; **cold** and **warm** rows separate |
| **≤ 5 s / single file** | warm run directory over a representative repo, change **one** file, `analyze --incremental` (Flow 2) | (a) **warm, excluding cold start**; (b) **end-to-end incl. cold start** — separate rows. Target evaluated against (a); (b) disclosed. Miss caused only by cold start is documented as a condition, not used to redefine the metric |

**Cold vs warm, always separate.** Every latency number records **cold** (fresh process, empty caches, first run) and **warm** (repeat run) as **separate rows**; a single blended number is not acceptable evidence. **The 5 s target is the one cold start can ruin**, so both rows are mandatory for it.

**Correctness precondition.** The ≤ 5 s number is meaningful only if the **H.1a equivalence test passes**.

## H.6 Reporting rules (measured vs estimated; miss handling)

- **Labelling:** every latency/precision number is labelled **measured** (only after P25, with corpus revision + hardware) or **estimated/proposed** otherwise. A number with no matching current corpus revision is **stale** and may not be quoted.
- **A missed target reports the measured number and requests renegotiation from the user** — it **MUST NOT** be silently passed, and its **metric MUST NOT be redefined**. Specifically forbidden: shrinking "100 k LOC", loosening "≤ 60 s"/"≤ 5 s", dropping cold start to flatter the warm number, reporting the min as the result.
- A missed target moves the milestone gate to a **documented no-go with a renegotiation request**; the number and request are the evidence.
- If measurement is **impossible**, the metric is reported **unmeasured** — never as passed.
- **Routed facts encoded as checks:** CI measures on **3.12 and 3.13 explicitly** (Python 3.12 security-only since 2025-04-02, EOL 2028-10-31; 3.13 security-only since 2026-10-01, EOL 2029-10-31 — do not float to the newest interpreter); the P08 smoke test asserts all four grammars load with **`abi_version ≤ 15`**.


## I. Security and Operational Readiness

Security here is architectural, not bolted on: the point of boundaries B1–B6 (§C.3) is that the file-write, Redis-socket and model-call capabilities each live in exactly one place, so the requirements that depend on them are **structurally checkable** rather than aspirational. This section states the trust boundaries, the enforcement points, the live-Redis refusal policy, the write boundary, the secret-handling invariants, the enumerated failure modes, the operator guidance and the supply-chain posture.

### I.1 Trust boundaries (T1–T6)

| # | Untrusted → trusted | Control (enforcement point) | Residual risk / open | Test | Phase |
|---|---|---|---|---|---|
| **T1** | analysed workspace content → the analyser | content is **data, never instructions**; parsing is read-only; **path confinement** to the workspace root with symlink and `..` refusal (EP-5); size, depth and iteration caps; contents are not retained after parse | mount/bind escape semantics `[assumption]` | adversarial tree test | P02 / P26 |
| **T2** | repository content → Jev / LangGraph | injections need not be human-visible, only parsed, and the provider does not treat adversarial content as hostile by default; therefore **cap and filter** what enters the model's state (EP-3), keep policy, prompts and thresholds in code, validate the output, and never let an answer authorise an action | which content shapes count as instruction-shaped `[unresolved]` (decide at P27) | payload assertion test | P26 / P27 |
| **T3** | EZ-Redis → live Redis (the tool is the untrusted caller of a production system) | opt-in only; **two-axis allowlist** plus a runtime capability cross-check (EP-2); **fail-closed**; per-command caps; TLS with username/password; a documented least-privilege ACL recipe; refusal is the default for anything mutating, administrative or unbounded | exact administrative-command flag sets `[unresolved]` (read from the live server at P22) | table-driven refusal matrix | P22 |
| **T4** | EZ-Redis → filesystem | write boundary (EP-1): owner identity, target allow-list, generated-file marker, workspace and output-directory confinement, refuse-and-report; the reserved coordinator channel is never written; run-directory confinement (EP-6) | output-directory misconfiguration | pre-edited-file and symlink-escape tests | P16 / P23 |
| **T5** | MCP client → EZ-Redis | stdio inherits OS process identity; tool arguments are validated by generated JSON Schema; `path` is confined (EP-5); no mutating tool; a capped tool surface; the runtime tool needs a named profile else it returns `runtime_disabled` | client-side discovery and confirmation are outside our control | cap and path tests | P20 |
| **T6** | generated documents → later analysis / model context | documents are **outputs**: they carry provenance and are re-validated against source, never trusted as instructions; a secret scan precedes every write (EP-1) | "poisoned memory" through a stale or hand-edited document | staleness and re-validation tests | P16 / P26 |

### I.2 Authorization enforcement points (EP-1…EP-6)

Each is the **single** place its capability can be exercised, which is why it cannot be bypassed; each returns a structured refusal rather than an exception.

| EP | Module owner | The single-entry property | Who may call it | Return on refusal | Phase |
|---|---|---|---|---|---|
| **EP-1 Write boundary** | `policy/` (security) | one predicate consulted by the only writer | documents, CLI, the MCP analyze tool | a write report listing refused `{path, code, axis}` | P16 |
| **EP-2 Live-Redis gate** | `policy/` + the runtime dispatcher (security) | every command issued only from the dispatcher, each passing the pure gate | runtime only | `unsafe_command_refused{command, axis, reason}` | P22 |
| **EP-3 AI egress gate** | the egress builder + the AI package | only the reduced-summary builder may construct a payload | AI only | a fallback return + an egress-refused diagnostic | P27 |
| **EP-4 MCP surface** | `mcp/` | exactly the six declared tools; documents are resources, not tools | MCP | an envelope problem code | P20 |
| **EP-5 Workspace confinement** | `discovery/` + the path predicate (security supplies it) | every path from a human or tool argument passes one confinement predicate | discovery, CLI, MCP, runtime | a path-outside-workspace refusal | P02 / P20 / P22 |
| **EP-6 Run-directory confinement** | the analysis run writer | all run state lands under the run directory via one atomic-write helper | analysis stages, exporter | a refusal with a limits or run-state diagnostic | P05 / P23 |

The architecture names EP-1…EP-4; **EP-5 and EP-6 are the security consultation's additions**, closing the path-confinement and run-state holes that would otherwise sit one call site away from EP-1/EP-2.

### I.3 The two-axis read-only live-Redis policy

**Allow predicate (a decision, not an algorithm):** allow **iff** A-flag ∧ A-cat ∧ A-sub (when the command is scoped) ∧ A-cap ∧ A-bound. One axis per refusal reason code (§E.8e) so a test can assert the **right** reason, not merely a refusal.

| Axis | Source of truth | Allow condition | Rationale |
|---|---|---|---|
| **A-flag** `readonly` | the server's `COMMAND` reply, per command | flag present | excludes everything that mutates data |
| **A-cat** ¬`@dangerous` | `COMMAND` ACL categories | category absent | excludes commands that are read-only **yet** dangerous |
| **A-sub** subcommand scope | `COMMAND` subcommands + server version | the scoped subcommand itself satisfies A-flag and A-cat | `CONFIG GET` is safe while `CONFIG SET` is not; per-subcommand rules need a Redis 7.0+ server |
| **A-cap** capability present | the `COMMAND` reply and server version | both axes are derivable from the reply | a pre-6.0 server carries no ACL categories, so the tool degrades rather than silently assuming safety |
| **A-bound** cost/volume | client-side caps (scan iterations, slowlog count, memory samples, response bytes) | budget not yet exhausted | O(N) commands are bounded rather than merely "read-only" |

**A runtime capability cross-check is mandatory** because the client allowlist is a *claim* and the server reply is *evidence*: a curated list drifts from the server (renamed command, module command, version difference). Disagreement fails **closed**; a missing or unparseable entry also fails closed. Module commands especially need this, because the `@all` category never covers them.

**Why `KEYS`, `INFO`, `CONFIG GET` and `CLIENT LIST` are special.**

| Command | Why a single-axis rule is wrong | Policy |
|---|---|---|
| `KEYS` | read-only **yet** dangerous — O(N) over the whole keyspace; an axis-1-only allowlist **over-permits** it | deny by default; `SCAN` is the bounded substitute |
| `INFO` | does **not** mutate but carries **no `readonly` flag at all** — so the flag axis cannot decide, and a "not dangerous" reading **under-permits** it | deny by default; reachable **only** from the explicit diagnostics sub-allowlist |
| `CONFIG GET` | non-mutating, yet the `CONFIG` family's write member is how keyspace notifications get enabled; scoping `CONFIG` safely needs a Redis 7.0+ server | deny by default; admissible only under the diagnostics profile; `CONFIG SET` is **never** issued |
| `CLIENT LIST` | non-mutating but **discloses other clients' addresses and names** — a leakage risk, not a mutation risk | deny by default |

`MONITOR`, `DEBUG`, `CLIENT KILL` and `SHUTDOWN` are read from the live `COMMAND` reply at runtime and never hard-coded; diagnostic commands such as `SLOWLOG GET`, `LATENCY LATEST`, `MEMORY USAGE`, `SCAN`, `OBJECT ENCODING` and `TTL` are allowed **only** with the A-bound per-command caps. **Keyspace notifications** are consumed only if the operator already enabled them; enabling them is a configuration write, so the tool never attempts it, and if the read of the notification setting is itself refused, detection is reported as best-effort/unknown and is never escalated to an attempt.

**Budgets (proposed; the values exist so the arithmetic is closed, not because they were measured).** Connect and TLS handshake ~2 s; connection acquire ~2 s; per-command read/response ~2 s; total inspection budget ~10 s enforced by one monotonic deadline, with every sub-bound the minimum of the configured value and the remaining time minus a margin. Scan iterations, slowlog count, memory samples and response bytes each have a named cap; the unbounded "all samples" form is forbidden. **No command is retried internally** — a read is repeatable, but an internal retry would change elapsed time without changing the answer; the operator re-runs. Exact redis-py timeout parameter names are `[unresolved]` and are to be confirmed against the pinned redis-py version at the start of P22.

### I.4 The write boundary and the AI egress gate

**B5 write boundary (control terms).** The decision inputs are: an owner identity that must match the marker (else refuse, so another writer's document is never overwritten); a **target allow-list** of the four document filenames in the configured output directory (no other path is ever writeable); a **generated-file marker** that must be present and matching (a hand-authored file is never overwritten); workspace and output-directory confinement after symlink resolution; and a **secret precondition** (a rendered document containing an unredacted secret is refused). A refusal **appends to the refused list and does not abort the run**: partial success is reported and other documents are still generated. The predicate is consulted by the single writer module; rules, document generators and MCP tools have **no write capability of their own**.

**B4 AI egress gate (control terms).** Only the reduced-summary builder may construct a request body, which closes the "one import away" hole. The payload is capped over a closed set of IR facts and findings — never a whole IR, whole repository, whole file, or evidence-span text beyond the recorded span. Analysed text is quoted as **data** in a clearly delimited field, and policy, prompts and thresholds live in code. The answer must map into the closed pattern set and the expected response shape, else it is discarded. **Authority ceiling:** no answer may authorise an action, set a threshold, bypass a rule or promote the evidence class. A secret-bearing config reference refuses the call. Any unavailability, invalid response, out-of-set answer or timeout returns the deterministic path as a **normal return value, not an error**.

### I.5 Secret handling — classes and invariants

| Class | Where it can appear | How it is represented | In logs / summary | In generated documents |
|---|---|---|---|---|
| Redis password / ACL credential | connection config, environment, analysed config files | never stored — a redacted config reference `{path, symbol, redacted=true}` | `<redacted>` | a config **symbol** only |
| TLS material (key path, passphrase) | config | redacted reference | `<redacted>` | the certificate **path** may be shown; the passphrase never |
| Iris store id and bearer credential | analysed source, environment | redacted reference | `<redacted>` | referenced redacted, never the value |
| Redis key **values** | live Redis | never read — value-returning commands are outside the allowlist | never logged | never |
| Auth tokens / API keys found in the analysed repo | analysed files | redacted reference | `<redacted>` | never |
| Repository file **contents** | analysis | contents are not retained after parse | spans and line ranges, not text | short, span-bounded evidence quotes only |
| Connection string (host, port, user, password) | runtime config | not stored | host/port may appear, user/password `<redacted>` | never |

**Redaction invariants (I-S1…I-S8).** **I-S1** no secret value is ever stored in the IR. **I-S2** no secret value reaches a log line, the run summary or diagnostics; redaction happens in **one** log-sink choke point, not at each call site. **I-S3** no secret value is copied into a generated document; documents reference config symbols. **I-S4** no secret value is sent to the model. **I-S5** a **document scan** and a **log scan** run in tests over a fixture repository with planted secrets, and both must return **zero hits**. **I-S6** redaction is a boundary property, so a new template or log call cannot forget it. **I-S7** the scanner set is fixed and fixture-driven — an entropy-only heuristic is **not** relied upon `[unresolved]`, to be decided at P26. **I-S8** generated documents are never consumed as instructions; they carry provenance and are re-validated against source.

### I.6 Enumerated failure modes (F1–F24) and the bounded-failure invariant

Each failure names the **bound that fires** and the reason code it emits. A stage that caps or skips without a matching record is a defect asserted against in P26's tests.

| # | Failure | User-visible behaviour | Recovery (bounded) | Reason code | Phase |
|---|---|---|---|---|---|
| F1 | Unparseable / partially parseable file | the file is listed with its parse status and the run summary gives the count; findings for it are marked unknown, never omitted | continue; record an unresolved parse-failure; never abort the run | `parse_failed` | P06, P07 |
| F2 | Grammar/core ABI mismatch | adapter initialisation error naming the language and the ABI | pin the tree-sitter core at 0.25.x per ADR-1 | — | P08 |
| F3 | Workspace too large / huge generated file / symlink loop | bounded run + explicit diagnostic + a `degraded` marker | skip-with-report above the cap | `file_skipped_oversize`, `size_cap_exceeded`, `iteration_cap_exceeded` | P02, P26 |
| F4 | Adversarial repository content (injection, oversize, crafted) | **zero** behaviour change on the deterministic path | content is data; policy in code; on the AI path an out-of-set output is discarded | `response_out_of_set` | P24, P26, P27 |
| F5 | Live Redis unreachable / TLS / auth failure | `runtime_unavailable` with a remediation hint; static analysis unaffected | the runtime module is additive; findings degrade from combined to static; never fatal | `dependency_unreachable` / `_tls_failed` / `_auth_failed` | P22 |
| F6 | A requested command is refused by the gate | `unsafe_command_refused{command, axis, reason}` | refuse and explain; widening only via an explicit profile | `command_refused_by_gate` | P22 |
| F7 | Pre-6.0 server (no ACL categories) | degraded codes: flag-only checks, no category axis | degrade with a documented message; **never assume safety** | `unf_command_flag_axis_unavailable` | P22 |
| F8 | Keyspace notifications disabled | "notifications not enabled; prevalence unknown" with the evidence | report unknown; **never** enable them | `obs_keyspace_notifications_unknown` | P22 |
| F9 | Jev throttling / overload / timeout / invalid / no candidate | the source stays `deterministic`; uncertainty is raised; the AI path is reported **unavailable, not failed** | bounded retries honouring `retry-after`, then fall back — the fallback **is** the return value | `dependency_throttled_429` / `_overloaded_529` / `dependency_timeout` / `budget_exhausted` | P27 |
| F10 | Run directory missing/expired at an MCP call | `run_expired` plus the command to re-analyse | reject; **no implicit re-analysis** | `not_found` / `run_expired` | P20 |
| F11 | MCP surface grows past the cap | tools stop being offered / are virtualised | a hard cap enforced by a test that fails on a seventh tool | — | P20 |
| F12 | Write-boundary conflict (a user edited a generated document) | the refusal list shows the path and reason; nothing is overwritten | refuse with a regeneration path; never overwrite user edits | `permission_denied` + a refusal record | P16 |
| F13 | Partial / interrupted run | the manifest records the last completed step; a re-run resumes deterministically | idempotent steps; re-run is safe; no distributed state | `run_interrupted` / `run_resumed` | P05, P23 |
| F14 | Version drift between a stored IR and the current rules | the load is **refused** with both versions shown | re-analyse, or a documented migration; **never interpret an old IR with new rules silently** | `ir_schema_mismatch` / `schema_version_mismatch` | P03, P23 |
| F15 | Pathological input hangs the parser (deep nesting, huge single expression, adversarial token soup) | the file is marked partial/failed with a timeout reason; the run continues; `degraded=true` | cancel the parse, record an unresolved parse failure and continue; **or** pin 0.25.x to retain a parse timeout | `parse_timeout` | P06, P07, P26 |
| F16 | Run-directory write failure (disk full, permission, partial manifest) | the run fails **with** the reason; if the manifest is unwritable, exit 1 with stderr detail | write to a temp file on the same filesystem then atomically replace; a truncated temp is discarded, never adopted | `internal_error` | P05, P26 |
| F17 | Double retry layer on the optional AI dependency | latency inflation only, unless the deadline is breached | **one** retry layer (ours); the provider SDK's own retry is set to a single attempt and the effect is asserted in a stub test | `budget_exhausted` if the deadline is breached | P27 |
| F18 | Recursion-limit exhaustion in the agent graph | the agent run stops with **partial** results and a stated reason; the deterministic report is still produced | treat it as a **bounded stop**: catch, mark partial, publish deterministic results, never crash the process | `limits_exceeded` | P28 |
| F19 | Concurrent runs against one run directory | the second process gets a run-in-progress problem naming the holder; no interleaving | an exclusive lock file, or unique per-invocation run ids | `run_in_progress` | P05, P26 |
| F20 | AI payload ceiling exceeded | a clipped summary is reported, never silently sent | reduce deterministically **before** send; if reduction cannot reach the ceiling, fall back rather than send | `payload_over_limit` | P27 |
| F21 | Invalid question shape | fall back, **and** emit a visibility diagnostic so the defect is visible | never retry a non-transient rejection; fix the question builder | `response_invalid` (non-retryable) | P27 |
| F22 | A diagnostic command exceeds its per-command cap | a partial diagnostic with the ceiling recorded; "the keyspace was fully scanned" is never asserted | cap iterations and the count; stop the cursor; report coverage, not a total | `iteration_cap_exceeded` | P22, P26 |
| F23 | The MCP client disconnects mid-run (broken pipe) | the client sees a closed stream; the run directory remains consistent and resumable | finish the atomic write first; no partial JSON to the broken pipe | `internal_error` / `run_interrupted` | P20, P26 |
| F24 | A stale generated document consumed as truth (poisoned memory) | the document is flagged **stale** in the run report; not silently trusted | compare recorded source hashes on each run; re-validate against source | `degraded` marker + a staleness record | P16, P26 |

**Invariant BF-1 — static completeness.** With **every** optional dependency absent, disabled, unreachable or answering wrongly, the deterministic static path completes and produces the full IR, findings, recommendations and applicable documents; the only differences are `degraded=true`, the named reason codes, and the absence of runtime/AI enrichment. **No finding may disappear and no document may be skipped because an optional dependency failed.** Asserted by six cases: the runtime module unimportable; Redis unreachable; the AI module unimportable; the AI dependency throttling, erroring and timing out; the agent absent; and the network entirely disabled.

**Corollary — findings never silently vanish.** Every rule that fails, times out or is skipped produces a `(rule_id, reason_code)` record, and the summary carries rules expected / completed / skipped plus a `findings_complete` flag. A run whose findings are incomplete may never be presented as a clean result: the summary and the CLI both say so, and `--strict` turns it into a non-zero exit (§E.8b).

### I.7 Observability, and what is deliberately absent

**The surface (all local; zero egress).** Eight channels: the human run summary; the machine run summary (a `--json` projection); the structured JSON event stream; the run manifest; the refusal list; the unresolved roll-up; the parse-failure list; and the document provenance headers. The four things a user needs to *distrust results correctly* — the summary, the unresolved roll-up, the parse-failure list and the refusals — must never be summarised away.

**Redaction enforcement.** One choke point — the event serializer — applies a typed deny list, a value deny pattern over every string, and a length bound on `detail` to stop accidental source dumps. The `workspace_root` is the single documented exception and appears only in the local manifest; everywhere else the display basename is used. No environment values are ever serialised; a refused command logs its name, axis and reason but never its arguments.

**The liftable FR-19 statement.** *No metrics backend, no distributed tracing, no telemetry egress.* EZ-Redis is a local developer tool with no collector, no scrape endpoint and no tracing backend. Core analysis performs **no network I/O of any kind**: no exporter, no metrics endpoint, no vendor agent, no crash reporter, no usage analytics and no version-check or update ping. The only outbound traffic the product can ever produce is the opt-in, gated live-Redis connection (P22) and the late-optional reduced-evidence summary (P27); neither is telemetry, neither is enabled by default, and disabling both leaves the product complete.

**Health, readiness and SLIs are deliberately absent.** There is no long-running server in the slice, so liveness/readiness endpoints do not apply — the substitutes are the manifest status, the run-state problem codes and the `version` subcommand. There is no metrics backend for dashboards or alerts, so the substitutes are the run summary and the event stream. No SLI is claimed and no alert rule is authored: **the two NFR targets are measured from the recorded per-stage durations and environment block, and the precision bar is measured per rule** — a recorded comparison, not a histogram. The one observability non-negotiable that survives is **fail-open logging**: if the event stream cannot be written, the run continues and reports the degradation; no logging call may raise into analysis.

**Runtime diagnostic sources** (reachable only through the explicit diagnostics sub-allowlist with per-command caps): the slowlog (counts and event names only, with a bounded count — its arguments are server-redacted), the latency-monitor events (the cheap signal, available only if the server configured a latency threshold), and keyspace-notification **state** (consumed, never enabled). Each has its own reason code when unusable.

### I.8 Operator guidance — least-privilege ACL recipe

This is **documentation for the operator**; EZ-Redis never connects with administrative credentials to apply it, and the **server-side ACL is a backstop — the client-side gate is primary**: a test asserts the gate refuses a command even when the ACL would permit it, so a misconfigured ACL is not the only control.

Create a dedicated principal with a secret from the environment (never the default user); drop inherited key patterns (`resetkeys`) and confine the key space to the prefixes the analysis found; start from `-@all` then `+@read` rather than inheriting categories; **remove `@keys`** (the read-only-but-dangerous O(N) command); remove `@dangerous` (`FLUSHALL`, `MIGRATE`, `RESTORE`, `SORT`, `KEYS`, `CLIENT`, `DEBUG`, `INFO`, `CONFIG`, `SAVE`, `REPLICAOF`); add explicit `-@write -@admin` denials as defence in depth; allow the capability cross-check query (`+command`); allow read-only config inspection (`+config|get`) and deny the notification-enabling write (`-config|set`) — noting that per-subcommand rules need a Redis 7.0+ server, otherwise deny the whole family; remove the administrative families (`-client -monitor -debug -shutdown`); and, only when the operator enables the diagnostics profile, allow the bounded diagnostics with their per-command caps. **Never `+config|set`.** The exact directive ordering and the exact flag/category membership of the administrative commands are `[unresolved]` and are read from a live server at P22 rather than hard-coded.

### I.9 Supply chain

The review is recorded at P26; **no audit tool has been run here**, and the values below are research findings to be re-verified at the pinned versions. Triage outcomes: an advisory in the shipped set **blocks** the phase gate until upgraded or removed; an obligation-bearing licence (LGPL/AGPL) needs a recorded legal decision, because attribution is not a substitute; inconsistent licence metadata means **read the actual `LICENSE`** and treat "unknown" as unresolved, never permissive; an unpinned or non-locked install is prohibited (`uv sync --frozen` against a committed lock); and a missing PyPI attestation is a recorded note, not a block. Concretely: `pylint`/`astroid` must not enter any group (LGPL), and `libcst`'s licence must be read before adoption (§D.5).

## J. Risks, Trade-offs, and Unresolved Questions

Every item below **carries a recommended default** (FR-29 / AC-23). Items settled by research are marked **settled** and must not be re-opened as open questions; items that remain open are marked **open** and name the phase that will resolve them.

### J.1 Risks and open questions (R-1…R-14)

| ID | Risk / question | Status | Recommended default (the answer to use if nobody decides otherwise) |
|---|---|---|---|
| **R-1** | Which libraries parse and validate on the 3.12–3.13 baseline, and whether wheels exist for the locally installed 3.14 | **settled for selection, open for confirmation** | Keep the 3.12–3.13 baseline; tree-sitter primary with the four confirmation measurements at **P08**; fallback is pinning the tree-sitter core at 0.25.x, then the LibCST/TS-API deepening tiers |
| **R-2** | What "IRIS" refers to | **settled** | Iris is Redis's AI-product umbrella, materialised today as Redis Agent Memory; `IRIS.md` is generated conditionally on detection and never emitted empty (ADR-9). Only the per-repository contents remain an implementation step |
| **R-3** | Whether MCP can be verified without a bespoke harness | **settled** | Verify at **P21** via the official Inspector plus a documented real-client walkthrough plus a thin in-process client; no bespoke protocol harness |
| **R-4** | Whether ≥ 90 % precision is achievable and measurable | **open** | Keep the bar; define the corpus and labelling protocol at **P24**, measure at **P25**, tighten or withdraw rules below the bar; if unreachable, return the measured numbers to the user with a renegotiation proposal — **never silently redefine precision** |
| **R-5** | Whether the LangGraph agent adds value over deterministic workflows | **open** (expected answer: no) | Keep it as the **last, droppable** phase (**P28**) with the explicit adoption criterion; default is the deterministic orchestrator |
| **R-6** | Whether JS, TS and TSX need one grammar family or separate adapters | **settled** | One adapter module covering JS/TS/TSX, but TS and TSX are **distinct parsers and both must be wired**; a TSX-only fixture test prevents the second grammar being forgotten (**P07**) |
| **R-7** | What Jev can do, and its licensing, pricing and service requirements | **partly settled** | Keep Jev late-optional (**P27**); assert no capability beyond the documented primitives; gate the phase on user approval of the cost estimate and the licence/retention review; the deterministic fallback is the default |
| **R-8** | Whether 20–30 phases in only 5–7 milestones keep each gate meaningful | **open** (author's judgement) | 28 phases / 6 milestones as designed; M1–M5 carry decisive gates, M6 is the droppable tail. If more than 30 phases are ever needed, **add milestones rather than shrink phases** |
| **R-9** | Whether the user or the plan provisions a Redis instance for later phases | **open** | Assume a developer-supplied or locally provisioned instance; **P22's integration test is skipped with a reported skip when absent**, and the skip is never counted as a pass |
| **R-10** | Whether the 1,500–2,500-line bound matches "extremely high level" | **open** | Keep the bound; the user may renegotiate at approval. Move long detail into compact tables, never drop content |
| **R-11** | Whether mandatory-but-indicative calendar estimates are acceptable | **open** | Apply D-7 literally: every phase carries an estimate labelled **indicative**, with assumptions, an uncertainty range and a not-a-measurement/not-a-commitment statement |
| **R-12** | Whether the required section C/D/E/I depth fits inside the unchanged line bound | **open** | Resolved by design: hold the bound and buy depth with density; if the bound proves unreachable, surface it to the user at approval rather than silently exceeding it |
| **R-13** | Whether the named roster specialists are available and what counts as identifiable consultation output | **open** | The roster marks consulted versus excluded; exclusions carry a reason; nothing is labelled `[verified]` unless the output exists |
| **R-14** | Run-directory location and lifetime | **open** | Default to the **OS user cache directory** with an explicit override, so the analysed repository is never polluted; retention defaults to "keep until an explicit purge" |

### J.2 Unresolved questions (U-1…U-13)

| ID | Question | Recommended default |
|---|---|---|
| **U-1** | The achievable Redis call-site resolution rate per language — the number that sets semantic depth | Measure at **P08**; the design consequence is already applied (the provenance and unresolved axes exist because this number is not 100 %) |
| **U-2** | Whether the tree-sitter core co-loads with the grammar wheels on 3.12/3.13 | The four-language load smoke test at **P08**; fallback pins the core at 0.25.x |
| **U-3** | Whether 100 k LOC fits 60 s and one file fits 5 s | Measure at **P08** (parse headroom) and **P25** (end-to-end); disclose cold start for the 5 s target; every figure before measurement is **estimated** |
| **U-4** | The provider SDK version and its Python constraints | Read the package metadata and changelog at the start of **P27**; treat the version as to-be-confirmed and do not invent one |
| **U-5** | The AI cost per full analysis and user acceptance | Estimate from a prototype call on one fixture at **P27**; gate the phase on the user's budget approval |
| **U-6** | Data-protection/retention sufficiency for sending source-derived content to a third party | Default: acceptable for non-sensitive code, with enterprise zero-retention only; a **user/legal decision before P27 is enabled** |
| **U-7** | The exact flag and category membership of the administrative commands | Do not hard-code: read flags and categories from the live `COMMAND` reply at **P22**; deny by default until confirmed |
| **U-8** | Whether a maintained SARIF 2.1.0 validation library exists | Write the exporter against the spec and validate with a general schema validator at **P17**; adopting a library is optional and revisitable |
| **U-9** | Whether the MCP SDK exposes a documented in-memory transport for tests | Confirm the class name during **P20**; if absent, use the Inspector plus a stdio-subprocess client |
| **U-10** | Whether a vendored per-command metadata snapshot is viable for offline mode | Best-effort vendor of a pinned snapshot for offline validation; the live capability cross-check remains authoritative at runtime (**P22**) |
| **U-11** | Whether ≥ 90 % precision is achievable | Same as R-4: corpus and protocol at **P24**, measurement at **P25**, conservative reporting as the mechanism |
| **U-12** | Whether LangGraph is worth adopting at all | The deterministic orchestrator is the default; **P28** is gated and droppable |
| **U-13** | The exact scope of `IRIS.md` for repositories that do use Iris | The investigation is the first step of the Iris work; default content: SDK detection, session versus long-term tiers, TTL/promotion configuration, retrieval call sites, redacted credential references |

### J.3 Trade-offs accepted, and what was deliberately not done

| Trade-off | Accepted cost | Why it is right here |
|---|---|---|
| **syntax-only baseline depth** (tree-sitter + heuristics + a one-hop symbol index) rather than type-aware analysis | some dynamic keys, wrapper indirection and cross-file flow are only partially resolvable | it keeps the core fast, dependency-light and language-uniform; the IR's provenance and unresolved axes make the limit **visible** rather than masked, and the deepening tiers remain available if P08 shows the rate is too low |
| **report less rather than guess** (conservative rules, `needs_confirmation` on unresolved input, `needs_confirmation` counted as a false positive at measurement) | fewer findings, and a precision number that looks worse than an optimistic one | the product's entire trust claim is precision; a rule that guesses is worse than a rule that asks |
| **no metrics backend, no tracing, no telemetry egress** | no dashboards, no burn-rate alerts, no distributed traces | there is no service to page and no collector; the run summary, refusals, unresolved roll-up and parse-failure list are the honest substitute for telemetry |
| **no circuit breaker, bulkhead or outbound rate limiter** | no per-dependency resilience statistics | those mechanisms need volume a local tool does not have (a handful of AI calls per run, one Redis connection, one process); the correct control is a retry budget, an attempt cap and a total deadline |
| **documents are projections, not advice** | longer, less chatty documents; a document with nothing to report is not emitted | a document that states an unevidenced recommendation is indistinguishable from a model answer, and the prompt's own rule forbids empty or irrelevant documents |
| **MCP surface capped at six tools** | some capability is reachable only by parameterising a tool rather than by a dedicated one | it respects the client's tool budget and per-turn context cost, and keeps each tool's schema meaningful |
| **the optional AI tail is last and droppable** | the product ships without the "intelligent" layer by default | it keeps an unverified external service off the critical path and makes D-5's "droppable" real rather than rhetorical |
| **not done:** patch generation and verification | the tool proposes; it does not edit the developer's source | excluded by the user; excluded again here so no reader infers the door was left open |
| **not done:** Java adapter, FastAPI service, IDE extension, runtime telemetry correlation, GUI | narrower language and integration coverage in the initial slice | each is a later candidate; adding them now would trade depth for breadth in a plan whose value is an ordered path |

### J.4 Disclosed tensions and amendments

1. **The applicability rule deviates from a literal reading of "include all four documents."** FR-22 is satisfied by the phase existing plus the conditional rule, exactly as the plan already argues for `IRIS.md`; an always-emitted placeholder is rejected (§F.1). A reviewer who prefers the literal reading must say so explicitly, because the two cannot both hold.
2. **The precision gate is stricter than requested.** QA proposes gating on the **Wilson 95 % lower bound ≥ 0.90** rather than the point estimate. The user's requirement was "≥ 90 % of reported findings are true positives", which a point estimate satisfies; the lower-bound form additionally requires the worst plausible precision at the measured sample size to clear 0.90. **The user may accept it or relax it to the point estimate**; either way the gate, the corpus and the method are stated (§H.4).
3. **The milestone count is 6 rather than 5**, so the optional AI tail is a genuinely separable, droppable unit with its own gate — still inside the 5–7 bound.
4. **The original prompt's phase field list is reconciled with the nine required fields** by folding "technical approach" into *Key deliverable*/*Scope* and appending a compact `Rollback:` clause to *Definition of done* for state-changing phases. No content is lost and no length bound is violated.
5. **The 60 s stage allocation has no margin as first drafted.** Recommended default: cap parsing at 15 s and IR assembly at 12 s, leaving an 8 s margin, and record the discarded 8 s as the margin line rather than hiding the tension (§I.3 budgets; RZ-A2). A 5 s margin does not exist in the naive split, and the design cannot satisfy its own nesting rule without this adjustment.
6. **Two small dependency needs are requested, not assumed:** a timeout plugin and a fake-clock library for the failure-injection suites are **not yet in the approved dev set**; they must be approved before P26 rather than added silently.
7. **Nothing in this plan was measured, built, installed, benchmarked or integrated** — including the consultations, which are design reviews of this document and are never cited as evidence that code, tests or an integration works (FR-28).

## K. Final Implementation Checklist

An ordered list of the proposed work, with the gate that closes each stretch, plus the requirement-coverage table, the acceptance-criteria self-check for **this document**, and the file-ownership map. The plan is complete when every item below is ticked **with quoted evidence**; a milestone gate may not be passed on an unverified item.

### K.1 Ordered checklist

| # | Work | Phase | Gate that closes it |
|---|---|---|---|
| 1 | uv package skeleton, pinned 3.12–3.13 baseline, lint and types, CI, the no-network import guard | P01 | — |
| 2 | Deterministic discovery, language detection, encoding verdicts, caps, escape refusal | P02 | — |
| 3 | Shared Redis IR: validated, provenance-carrying, deterministic, versioned | P03 | — |
| 4 | Finding record: evidence classification, severity ≠ confidence, `needs_confirmation` | P04 | — |
| 5 | Analysis engine, rule registry, run directory, run log, resume and idempotency | P05 | **G1** |
| 6 | Python adapter (tree-sitter-python) → IR facts | P06 | — |
| 7 | JS/TS/TSX adapter (two grammars) → IR facts | P07 | — |
| 8 | Parser decision confirmed by four measurements; conformance harness; load smoke test | P08 | **G2** |
| 9 | Rule families: cache-aside and key construction; TTL policy; invalidation and staleness; stampede and rate limiting; Search and vector; connection/pipeline/transaction, serialization, memory — **per-rule developer fixtures authored in-phase** | P09–P14 | **G2** |
| 10 | Deterministic recommendation layer with alternatives, trade-offs, constraints and questions | P15 | — |
| 11 | The four document generators and the enforced write boundary (conditional, never-empty `IRIS.md`) | P16 | **G3** |
| 12 | Canonical JSON export and the secondary SARIF 2.1.0 exporter | P17 | — |
| 13 | CLI with the documented exit codes, and the importable library API | P18, P19 | **G3** |
| 14 | MCP server over stdio with the capped tool surface and documents as resources | P20 | **G4** |
| 15 | MCP verification: Inspector, real-client walkthrough, workspace config documentation | P21 | — |
| 16 | Opt-in read-only live-Redis inspector: two-axis gate, capabilities cross-check, caps, refusals | P22 | **G4** |
| 17 | Incremental analysis with the invalidation closure and the **incremental-equals-full** equivalence test | P23 | **G4** |
| 18 | Labelled measurement corpus and the labelling protocol (dependencies: **P08, P14, P15**) | P24 | — |
| 19 | Measure precision and benchmark both latency targets; withdraw or tighten sub-bar rules (dependencies: **P23, P24**) | P25 | **G5** |
| 20 | Hardening: limits, timeouts, adversarial resilience, security review, observability polish | P26 | **G5** |
| 21 | Jev decision layer behind an interface, with the deterministic fallback as a return value | P27 | **G6** |
| 22 | LangGraph adoption decision — and, only if adopted, a bounded orchestrator | P28 | **G6** |
| 23 | Reproduce this section's coverage table and the acceptance-criteria self-check against the finished implementation | all | — |

**Completion conditions.** Every item is ticked with **quoted evidence**; each milestone gate's evidence list is satisfied or the gate is honestly recorded as a no-go with a renegotiation request; every phase's definition of done is met; and no item is claimed as done on the strength of an estimate. **Dropping P27 and P28 at G6 is a successful outcome, not a failure** (ADR-6).

### K.2 Requirement coverage (FR/NFR → the phases that serve them)

| Requirement | Phases that serve it |
|---|---|
| **FR-1…FR-5** (one deliverable, no implementation, no other file, pre-write check, "nothing built" statement) | task-level; stated in the front matter and §B |
| **FR-6…FR-9** (20–30 phases, stable ids in dependency order, 5–7 milestones, one gate each) | §G (P01–P28, M1–M6, G1–G6) |
| **FR-10, FR-11, FR-12** (nine fields per phase, indicative estimates, terseness) | every phase box in §G |
| **FR-13** (A–K retained, phase list in §G) | the whole document; §G |
| **FR-14** (four contracts + five interfaces, no pseudocode) | §E; P03, P04, P05, P15, P20 |
| **FR-15** (A–K ↔ phase mapping) | §G.7; the appendix |
| **FR-16** (layout and package name) | §C.1 |
| **FR-17** (target slice) | P02–P20; §C.2 |
| **FR-18** (Jev late-optional, LangGraph final and droppable) | P27, P28; §C; §J |
| **FR-19** (no network, no AI provider, no LLM, no live Redis) | §C.3 (B1); P01 (import guard), P05; §I.7 |
| **FR-20** (opt-in, read-only, refusal behaviour) | P22; §C.5; §I.3 |
| **FR-21, FR-22** (self-generated writes only; four documents; conditional never-empty IRIS; patches excluded) | P16; §F; §I.4 |
| **FR-23** (≥ 90 % precision with a corpus and method) | P24, P25; §H.1, §H.3, §H.4 |
| **FR-24** (both latency targets with measurement conditions) | P08, P23, P25; §H.1, §H.5 |
| **FR-25** (3.12–3.13 + uv, 3.14 excluded) | P01; §D.5 |
| **FR-26** (parser recommendation, alternatives, confirming evidence, named deciding phase) | P08; §D.1, §D.2 |
| **FR-27** (dependency groups separated) | §D.5 |
| **FR-28** (every claim labelled) | every section; the label key in the front matter |
| **FR-29** (unresolved items with defaults) | §J.1, §J.2 |
| **FR-30** (demonstrated consultation) | the front-matter roster; the reconciliation table |
| **FR-31** (depth by density, bound unchanged, terse boxes) | §C, §D, §E, §I; every phase box in §G |
| **NFR-1** (1,500–2,500 lines) | this document's length |
| **NFR-2** (box length ≤ 20, median ≤ 15) | every phase box in §G |
| **NFR-3** (phase/milestone/gate counts) | §G; G1–G6 |
| **NFR-4** (nine fields on every phase) | every phase box in §G |
| **NFR-5** (repository footprint) | the task-level check; §K.4 |
| **NFR-6, NFR-7** (labelling; zero unperformed work presented as done) | the label key; the front-matter disclosure; §J.4.7 |
| **NFR-8** (no duplicate ids, no dangling references) | §G phase ids and dependency edges |
| **NFR-9** (estimates labelled with assumptions and uncertainty) | every calendar estimate in §G |

### K.3 Acceptance-criteria self-check for this document

| AC | How this document satisfies it |
|---|---|
| **AC-1 / AC-3 / NFR-5** | the pre-write check was run and reported clean before authoring; after authoring the filtered `git status --porcelain -- . ':!.pi'` returns exactly `?? PLAN.md` (§K.4) |
| **AC-2** | §B states plainly that no component has been implemented |
| **AC-4** | `PLAN.md` exists at the repository root only; no copy elsewhere |
| **AC-5 / NFR-3** | §G carries 28 unique phase ids (P01–P28) across 6 named milestones, each milestone ending in exactly one gate naming its evidence and its failure action |
| **AC-6 / NFR-4** | every phase box carries all nine fields (objective, scope/non-goals, key deliverable, dependencies, relative size, calendar estimate, serves, tests/acceptance criteria, definition of done) |
| **AC-7 / NFR-9** | every calendar estimate is labelled **indicative**, names its assumptions, gives an uncertainty range, and states that it is a forecast, not a measurement and not a commitment |
| **AC-8 / NFR-2** | every phase box is ≤ 20 lines (median ≤ 15), with no per-file design detail and no pseudocode |
| **AC-9** | all eleven sections appear, in the prompt's order and titles, with the numbered phase list in §G |
| **AC-10** | §E carries the four field-level contracts and the five interface-level specs, with no algorithm or per-rule pseudocode; the only fenced blocks are a generated-schema illustration, two layout illustrations, and §H's measurement definition |
| **AC-11** | §G.7 and the appendix map every phase to one or more A–K sections |
| **AC-12** | §C.1 carries a proposed repository layout and the package name |
| **AC-13 / AC-14** | the target slice is ordered core → IR → adapters → CLI/library → MCP; Jev is late-optional and LangGraph final and droppable; §C.5 states the core runs with no network, no AI provider, no LLM and no live Redis |
| **AC-15** | §I.3 states read-only is the default, only two-axis read-only commands are permitted, and mutating or configuration-changing commands are refused without explicit authorisation |
| **AC-16** | §F plans all four documents with `IRIS.md` conditional and never empty, and states that patch generation and verification are excluded |
| **AC-17 / AC-18** | §H states the ≥ 90 % bar with a defined corpus and method, and both latency targets with their measurement conditions, each labelled unmeasured |
| **AC-19 / AC-20 / AC-21** | §D.5 states the 3.12–3.13 + uv baseline and excludes 3.14; §D.1/§D.2 give the parser recommendation, alternatives and confirming evidence with the decision at P08; §D.5 separates the dependency groups |
| **AC-22 / NFR-6 / NFR-7** | the label key plus per-section labels; a 20-claim sample finds every capability, benchmark, integration and consultation statement labelled, and zero unperformed work presented as completed (the manual audit is QA's, in A2) |
| **AC-23** | every item in §J.1 and §J.2 carries a recommended default |
| **AC-24** | the length is within 1,500–2,500 lines |
| **AC-25 / NFR-8** | phase ids are unique and every dependency reference resolves (verified in §K.4) |
| **AC-26** | the front-matter roster marks every entry `consulted` or `deliberately excluded with a reason`, attributes contributions, and records the conflicts and their reconciliation |
| **AC-27** | the added depth is carried as tables and interface specs concentrated in §C/§D/§E/§I, paid for by prose cuts in the front matter and §A/§B/§J/§K, with every phase box still terse |

### K.4 Task-level evidence to record on completion

- **FR-4 pre-write check:** `PLAN.md` was confirmed **absent** at the repository root before authoring, so no conflict existed and nothing was overwritten.
- **Pre-write footprint:** `git status --porcelain -- . ':!.pi'` returned **empty** before authoring; the raw unfiltered `git status --porcelain` showed only the pre-existing untracked `.pi/` entry. The clean "before" value is what makes the AC-1 attribution argument valid.
- **Post-write footprint:** `git status --porcelain -- . ':!.pi'` returns **exactly** `?? PLAN.md` after authoring — one file created, zero existing files modified. `.gitignore` was **not** edited to make this pass (FR-3).
- **Length:** the document is within the 1,500–2,500-line bound.
- **Structure:** 28 unique phase ids, 6 milestones, 6 gates, zero duplicate ids and zero dangling dependency references.
- **Fields and headings:** every phase box carries all nine fields, and all eleven A–K headings appear in the prompt's order.
- **Rollback for this task:** trivial by construction — the only project file created is `PLAN.md`, so rollback is deleting that one file; no existing file was modified, so nothing needs restoring.

### K.5 Proposed file ownership (for the implementation phase, per the architecture's ownership map)

Each shared path has exactly one owner, so two authors can never silently overwrite each other. **`devops`** owns the manifest, lockfile and CI. **`data_processing`** owns discovery, the IR and both adapters. **`caching`** owns the analysis rules and the **rule registry** (the one shared serialisation point) plus recommendations. **`backend_lead`** owns findings, documents, the CLI and the optional agent. **`security`** owns the policy/write-boundary and the runtime gate decisions as a single code owner, with `caching` reviewing command semantics. **`api_development`** owns the output exporters, the public API surface and the MCP server. **`resilience`** owns the optional AI adapter. **`qa`** owns the fixtures, integration and adversarial tests. `PLAN.md` itself is owned by `backend_lead` (this authoring task).

## Appendix — Cross-reference tables

### Appendix A. Phase → interface, gate and owner

| Phase | Contract / interface it implements or first consumes | Gate | Proposed owner | Primary A–K sections |
|---|---|---|---|---|
| P01 | config model (E.6); dependency groups | — | `devops` | B, D, K |
| P02 | — (produces the manifest the IR consumes) | — | `data_processing` | C, K |
| P03 | field-level contract 1 — Redis IR (E.1) | — | `data_processing` | C, D, E |
| P04 | field-level contract 2 — finding record (E.2) | — | `backend_lead` | E, G |
| P05 | interface spec 2 — rule interface (E.5); interface spec 4 — run directory (E.7); interface spec 5 — reason codes (E.8) | **G1** | `caching` + `backend_lead` | C, I, K |
| P06 | interface spec 1 — adapter→IR (E.4) | — | `data_processing` | C, D, K |
| P07 | interface spec 1 — adapter→IR (E.4), TS/TSX dialects | — | `data_processing` | C, D, K |
| P08 | the adapter capability declaration (E.4) confirmed | **G2** | `data_processing` | D, G, H |
| P09–P14 | rule ids and assertion ceilings (§C.6) over the rule interface (E.5) | **G2** | `caching` | C, G |
| P13 | — (also feeds `REDIS-SEARCH.md`) | — | `caching` | C, F, G |
| P15 | field-level contract 4 — recommendation record (E, E.6 spec 3) | — | `caching` | C, E, G |
| P16 | — (implements the write boundary EP-1, §I.4) | **G3** | `backend_lead` + `security` | F, I, K |
| P17 | canonical/SARIF output (ADR-3) | — | `api_development` | C, E, K |
| P18 | — (surfaces the reason-code catalogue and exit map, E.8b) | **G3** | `backend_lead` | C, I, K |
| P19 | the public API surface (R-B6-4 parity) | — | `api_development` | A, C, D |
| P20 | field-level contract 3 — MCP tool I/O (E.3) | **G4** | `api_development` | A, C, E |
| P21 | — (MCP verification and config documentation) | — | `api_development` | C, I, J |
| P22 | the two-axis gate (EP-2, §I.3) and the live-Redis refusal codes (E.8e) | **G4** | `security` (+ `caching` review) | G, I, J |
| P23 | the invalidation closure and drift refusal (E.7) | **G4** | `data_processing` | G, H, J |
| P24 | the labelled corpus and protocol (E.7 staleness inputs) | — | `qa` | H, J |
| P25 | the measurement instrument (E.7 durations and environment block) | **G5** | `qa` | H, J, K |
| P26 | the full reason-code catalogue (E.8) exercised; BF-1 | **G5** | `security` + `resilience` | H, I, J |
| P27 | the deterministic-fallback contract (E.8) and the AI egress gate (EP-3) | **G6** | `resilience` | D, G, J |
| P28 | — (agent bounds; nothing upstream depends on it) | **G6** | `backend_lead` | D, G, J |

### Appendix B. Milestone and gate summary

| Milestone | Phases | Gate | One-line pass condition | One-line fail action |
|---|---|---|---|---|
| **M1** Foundation, contracts and deterministic core | P01–P05 | **G1** | schemas validate and emit; discovery deterministic; four languages detected; import guard proves the network/AI packages unreachable; the engine seam is proven | revise the schemas and engine scope before any adapter work |
| **M2** Adapters and static analysis breadth | P06–P14 | **G2** | both adapters conform with provenance-asserting snapshots; four parser measurements recorded; every category has a rule with positive and negative fixtures; offline run | pull the deepening tiers forward per ADR-1, or narrow a category and report the gap as unresolved |
| **M3** Findings, recommendations and outputs | P15–P19 | **G3** | applicable documents produced with conditional IRIS both ways; write boundary proven; canonical and SARIF validate; CLI and library offline | narrow the documents or fix the boundary **before** exposing anything over MCP |
| **M4** Developer integrations and opt-in runtime | P20–P23 | **G4** | Inspector plus client walkthrough recorded; every mutating/admin command refused with the right axis; incremental equals full; 5 s met or renegotiated | disable the runtime module entirely rather than ship an escape hatch; document a cold-start-only miss |
| **M5** Evaluation, quality bar and hardening | P24–P26 | **G5** | precision measured overall and per rule with sub-bar rules withdrawn; both latencies measured or reported unmet; adversarial suites pass; dependency review recorded | never ship a rule set whose precision is unknown; return measured numbers with a renegotiation request |
| **M6** Optional AI layers (droppable) | P27–P28 | **G6** | cost/licence/retention decision recorded; deterministic fallback proven on every AI failure mode; the orchestration criterion evaluated | **the expected outcome:** drop P27 and/or P28 and ship the deterministic product |

### Appendix C. Security and quality acceptance-test matrix

| # | Test | Boundary | Pass condition | Phase |
|---|---|---|---|---|
| S-T1 | table-driven refusal matrix over the denied command set | live Redis | each denied command is refused with the **expected axis code** | P22 |
| S-T2 | the gate refuses a command even when the ACL would permit it | live Redis | refusal returned; no command issued | P22 |
| S-T3 | unknown / unclassified command | live Redis | an unknown-capability refusal; nothing issued | P22 |
| S-T4 | pre-6.0 capability set | live Redis | a flag-axis-unavailable refusal; no category-axis allow | P22 |
| S-T5 | log scan after a recorded-response runtime run | live Redis / logs | zero connection strings, credentials or key values | P22 |
| S-T6 | write boundary versus a pre-edited generated file | filesystem | the file is byte-identical afterwards and appears in the refused list with the right code | P16 |
| S-T7 | write boundary versus a symlink escape and an out-of-workspace output directory | filesystem | refused; nothing written outside the root | P16 |
| S-T8 | secret scan over every generated document | docs | zero planted secrets | P16 |
| S-T9 | adversarial repository content (injection, oversize, malformed, undecodable, symlink loop) | workspace | no policy or threshold change; bounded run; disclosures present | P26 |
| S-T10 | an MCP `path` argument escaping the workspace | MCP | refused; no filesystem access | P20 |
| S-T11 | AI egress payload assertion | AI | payload ⊆ reduced summary; no whole file or IR; no secrets; an out-of-set answer falls back | P27 |
| S-T12 | tool-surface cap | MCP | a seventh tool registration **fails the build** | P20 |
| S-T13 | dependency / licence / advisory review record | supply chain | every pinned package has licence, advisory status and triage | P26 |
| S-T14 | run-directory confinement under adversarial paths | filesystem | no write outside the run directory | P05 / P23 |
| DET-1 | run the same input twice and byte-compare | determinism | identical IR, findings and documents, excluding only the declared volatile set | P05 / P17 |
| BF-1 | run with the network, runtime, AI and agent modules each absent/unreachable in turn | bounded failure | the full static result is produced in every case | P26 |

### Appendix D. Complexity-budget test (why this design and no more)

| Question | Answer | Requirement / ADR it preserves |
|---|---|---|
| Does this add a deployable service? | **No** — one local package, no HTTP service | FR-19, ADR-4 |
| Does this add a server-side datastore, cache, queue or search index? | **No server-side store**; a local JSON run directory only (SQLite optional and conditional, R-14) | the simplicity heuristic; R-9 |
| Does this add runtime dependencies? | **Yes, bounded** — tree-sitter plus three grammar wheels, pydantic and click in core; a Redis client, an MCP SDK and an optional agent group | FR-27, ADR-1…ADR-4 |
| Does this add a cross-cutting abstraction? | **No** — a rule registry over a fixed IR, no plugin system and no speculative generality | the complexity budget |
| Does this add configuration options? | **Yes, small** — the language set, ignore globs, caps, document output directory, the live-Redis opt-in profile and an optional model id | the simplicity heuristic |
| Does this add asynchronous processing or eventual consistency? | **No** — synchronous, single-process, one file live at a time | the simplicity heuristic (synchronous first) |
| Does this introduce an irreversible external API? | **Yes, at field level** — the IR, finding, MCP and recommendation contracts, which are versioned and gated | FR-14, ADR-2/ADR-3 |
| Does this change a schema on a hot table? | **No tables exist** | not applicable |
| Does this add more than two specialists in one domain? | **No** — see §K.5 | the delegation budget |

---

## How to use this plan

Start at **P01** and stop at any milestone gate. Read the phase box for the objective, what is explicitly *out* of scope, what must exist when it is done, and how it will be judged — then read the gate at the end of that milestone before starting the next. If a phase's gate fails, take the failure action in the gate row rather than proceeding; every gate's failure action is designed so that failing early costs one phase, not a milestone.

**Provenance and scope of this document.** `PLAN.md` is the single deliverable of task `rd-20261019-032903-bc12`; it is authored from the approved plan revision 2 and from the artifacts and specialist inputs listed in the front matter. It **plans** the product and does not implement it: no component, dependency, test, benchmark, integration or measurement exists, and every number in it is a target, a threshold, an estimate or a research-cited fact. The eleven A–K sections, the 28 phases, the six milestones and the six gates are the plan's committed structure; everything inside them that is labelled `[proposed]`, `[assumption]` or `[unresolved]` is open to the user's decision at approval.
