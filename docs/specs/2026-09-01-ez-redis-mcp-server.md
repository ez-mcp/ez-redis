# ez-redis — MCP Server Specification & High-Level Plan

| Field | Value |
|---|---|
| **Spec version** | v1 |
| **Status** | **APPROVED v1** — user approved via recorded approval prompt on 2026-09-01 ("Approve v1 as written"). A1, A6, A7 confirmed in the same prompt and promoted to D32–D34. |
| **Date** | 2026-09-01 |
| **Author** | Brainstorm agent (requirements & architecture review) |
| **Handoff target** | Plan agent → Implementation |
| **Companion file** | `docs/specs/2026-09-01-ez-redis-diagrams.md` (Mermaid diagrams) |

> **Evidence legend.** Every material statement carries a tag so its provenance can be audited:
> `[USER]` user-stated requirement · `[DECISION]` user-approved decision after seeing tradeoffs · `[REPO]` repo-derived fact · `[EXT]` externally verified fact (source cited) · `[PREF]` user preference · `[REC]` agent recommendation (not yet a requirement unless also `[DECISION]`) · `[INF]` inference · `[ASSUME]` assumption · `[UNKNOWN]` open question · `[REJECTED]` rejected alternative.
>
> **Requirements vs. implementation suggestions.** Sections 6–8 are *requirements*. Sections 21–23 are *implementation suggestions* for the Plan agent and may be changed without re-approval unless they touch a `[DECISION]`.

---

## 1. Objective

Build **ez-redis**: a production-grade, Python MCP server plus an installable agent-hook pack that makes working with Redis in a codebase as frictionless and trustworthy as using Git. It must behave like a senior engineer pairing with the developer — surfacing correct, evidence-backed Redis guidance and optimizations at the moment they matter, and **never hindering** the developer's flow. `[USER]`

Four tools are mandatory: `search_redis`, `optimize_redis`, `redis_architecture`, `redis_conversion`. `[USER]`

---

## 2. Context

### 2.1 Repository state
- Workspace `/Users/aaishwinsathisshkumar/ez-redis` contains only `README.md` (one sentence). No source, config, tests, CI, or conventions exist. Every architectural decision is open. `[REPO]`

### 2.2 Research findings that reshaped the request

| ID | Finding | Source | Effect on design |
|---|---|---|---|
| **F1** | An MCP server **cannot see the user's prompt**. Tools are model-invoked; servers receive only `tools/call` arguments. | MCP spec 2026-07-28, *Server → Tools* ("Tools are model-controlled") `[EXT]` | "Detect when caching is mentioned in the prompt" is only achievable through **host hooks** (`UserPromptSubmit`), which are shell commands configured in the *user's* repository. ez-redis therefore ships **two artifacts**: the MCP server and a hook pack. `[DECISION]` |
| **F2** | "Middleware interception" maps to **`PreToolUse` hooks**, which receive `tool_name` + `tool_input` and may return `additionalContext`, `updatedInput`, or `permissionDecision`. | Claude Code hooks reference; VS Code *Agent hooks* docs `[EXT]` | Interception is host-mediated, not server-mediated. VS Code currently **ignores matchers** and uses different tool names/casing (`create_file`, `replace_string_in_file`, `tool_input.filePath`) than Claude Code (`Write`, `Edit`, `tool_input.file_path`). The shim must normalize. `[EXT]` |
| **F3** | MCP 2026-07-28 **deprecates Sampling, Roots, Logging**; removes protocol sessions; replaces server-initiated elicitation with **Multi Round-Trip Requests** (`resultType: "input_required"`). | MCP 2026-07-28 changelog `[EXT]` | Server cannot call the model itself; cannot rely on sessions; question-asking must be agent-mediated (see §6.3). Logging goes to stderr. |
| **F4** | The requested `search_redis` shape `{score 1–10: filename}` holds ≤10 entries and collides on equal scores. | Arithmetic on the stated contract `[INF]` | Shape inverted to a ranked list (see §6.1). `[DECISION]` |
| **F5** | `jq` adds no capability over Python's stdlib `json` + `rg --json`. | Python stdlib docs; ripgrep `--json` `[EXT]` | `jq` dropped; `rg` kept as a required binary dependency. `[DECISION]` |
| **F6** | `redis/agent-skills` (correct repo; the given URL 404'd) contains 8 MIT-licensed skills: `redis-core`, `redis-connections`, `redis-search`, `redis-semantic-cache`, `redis-clustering`, `redis-security`, `redis-observability`, `iris-development`. Their rules (KEYS→SCAN, SMEMBERS→SSCAN, HGETALL→HSCAN, pool-not-per-request, pipeline N calls, explicit timeouts, RESP3 client cache, key naming, data-structure fit) are directly usable as an offline rule/knowledge catalog. | github.com/redis/agent-skills `[EXT]` | Confirms "use the information, not the skills" is viable. Content is **paraphrased with attribution**, never vendored as skills. `[DECISION]` |
| **F7** | Upstash's 2026 caching-patterns guide covers cache-aside, write-through, write-behind, read-through; TTL + jitter; null-sentinel; stampede protection (lock / XFetch); versioned-namespace invalidation; hit-rate measurement; common mistakes (no TTL, `KEYS` in prod, no null caching, no cache-down fallback, huge values). | upstash.com/blog/redis-caching-patterns-2026 `[EXT]` | Becomes the pattern catalog for `redis_architecture` and the design-time checklist (§6.3). |
| **F8** | Official Python SDK is **v2** (`mcp>=2`), `from mcp.server import MCPServer`, Python ≥3.10, supports stdio and Streamable HTTP, structured output via type hints. | github.com/modelcontextprotocol/python-sdk README `[EXT]` | Server built on `mcp` v2 `MCPServer`. |
| **F9** | Hook output guidance: `additionalContext` should be **factual statements, not imperative system instructions** — imperative phrasing can trigger the model's prompt-injection defenses. Hook strings cap at 10,000 chars. | Claude Code hooks reference, *Add context for Claude* `[EXT]` | Hook context is phrased as facts ("This repo uses redis-py 5.x; file X calls KEYS at line 42"). |

---

## 3. In Scope (v1)

1. **MCP server** `ez-redis` (Python ≥3.11, `mcp` v2, stdio transport) exposing exactly four tools with JSON `inputSchema`/`outputSchema`. `[USER]` `[DECISION]`
2. **Core analysis engine** as a pure, importable library shared by the server and the hook shim. `[DECISION]`
3. **Hook pack** for Claude Code (`.claude/settings.json` fragment) and VS Code (`.github/hooks/*.json`), plus a Python shim entry point `python -m ez_redis.hook`. `[DECISION]`
4. **Python / redis-py static analysis** (sync `redis.Redis`, `redis.StrictRedis`, `redis.asyncio.Redis`, `ConnectionPool`, `pipeline()`). `[DECISION]`
5. **Six rule families** (§7.2). `[DECISION]`
6. **Bundled offline knowledge base** (curated from redis.io, agent-skills, Upstash) with outbound links. `[DECISION]`
7. **redis-cli command parser** + bundled command table for single-command optimization. `[DECISION]`
8. **Quality gates**: ruff, strict pyright/mypy, pytest golden files ≥90% engine coverage, MCP Inspector smoke, hook latency benchmark, pre-commit, GitHub Actions, `uv.lock`, `pip-audit`. `[DECISION]`
9. **CLI convenience** `ez-redis init --host {claude,vscode,both} [--dry-run]` that writes hook configuration into the *user's* repo after printing exactly what it will write. Explicit user action, not server behavior. `[DECISION]` (D33)

## 4. Out of Scope (v1)

- Live Redis connections of any kind (INFO, SLOWLOG, MEMORY USAGE, TTL probes). `[DECISION]`
- Server-side file writes to the user's repo (Apply/Test/Verify/Rollback). The server returns proposed diffs; the agent/host applies. `[DECISION]`
- Auto-rewriting tool input via `updatedInput`; blocking via `permissionDecision`. Hooks are **advise-only**. `[DECISION]`
- Languages other than Python; client libraries other than redis-py. `[DECISION]`
- Rule families: key-naming conventions; data-structure-fit (String-blob → Hash). `[DECISION]`
- Cache-aside sub-rules "null-sentinel" and "stampede protection" as *code detectors* (they require runtime knowledge). They live in the architecture checklist instead. `[DECISION]`
- Streamable HTTP transport, remote/team hosting, authentication. `[DECISION]`
- Live documentation fetching at call time. `[DECISION]`
- A live Redis wire-protocol proxy. `[REJECTED]`
- Use of MCP Sampling, Roots, or Logging (deprecated). `[EXT]`

## 5. Deferred (candidate v2 items, recorded so they are not lost)

| Item | Trigger to revisit |
|---|---|
| Optional read-only dynamic evidence (INFO/SLOWLOG/TTL) via `REDIS_URL` | Users request hit-ratio or hot-key evidence; requires a secrets-handling design. |
| TypeScript/JS (ioredis, node-redis), Go, Java analyzers behind the same IR | Demand; the IR seam is designed for this. |
| Streamable HTTP + auth | A team wants a shared hosted instance. |
| Native MRTR `input_required` for `redis_architecture` | Host support becomes broad in the Python SDK and major clients. |
| `redis_version` tool parameter | Users on <7.2 or needing 8.x-only suggestions. |
| Starter code generation (cache-aside helper) | After the rule engine and architecture tool are stable. |
| Key-naming and data-structure-fit rules | After v1 rules prove low false-positive rates. |

---

## 6. Functional Requirements — Tools

All tool names are lowercase snake_case per MCP tool-name guidance (SEP-986). The user's `Optimize_redis` is normalized to `optimize_redis`. `[INF]` `[EXT]`

Common to every tool `[DECISION]`:
- **Input** validated by schema; unknown fields rejected; `repo_root` must be an existing directory; every analyzed path is resolved and must remain under `repo_root`.
- **Output** is `structuredContent` conforming to a declared `outputSchema`, plus a Markdown rendering in a `text` content block.
- **Errors** are tool-execution errors (`isError: true`) with an actionable message; never a silent empty result.
- **Never** reads, prints, or returns contents of secret-like files (`.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `*secret*`, `*credential*`) and **redacts userinfo** in any `redis://` / `rediss://` URL that appears in a match (`redis://user:***@host`). `[DECISION]` `[REC]`
- **Bounded work**: hard caps on files scanned, bytes read per file, total bytes, and wall-clock; caps are constants surfaced in output metadata when hit.

### 6.1 `search_redis`

**Purpose.** Locate files in the repository that use or relate to Redis/caching, rank them by relevance to the user's request, and return that ranking as agent context. `[USER]`

**Input**
| Field | Type | Req | Notes |
|---|---|---|---|
| `repo_root` | string (abs path) | yes | Validated per §6 common rules. |
| `query` | string ≤ 500 chars | no | The user's request excerpt; boosts files whose path/content match query terms. `[DECISION]` |
| `max_results` | int 1–200, default 50 | no | Output cap. `[DECISION]` |
| `refresh` | bool, default false | no | Bypass the in-process cache. |

**Behavior**
1. Discover candidates with `rg` (`--json`, `.gitignore`-aware, `--max-filesize` capped) over a bundled term list: `redis`, `StrictRedis`, `ConnectionPool`, `redis.asyncio`, `aioredis`, `django_redis`/`django-redis`, `fastapi_cache`, `rq`, `celery` with `redis://` broker, `cache`/`caching`/`cached`, `ttl`, `expire`, `memoize`, `lru_cache`, `redis://`, `rediss://`. JSON files are searched with the same `rg` pass; no `jq`. `[DECISION]`
2. Score each file 1–10 with a **deterministic heuristic** `[DECISION]`; illustrative weights (Plan finalizes): imports a redis client +4; calls redis API +3; contains `redis://` URL +2; cache/TTL vocabulary +1; query-term overlap in path/content +2; is a test/fixture/mock file −2; is a lockfile/manifest −3. Clamp to [1, 10].
3. Return a **ranked list** sorted by score desc, then path asc. `[DECISION]`
4. **Cache** the result in process memory keyed by `(repo_root, query)`, invalidated when any candidate file's `(mtime, size)` fingerprint changes or after a 10-minute TTL; bounded to a fixed number of entries (LRU). `[DECISION]`

**Output** (`outputSchema`)
```
{
  repo_root: string,
  query: string | null,
  cached: boolean,
  truncated: boolean,          // a cap was hit
  scanned_files: int,
  results: [{
    path: string,              // relative to repo_root
    score: int (1..10),
    reasons: string[],         // e.g. "imports redis.asyncio", "calls KEYS"
    matches: [{ line: int, excerpt: string ≤ 200 chars }]  // redacted
  }]
}
```
`[DECISION]` for shape; excerpt cap `[REC]`.

### 6.2 `optimize_redis`

**Purpose.** Statically analyze Redis usage and propose optimized versions with explained differences. Three entry modes. `[USER]`

**Input** (exactly one of `command`, `snippet`, or `repo_root` must be supplied; ambiguity is a validation error)
| Field | Type | Notes |
|---|---|---|
| `command` | string ≤ 2 000 chars | A single redis-cli-syntax command (`KEYS user:*`). Parsed against the bundled command table; **unknown commands yield an explicit `unknown_command` finding, never a guess.** `[DECISION]` |
| `snippet` | string ≤ 50 KB | Python source text (used by the PreToolUse hook for the edit-in-flight and by agents for ad-hoc review). |
| `repo_root` | string | Whole-repo mode: internally calls `search_redis` to select files, analyzes each. `[USER]` |
| `paths` | string[] | Optional subset within `repo_root`. |
| `min_confidence` | enum `low\|medium\|high`, default `low` | Filter. |
| `min_severity` | enum `info\|warning\|critical`, default `info` | Filter. |

**Behavior**
1. **Parse** Python with stdlib `ast` (syntax errors → finding `unparseable_file`, continue with other files).
2. **Build IR**: `RedisCall` facts (`command`, receiver kind: client/pipeline/unknown, literal args where resolvable, `in_loop` + depth, enclosing function, cache-key heuristic flag), `ClientConstruction` facts (pool present, timeouts set, constructed inside a function/request handler), `DatastoreWrite` facts (ORM save/commit, SQL UPDATE/INSERT/DELETE heuristics) for the cache-aside rule.
3. **Apply rules** (§7.2) producing findings.
4. **Policy**: attach severity × confidence; apply filters; mark which findings are **hook-eligible** (confidence ≥ medium).
5. **Render**: for each finding produce `before`, `after`, `unified_diff`, `rationale`, `doc_refs[]`, and, where applicable, `min_redis_version`.

**Output** (`outputSchema`)
```
{
  mode: "command" | "snippet" | "repo",
  summary: { total: int, by_severity: {...}, by_confidence: {...} },
  findings: [{
    rule_id: string,           // e.g. "EZR001"
    title: string,
    severity: "info"|"warning"|"critical",
    confidence: "low"|"medium"|"high",
    hook_eligible: boolean,
    location: { path: string|null, line: int|null, col: int|null } ,
    before: string,
    after: string,
    unified_diff: string,
    rationale: string,
    doc_refs: [{ title: string, url: string }],
    min_redis_version: string | null
  }],
  truncated: boolean
}
```
`[DECISION]`

### 6.3 `redis_architecture`

**Purpose.** Produce an extensive, evidence-backed Redis architecture/plan for a repository or described system (caching pattern, key model, TTL policy, invalidation, failure modes, capacity), with Mermaid diagrams — after asking the user enough questions to understand **exactly** what they want. `[USER]`

**Interaction model.** Multi-turn, **agent-mediated**: the tool returns `status: "needs_input"` with a structured question set (id, text, options, recommended default, why-it-matters); the agent asks the user with its own UI and re-calls with `answers`. `[DECISION]` (native MRTR deferred, §5).

**Input**
| Field | Type | Notes |
|---|---|---|
| `repo_root` | string | Optional; if present, `search_redis` + IR are used to pre-fill facts (existing client, patterns, frameworks). |
| `goal` | string ≤ 2 000 chars | What the user wants (e.g., "cache product listings", "add search"). Required. |
| `answers` | object `{question_id: value}` | Answers from a previous round. |
| `assume_defaults` | bool, default false | Skip unanswered questions using recommended defaults; every default becomes a listed **Assumption** in the output. `[DECISION]` |

**Question bank** `[DECISION]`
- **Mandatory (~8):** workload type; read/write ratio; scale (RPS, key count, value size); staleness tolerance; TTL expectations; invalidation trigger (write-path, event, time); consistency needs; deployment topology (single node / Sentinel / Cluster / managed, e.g., Upstash/ElastiCache).
- **Conditional follow-ups:** hot-key expectation → stampede strategy; multi-tenant → key prefixing/ACL; search goal → RQE index fields & dialect; cluster → hash-tag requirements; write-heavy → write-behind durability tolerance.
- Questions are asked in **≤ 3 rounds**; the tool never loops indefinitely.

**Output** (`outputSchema`)
```
{
  status: "needs_input" | "complete",
  questions: [{ id, text, kind: "single"|"multi"|"text"|"number", options: [{value,label,description}], recommended: value|null, why_it_matters: string }],
  plan_markdown: string | null,        // full plan when complete
  diagrams: [{ id, title, mermaid: string }] ,  // 3–5, syntax-validated
  assumptions: [{ id, statement, source: "default"|"repo"|"user" }],
  risks: [{ statement, mitigation }],
  checklist: string[]                   // design-time items incl. null-sentinel, stampede, TTL jitter, cache-down fallback, KEYS ban, hit-ratio metric
}
```
Plan sections (mandatory when `complete`): pattern choice + rationale (cache-aside default per F7 unless answers justify otherwise); key schema (colon-separated, lowercase, tenant prefix if multi-tenant — from F6); TTL table with jitter; invalidation strategy; consistency & failure modes (cache down → fall through; ordering: DB write then cache delete — from F7); capacity/cost estimate (computed, with inputs shown); observability (hit ratio, `used_memory`, `SLOWLOG` — from F6); security notes (ACL least privilege, TLS — from F6 `redis-security`); open risks. `[DECISION]` `[EXT]`

### 6.4 `redis_conversion`

**Purpose.** Find parts of a Python application that would benefit from Redis and produce an architecture plan for them by delegating to `redis_architecture`. **Must never activate unless the user is asking to optimize the repo/application.** `[USER]`

**Trigger guard — three layers** `[DECISION]`
1. Tool description explicitly forbids unsolicited use.
2. Hook-injected context never mentions or suggests this tool.
3. Required arguments `user_requested_optimization: true` (literal) and `request_excerpt: string` (the user's words). Absent or `false` → validation error explaining why.

**Candidate detectors (v1, Python)** `[DECISION]`
| ID | Candidate | Detection sketch | Default confidence |
|---|---|---|---|
| EZC001 | HTTP handler with uncached ORM/SQL reads | Route decorator (Flask/FastAPI/Django) + DB read in same function, no redis/cache call | medium |
| EZC002 | In-process cache in server code | Module-level dict used as cache; `functools.lru_cache`/`cache` on request-path functions | medium |
| EZC003 | Counters / rate limiting via DB or memory | `UPDATE ... +1`, `.update(count=F('count')+1)`, in-memory counters in handlers | medium |
| EZC004 | Session storage in DB/filesystem | Framework session backend config = db/file | high (config is explicit) |
| EZC005 | Polling loops (sleep + query) | `while True:` containing `time.sleep` and DB read | **low** — user accepted higher false-positive risk |
| EZC006 | Leaderboard/ranking via `ORDER BY … LIMIT` | ORM `order_by(...)[:n]` / SQL `ORDER BY … LIMIT` on handler path | **low** — user accepted higher false-positive risk |

**Output.** `candidates: [{id, path, line, why, suggested_redis_primitive, confidence}]` plus the `redis_architecture` response for the top candidate group (invoking §6.3's question flow with `goal` synthesized from the candidates and `request_excerpt`). `[DECISION]`

---

## 7. Functional Requirements — Engine & Hooks

### 7.1 Core engine (simplified from the reference diagram) `[DECISION]`

```
Discover (rg) → Parse (ast) → IR (Redis facts) → Rules → Policy (severity/confidence/hook budget) → Render (diff/markdown/doc_refs)
```
- The engine is a **pure library** with no I/O beyond reading files under `repo_root` and spawning `rg`. `[DECISION]`
- **Extension seams** documented (not coded): (a) additional `Parser` producing the same IR for another language; (b) additional `EvidenceSource` feeding facts (future dynamic analysis). `[DECISION]`
- `[REJECTED]` Stub modules for Evidence Fusion / Change Manager — no callers today.

### 7.2 Rule catalog (v1) `[DECISION]`

| Rule ID | Family | Detects | Proposes | Default severity | Default confidence | Source |
|---|---|---|---|---|---|---|
| EZR001 | Full scan | `KEYS pattern` | `SCAN` cursor loop (`scan_iter`) | critical | high | F6 connections §3 |
| EZR002 | Full scan | `SMEMBERS` on unbounded set | `SSCAN` | warning | medium | F6 |
| EZR003 | Full scan | `HGETALL` on unbounded hash | `HSCAN` / `HMGET` named fields | warning | medium | F6 |
| EZR004 | Full scan | `LRANGE key 0 -1` | Paginated `LRANGE` | warning | high | F6 |
| EZR010 | Round-trips | N independent redis calls inside a loop/comprehension | `pipeline()` or `MGET`/`MSET`/`HMGET` | warning | high (same command) / medium (mixed) | F6 connections §2 |
| EZR020 | TTL | `SET` on cache-like key without `ex/px/exat/pxat` | `SET ... ex=` | warning | medium (cache-key heuristic) | F7 |
| EZR021 | TTL | `SET` followed by separate `EXPIRE` | Atomic `SET ex=` / `SETEX` | warning | high | F7, redis.io/commands/set |
| EZR030 | Connection | `redis.Redis(...)` constructed inside a function/handler/loop | Module-level client or `ConnectionPool` | warning | high | F6 connections §1 |
| EZR031 | Connection | Client without `socket_connect_timeout`/`socket_timeout` | Explicit timeouts (connect < read) | info | high | F6 connections §5 |
| EZR040 | Destructive | `FLUSHALL`, `FLUSHDB`, `DEBUG *`, `CONFIG SET`, `SAVE`/`BGSAVE`, `SHUTDOWN` in app code | Remove / gate behind explicit ops tooling | critical | high (literal) / medium (dynamic) | F6 security (command renaming) |
| EZR050 | Cache-aside | `delete(key)` before the datastore write in the same function | Write datastore first, then delete | warning | medium | F7 (Microsoft cache-aside ordering) |

Every rule ships with: golden-file tests (positive, negative, edge), a rationale paragraph, ≥1 `doc_ref`, and, if applicable, `min_redis_version`. Suggestions assume **Redis ≥ 7.2**; newer-only commands are annotated. `[DECISION]`

### 7.3 Hook pack `[DECISION]`

| Event | Fires when | Shim behavior | Output |
|---|---|---|---|
| `UserPromptSubmit` | Every prompt | Gate (a): repo depends on Redis (manifest scan, disk-cached); gate (b): prompt matches Redis/caching terms. If both pass, run `search_redis` (cached) and emit ≤ ~600 chars of **factual** context: top-N relevant files with scores, detected client/version, and a note that `optimize_redis`/`redis_architecture` are available. **Never mentions `redis_conversion`.** | `hookSpecificOutput.additionalContext`; exit 0. Silent exit 0 otherwise. |
| `PreToolUse` (file edit tools) | Before `Write`/`Edit`/`MultiEdit` (Claude) or `create_file`/`replace_string_in_file`/`insert_edit_into_file` (VS Code) | Self-filter (VS Code ignores matchers): only when target path is `.py` **and** the new content contains a Redis term. Run `optimize_redis` in `snippet` mode on the new content; emit only `hook_eligible` findings, ≤ ~600 chars. **Never** returns `permissionDecision` or `updatedInput`. | `hookSpecificOutput.additionalContext`; exit 0. |
| `SessionStart` | New session | Optional: warm the dependency-gate cache. | Nothing to context unless repo uses Redis (then one line). |

- **Latency budget:** p95 < 300 ms end-to-end per hook invocation on a 10k-file repo; measured by a benchmark in CI. `[DECISION]`
- **Dependency gate cache:** `$XDG_CACHE_HOME/ez-redis/<sha256(repo_root)>.json` storing only booleans, detected client name/version string, and manifest mtimes. Never inside the repo. `[DECISION]`
- **Manifests scanned:** `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `uv.lock`, `Pipfile*`, `setup.py`, `setup.cfg`, `environment.yml`, `docker-compose*.y*ml` (Redis service image). **Not** `.env*`. `[REC]`
- **Host normalization:** detect host by field casing/tool names; map to a common internal event. `[EXT]`
- **Failure policy:** any exception → log to stderr, exit 0 with no output (fail open for *advice*; there is nothing security-relevant to fail closed on). Timeouts inherit host defaults (VS Code 30 s; Claude 30 s on `UserPromptSubmit`). `[DECISION]` `[EXT]`

---

## 8. Non-Functional Requirements

| Category | Requirement | Tag |
|---|---|---|
| Correctness | Zero false *rewrites*: the server never mutates user files or tool inputs. | `[DECISION]` |
| Determinism | Same inputs → byte-identical outputs (stable sort keys; no time-dependent content except cache metadata). | `[REC]` |
| Performance | Hook p95 < 300 ms; `search_redis` cold on a 10k-file repo < 3 s; `optimize_redis` repo mode < 10 s on 500 Python files (Plan to confirm via benchmark). | `[DECISION]` (hook) / `[REC]` (others) |
| Typing | pyright/mypy **strict**, zero errors; no `Any`, no untyped `dict` standing in for shapes (Pydantic/TypedDict/dataclasses). | `[DECISION]` |
| Lint/format | ruff, zero warnings. | `[DECISION]` |
| Tests | pytest; golden-file tests per rule; ≥ 90 % line coverage on `engine/`. | `[DECISION]` |
| Compatibility | Python ≥ 3.11; `mcp>=2,<3`; Redis ≥ 7.2 semantics; macOS/Linux first-class; Windows hooks best-effort (PowerShell command variant provided). | `[DECISION]` / `[REC]` |
| Observability | JSON-lines logs to stderr; `EZ_REDIS_LOG_LEVEL` env var; never log file contents, prompts, or secrets. | `[DECISION]` |
| Packaging | PyPI `ez-redis`; `uvx ez-redis` runs the stdio server; `uv.lock` pinned; `pip-audit` in CI. | `[DECISION]` |
| License | MIT; attribution + links for paraphrased agent-skills and summarized Upstash content. | `[DECISION]` |
| Docs | README (install, host configs, tool reference), CONTRIBUTING, rule catalog doc auto-generated from rule metadata. | `[REC]` |

---

## 9. Constraints

- Blank repository: no conventions to inherit; those chosen here become the conventions. `[REPO]`
- MCP 2026-07-28: no sessions, no server-side prompt visibility, Sampling/Roots/Logging deprecated. `[EXT]`
- Hooks are host features with host-specific schemas; VS Code ignores matchers and is in Preview. `[EXT]`
- `rg` must be on `PATH`; absence is a loud, actionable error at startup and in hook logs. `[DECISION]`
- Server must never require network access. `[DECISION]`

---

## 10. Explicit User Decisions (record)

| # | Decision | Rejected alternatives | User rationale / acknowledged tradeoff |
|---|---|---|---|
| D1 | Two artifacts: server + hook pack (Claude Code & VS Code) | Server only; single host | Full auto-detection; accepts shim maintenance across two hosts. |
| D2 | Intercept **file edits** touching redis code | redis-cli shell commands; both; live proxy | Where bugs are introduced; deterministic. |
| D3 | Hooks **advise only** | Block denylist; auto-rewrite | "Assist, never hinder"; no silent behavior changes. |
| D4 | **Python/redis-py only** in v1 | +TS/JS; +Go/Java; regex-only multi-language | Ship narrow and correct; IR seam for later. |
| D5 | **No live Redis** in v1 | Optional read-only; required | No secrets/network; faster ship. |
| D6 | Server **never writes** to the repo | Explicit apply tool; full autonomous Change Manager | Host applies; git is the rollback. |
| D7 | Agent-mediated structured questions | Native MRTR; single-shot | Works on every host today. |
| D8 | Keep `rg`, drop `jq` | Both; neither; jq optional | jq adds nothing over stdlib. |
| D9 | Ranked list output for `search_redis` | `{path: score}`; `{score: [paths]}` | Fixes collision; explains scores. |
| D10 | Deterministic heuristic scoring | LLM-scored; hybrid | Reproducible/testable; `query` boosts included. |
| D11 | In-process cache, fingerprint + 10-min TTL | No cache; disk in repo | Useful across calls; no repo pollution. |
| D12 | PyPI + `uvx`, stdio, Python ≥ 3.11 | +HTTP; git clone only | Standard local-MCP distribution. |
| D13 | Bundled offline KB | Live fetch; hybrid | Deterministic; no injection from fetched pages. |
| D14 | Six rule families (§7.2) | + key naming; + data-structure fit | Highest-impact first. |
| D15 | severity × confidence; low-confidence excluded from hooks | Severity only; numeric | Hook noise near zero. |
| D16 | Hook budget: <300 ms p95, ≤~600 chars, dual gate | Fire on terms alone; no budget | Never stall prompts; no firing in non-Redis repos. |
| D17 | Shim imports engine in-process | MCP-to-subprocess; `mcp_tool` hooks | Meets budget; works on both hosts. |
| D18 | Repo boundary rules + secret-file skip + caps | Trust caller | Zero-trust on tool input. |
| D19 | Strict redis-cli parser; unknown → explicit finding | + redis-py one-liners; fuzzy | Fails loudly, never guesses. |
| D20 | Structured JSON + markdown | Markdown only | Agent-actionable. |
| D21 | Three-layer guard on `redis_conversion` | Description only | Consent-shaped parameter. |
| D22 | Architecture output: markdown plan + 3–5 validated diagrams | + starter code | Code-gen deferred. |
| D23 | Tiered question bank with `assume_defaults` | Ask everything | Bounded; escape hatch. |
| D24 | Full quality-gate set (§8) | — | Production grade. |
| D25 | stderr JSON-lines logging | OTel; none | Per MCP migration guidance. |
| D26 | MIT + attribution | Apache-2.0; proprietary | Compatible with sources. |
| D27 | Simplified pipeline; IR as seam | Stub modules | No code without callers. |
| D28 | Cache-aside v1 = ordering rule only | All three low-confidence; drop family | Only the ordering rule is statically decidable. |
| D29 | User-level disk cache for hook gate | Rescan every event | Meets budget; nothing in repo. |
| D30 | All six conversion candidates, EZC005/EZC006 at **low** confidence | Subset | User accepts higher false-positive risk on those two; they never reach hooks. |
| D31 | Redis ≥ 7.2 semantics with min-version annotations | 8.x only; configurable | Broad managed-offering coverage. |
| D32 | Hook pack targets **Claude Code and VS Code only** in v1; other hosts get the server without auto-detection | Add Cursor/Codex adapters in v1 | Documented hook schemas exist only for these two today. (Promoted from A1.) |
| D33 | Ship `ez-redis init --host {claude,vscode,both} [--dry-run]` | README copy/paste only | Explicit CLI action; supports "as easy as Git". (Promoted from A6.) |
| D34 | Windows hook support is **best-effort** (PowerShell variant; CI on macOS/Linux) | First-class Windows CI | Accepts manual tweaks on Windows for v1. (Promoted from A7.) |

## 11. User Preferences (non-binding)
- "Professional, not over-engineered." `[PREF]` — drives D27, D28.
- Should feel as natural as Git to developers. `[PREF]` — drives D12 and the `ez-redis init` recommendation.

---

## 12. Assumptions Ledger

| ID | Assumption | Reason | Impact if wrong | Needs confirmation? |
|---|---|---|---|---|
| A1 | Target users run Claude Code and/or VS Code Copilot agent mode. | These are the hosts with documented hooks. | Other hosts (Cursor, Codex) get the server but no auto-detection until their hook formats are added. | **Confirmed → D32** |
| A2 | Repos of interest are ≤ ~50k files; `rg` handles them within budget. | Typical service repos. | Caps trigger `truncated: true`; still correct, less complete. | No — surfaced via output |
| A3 | redis-py idioms cover `redis`, `redis.asyncio`, `StrictRedis`, `ConnectionPool`, `pipeline()`; third-party wrappers (django-redis, fastapi-cache) are *detected* by `search_redis` but *not deeply analyzed* by rules in v1. | Scope D4. | Some findings missed in wrapper-heavy code. | **Yes** |
| A4 | "Cache-like key" heuristic = key literal/prefix containing `cache`, `sess`, `tmp`, `token`, `rate`, or file path containing `cache`; otherwise EZR020 is `low` confidence. | Static analysis cannot know intent. | Some no-TTL SETs unflagged in hooks (still visible in explicit calls). | No — Plan refines |
| A5 | Hook JSON I/O schemas as documented today remain stable enough; shim tolerates unknown fields. | Both hosts label hooks Preview/evolving. | Shim update on host change; failure mode is silent no-op, never a stalled prompt. | No |
| A6 | `ez-redis init` writing hook config to the user's repo is acceptable because it is an explicit CLI action, not server behavior. | Adoption. | If rejected, users copy JSON from README. | **Confirmed → D33** |
| A7 | Windows support for hooks is best-effort via a PowerShell command variant; primary CI on macOS/Linux. | Hook exec differs on Windows. | Windows users may need manual tweaks. | **Confirmed → D34** |

---

## 13. Security Considerations (threat model)

**Assets:** the user's source code (may contain secrets), the agent's context window (prompt-injection surface), the user's filesystem.

**Entry points & trust boundaries**
1. `tools/call` arguments from the agent — **untrusted**. Validated by schema; `repo_root` existence + resolution; all paths confined under `repo_root`; caps enforced. `[DECISION]`
2. Hook stdin JSON from the host — **untrusted**. Parsed with a tolerant schema; unknown fields ignored; strings length-capped before use. `[DECISION]`
3. Repository file contents — **untrusted data, never instructions**. Only bounded, control-character-stripped excerpts flow into findings; secret-like files are never opened; `redis://` userinfo redacted. `[DECISION]`
4. Bundled KB — trusted at build time; content is static text with links.

**Top abuse cases & mitigations**
| Abuse | Mitigation |
|---|---|
| Path traversal via `repo_root`/`paths` (`../`, symlink escape) | `Path.resolve()` then `is_relative_to(repo_root)`; reject symlinks that escape; reject absolute `paths`. |
| Secret exfiltration through tool output | Denylist of secret-like file globs; URL userinfo redaction; excerpt caps; never log contents. |
| Prompt injection via repo content or hook input reaching the agent | Excerpts bounded and control-stripped; hook context phrased as facts (F9); no imperative text from files is ever echoed. |
| DoS via huge repo / giant file / pathological regex | File-count, per-file bytes, total bytes, and wall-clock caps; `rg --max-filesize`; term list is literal (no user-supplied regex). |
| Command injection via `rg` invocation | `subprocess.run([...], shell=False)` with fixed argv; user strings are passed as literal `-e` patterns/paths, never interpolated into a shell. |
| Hook script tampering by the agent | README recommends host protections (VS Code `chat.tools.edits.autoApprove` exclusion; Claude workspace trust). |
| Confused deputy: hook or tool suggests running `redis_conversion` unsolicited | D21 three-layer guard; hook context never names the tool. |

**Fail-closed vs fail-open:** nothing security-critical is gated by ez-redis; advice fails open (silent no-op). Path-boundary and secret-file checks fail **closed** (reject the path). `[DECISION]`

**Dependencies:** `mcp>=2,<3`, `pydantic` (transitively required by mcp), `ripgrep` binary. No other runtime deps planned; dev deps: ruff, pyright/mypy, pytest, pytest-cov, pip-audit. All pinned in `uv.lock`. `[REC]`

---

## 14. Performance Considerations
- The hook is the hot path: a fresh Python process per event. Budget < 300 ms p95 requires: lazy imports, no Pydantic model construction on the gate path, disk-cached gate, `rg` limited to the changed file in `PreToolUse`. `[DECISION]` `[INF]`
- `search_redis` cost is dominated by `rg`; scoring is linear in matches. In-process cache amortizes repeated calls within a server lifetime. `[INF]`
- `optimize_redis` repo mode parses only files selected by `search_redis` (score ≥ threshold), not the whole repo. `[REC]`
- All budgets are asserted by a CI benchmark on a synthetic 10k-file fixture. `[DECISION]`

## 15. Reliability Considerations
- Any single-file failure (syntax error, encoding, permission) is a **finding**, not a crash; analysis continues. `[REC]`
- `rg` missing → clear startup error for the server; hooks log and no-op. `[DECISION]`
- Cache corruption (disk gate cache) → treated as miss and rewritten. `[REC]`
- Question flow bounded to ≤ 3 rounds. `[DECISION]`
- Mermaid output is syntax-validated by a bundled minimal validator before return; invalid → diagram omitted with an explicit note, never a broken block. `[DECISION]` `[REC]`

## 16. Operational Considerations
- Install: `uvx ez-redis` (server) / `uv tool install ez-redis` (CLI + hooks). Host config snippets in README. `[DECISION]`
- Upgrades: KB and rule catalog versioned with the package; `ez-redis --version` prints package, KB, and command-table versions. `[REC]`
- Diagnostics: `ez-redis doctor` checks `rg`, Python version, hook file presence, cache dir writability. `[REC]`
- Logs: stderr JSON lines; `EZ_REDIS_LOG_LEVEL`. `[DECISION]`

## 17. Dependencies & Integrations
| Dependency | Kind | Why | Risk / mitigation |
|---|---|---|---|
| `mcp>=2,<3` | Python pkg | Protocol + `MCPServer` | Young v2 API; pin minor; smoke test with Inspector. |
| `pydantic` | Python pkg (transitive) | Schemas | Standard. |
| `ripgrep` (`rg`) | Binary | Fast, `.gitignore`-aware discovery | Must be installed; loud error if absent. |
| Claude Code hooks | Host feature | `UserPromptSubmit`, `PreToolUse` | Schema evolution; tolerant parser. |
| VS Code agent hooks (Preview) | Host feature | Same | Matchers ignored; self-filter; Preview churn. |
| redis/agent-skills (MIT) | Content source | Rule/KB paraphrase with attribution | License-compatible. |
| redis.io/commands | Content source | Command table (names, arity hints, since-version) | Generated at build time into a static table; refreshed per release. |
| Upstash blog | Content source | Pattern catalog summaries | Summarize, link; do not copy. |

## 18. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Host hook schemas change (both hosts label hooks Preview) | Medium | Hooks silently stop firing | Tolerant parsing; `ez-redis doctor`; CI fixture tests against recorded host payloads. |
| False positives erode trust ("never hinder") | Medium | Users disable hooks | Confidence gating; golden negatives per rule; low-confidence never in hooks; easy `EZ_REDIS_DISABLE_HOOKS=1`. |
| 300 ms budget missed on large repos | Medium | Prompt latency | Disk gate cache; `PreToolUse` analyzes only the edited content; benchmark in CI. |
| `mcp` v2 API churn | Low–Medium | Build breaks | Pin `<3`; Inspector smoke in CI. |
| Scope creep toward live Redis / apply | Medium | Complexity, secrets | Deferred list (§5) with explicit triggers. |
| Heuristic conversion detectors (EZC005/006) noisy | High | Noisy explicit calls | Low confidence; user accepted (D30). |

## 19. Tradeoffs (named axes)
- **Simplicity ↔ flexibility:** chose simplicity (D27); flexibility preserved only at the IR seam.
- **Correctness ↔ coverage:** chose correctness (D4, D28) — fewer languages/rules, each fully tested.
- **Latency ↔ richness (hooks):** chose latency (D16) — hooks give a pointer, tools give depth.
- **Determinism ↔ semantic depth (scoring):** chose determinism (D10).
- **Buy ↔ build:** buy `rg` and `mcp`; build the small AST analyzer (core differentiator).

## 20. Rejected Alternatives (consolidated)
Live Redis proxy; auto-rewrite via `updatedInput`; server-side apply/rollback; multi-language v1; live docs fetch; `jq`; LLM scoring; `{score: file}` dict; native MRTR now; stub Evidence-Fusion/Change-Manager modules; OTel in v1; Streamable HTTP in v1. See §10 for rationale.

## 21. External Evidence (sources consulted)
- MCP specification 2026-07-28: Tools, Elicitation, Sampling, Changelog, Interceptors WG charter — modelcontextprotocol.io.
- MCP Python SDK v2 README — github.com/modelcontextprotocol/python-sdk.
- Claude Code hooks reference — code.claude.com/docs/en/hooks.
- VS Code *Agent hooks (Preview)* — code.visualstudio.com/docs/copilot/customization/hooks.
- redis/agent-skills: `AGENTS.md`, `redis-core`, `redis-connections`, `redis-observability` SKILL.md — github.com/redis/agent-skills.
- Upstash, *Redis Caching Patterns: A Practical 2026 Guide*.
- redis.io command reference (to be used at build time for the command table).
- Prior art (architecture doctrine): system-design-primer caching section — confirmed cache-aside as default, consistent with F7.

## 22. Unresolved Non-Blocking Unknowns (delegated to Plan)
- Exact scoring weights and thresholds for `search_redis` (illustrative values in §6.1).
- Exact wording/order of the architecture question bank.
- Module/file layout and class names (suggestion in §23).
- Golden-fixture corpus composition.
- Whether to vendor a tiny Mermaid grammar check or shell out to `mmdc` when available (must not become a hard dependency).

---

## 23. Implementation Suggestions (non-binding for Plan)

### 23.1 Proposed package layout
```
ez-redis/
  pyproject.toml            # uv-managed; console scripts: ez-redis (server/CLI)
  uv.lock
  src/ez_redis/
    __init__.py
    server.py               # MCPServer wiring; tool registration; schemas
    cli.py                  # ez-redis init|doctor|--version
    hook.py                 # python -m ez_redis.hook (host-normalizing shim)
    hosts/                  # claude.py, vscode.py (event/field normalization)
    engine/
      discover.py           # rg wrapper (argv-only), term list, caps
      parse_py.py           # ast → IR
      ir.py                 # RedisCall, ClientConstruction, DatastoreWrite
      rules/                # one module per rule id; registry with metadata
      policy.py             # severity/confidence/hook eligibility/filters
      render.py             # diff/markdown/doc refs
      cache.py              # in-process LRU; gate disk cache
    knowledge/
      kb.py                 # bundled KB loader
      data/                 # commands.json, patterns.md, rules_docs.md (attributed)
    architecture/
      questions.py          # tiered bank
      planner.py            # plan + diagrams + checklist
      mermaid.py            # minimal validator
    conversion/
      detectors.py          # EZC001–006
  hooks/
    claude/settings.hooks.json
    vscode/ez-redis.hooks.json
  tests/                    # golden/, fixtures/, bench/
  docs/specs/               # this spec + diagrams
  .github/workflows/ci.yml
```

### 23.2 Phased delivery (each phase independently verifiable)
1. **Foundation:** repo scaffolding, tooling, CI, empty `MCPServer` with `search_redis` schema; Inspector smoke passes.
2. **Discover + search:** `rg` wrapper, term list, scoring, cache; golden tests on fixture repos.
3. **IR + rules EZR001–004, 010:** parser, IR, first rules; golden positives/negatives.
4. **Rules EZR020–031, 040, 050:** remaining rules; command-table parser for `command` mode.
5. **Hook pack:** shim, host normalization, gate cache, benchmark; manual verification in both hosts.
6. **Architecture tool:** question bank, planner, Mermaid validator, KB integration.
7. **Conversion tool:** detectors, delegation, guard tests (including negative: missing consent flag).
8. **Hardening & release:** docs, `doctor`, `init`, pip-audit, version stamping, PyPI publish.

---

## 24. Acceptance Criteria (testable)

**Server / protocol**
- AC1. `uvx ez-redis` starts a stdio MCP server; MCP Inspector lists exactly four tools, each with `inputSchema` and `outputSchema`; every tool's `structuredContent` validates against its `outputSchema` in CI.
- AC2. Calling any tool with an unknown field, a non-existent `repo_root`, or a path escaping `repo_root` returns a tool-execution error naming the offending field; no partial work is performed.

**search_redis**
- AC3. On the fixture repo, returns a ranked list sorted by `score` desc then `path` asc; no two entries share a `path`; every `score ∈ [1,10]`; `results.length ≤ max_results`.
- AC4. A fixture file containing `redis://user:pass@host` appears with `pass` redacted in every excerpt; fixture `.env` containing `REDIS_URL` never appears in results or logs.
- AC5. Second identical call returns `cached: true`; modifying a matched file's mtime or passing `refresh: true` returns `cached: false`.

**optimize_redis**
- AC6. Each rule EZR001–EZR050 has ≥1 positive and ≥1 negative golden test; the suite passes; engine coverage ≥ 90 %.
- AC7. `command: "KEYS user:*"` returns exactly one `EZR001` finding with `after` using `SCAN`, a non-empty `unified_diff`, and ≥1 `doc_ref`; `command: "FOOBAR x"` returns exactly one `unknown_command` finding and no suggestions.
- AC8. `snippet` mode on a file with a syntax error returns an `unparseable_file` finding and `isError: false`.
- AC9. Findings with `confidence: low` have `hook_eligible: false`; those with `medium|high` have `hook_eligible: true`.

**redis_architecture**
- AC10. First call with only `goal` returns `status: "needs_input"` with ≥ 8 questions, each with `recommended` and `why_it_matters`; ≤ 3 rounds always reach `complete`.
- AC11. `assume_defaults: true` yields `complete` on the first call, and every default appears in `assumptions` with `source: "default"`.
- AC12. `complete` output includes 3–5 diagrams, each passing the bundled Mermaid validator, and a `checklist` containing null-sentinel, stampede protection, TTL jitter, cache-down fallback, and a `KEYS` prohibition.

**redis_conversion**
- AC13. Calling without `user_requested_optimization: true` or without `request_excerpt` returns a validation error; with both, on the fixture app it returns ≥1 candidate for each of EZC001–EZC004 and marks EZC005/EZC006 as `confidence: low`.
- AC14. The string `redis_conversion` never appears in any hook `additionalContext` output in the hook test corpus.

**Hooks**
- AC15. Benchmark: 200 invocations of the `UserPromptSubmit` shim on the 10k-file fixture with a Redis-using manifest and a Redis-mentioning prompt → p95 < 300 ms; output ≤ 600 chars.
- AC16. In a fixture repo **without** a Redis dependency, both hooks exit 0 with empty stdout for a Redis-mentioning prompt/edit.
- AC17. `PreToolUse` shim never emits `permissionDecision` or `updatedInput` keys (asserted over the corpus); it emits `additionalContext` only when ≥1 `hook_eligible` finding exists in the edited content.
- AC18. Shim correctly handles recorded payloads from both Claude Code (`Write`/`Edit`, `file_path`) and VS Code (`create_file`/`replace_string_in_file`, `filePath`) fixtures.

**Quality gates**
- AC19. CI is green on: ruff (lint + format check), pyright strict (or mypy strict), pytest with coverage threshold, pip-audit, Inspector smoke, hook benchmark.
- AC20. No secrets, `.env`, or credential files exist in the repo; `git log -p` contains none.

---

## 25. Approval

**APPROVED v1 — 2026-09-01.** User selected "Approve v1 as written" in the recorded approval prompt and confirmed A1, A6, A7 (now D32–D34). This document is the authoritative input for the Plan agent. Any implementation-critical contradiction or missing requirement discovered during planning returns to the Brainstorm stage; on revision, only affected subsections change and the version increments to v2.
