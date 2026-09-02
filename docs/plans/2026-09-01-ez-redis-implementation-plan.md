# ez-redis — Implementation Plan (45 Phases, 10 Parallel Tracks)

| Field | Value |
|---|---|
| **Plan version** | v1 |
| **Status** | READY FOR EXECUTION — **no code has been written**; this document and the `.mmd` are the only artifacts |
| **Date** | 2026-09-01 |
| **Authoritative requirements** | `docs/specs/2026-09-01-ez-redis-mcp-server.md` (APPROVED v1 — decisions D1–D34, acceptance criteria AC1–AC20) |
| **Architecture source of truth** | `docs/plans/ez-redis-architecture.mmd` — every phase names the node ids it delivers; **any structural change edits the `.mmd` first** |
| **Doctrine loaded** | `planning.md`, `implementation.md`, `security.md`, `verification.md`, `python.instructions.md` |
| **Skills to load at implementation** | `python-fact-grounded-coding`, `api-design-principles`, `backend-development` |

---

## Part I — How to Read and Use This Plan

### I.1 Purpose

The approved spec is decomposed into **45 phases across 10 tracks** so several engineers can work concurrently without blocking or colliding. A phase is a *unit of ownership*: one engineer, one PR (or a short PR series), one unambiguous Definition of Done, and an explicit list of files it may touch.

Phases state **what must exist when finished, which spec requirements that satisfies, what it depends on, which architecture nodes it delivers, how it is proven done, and what it owns.** Phases deliberately do **not** dictate function signatures or line-level design; those are the implementer's decisions, bounded by the spec, the doctrine, and the Global Definition of Done below.

### I.2 Plan-level latitude exercised (C10 justification trail)

The spec left these choices to the Plan. Each is recorded here so the reasoning can be audited. None touches an approved `[DECISION]`.

| # | Choice | Spec allowed | Plan picks | Justification |
|---|---|---|---|---|
| L1 | Strict type checker | pyright **or** mypy (§8) | **pyright strict** | The team's editor runs Pylance; using pyright in CI gives byte-identical diagnostics in-editor and in CI, eliminating "passes locally, fails in CI" drift. |
| L2 | Hook host detection | "field casing / tool names" (§7.3) | **Payload field shapes** (`file_path`/`content`/`new_string` ⇒ Claude Code; `filePath`/`newString`/`code` ⇒ VS Code). Tool names are never consulted. | Tool names differ per host and change between releases (VS Code hooks FAQ; memory `vscode-agent-hooks.md`: "Never filter hooks on `tool_name`"). Field shapes are the stable signal. |
| L3 | Mermaid validation (§22) | vendor a tiny grammar check **or** shell out to `mmdc` if present | **Bundled minimal validator only**; `mmdc` is never invoked | Spec §22 forbids a hard dependency; an optional path is rarely exercised code. Deterministic and Node-free. |
| L4 | Package layout (§23.1) | non-binding suggestion | §23.1 **plus** `src/ez_redis/safety.py` and a `src/ez_redis/tools/` package holding one module per tool handler; `server.py` only registers them | `safety.py`: one auditable home for every security-critical boundary check (§13). `tools/`: four phases (12, 29, 41, 43) would otherwise each own a *section* of `server.py` — a guaranteed merge conflict in a parallel plan. |
| L5 | Command-table provenance (§17: "generated at build time") | unspecified mechanism | A **dev-time script** with network access produces a committed, versioned JSON artifact that is diffed in PRs. The release build and runtime never fetch. | Keeps D13 (offline KB) and §9 (no runtime network) intact while allowing the table to be refreshed per release. |
| L6 | `optimize_redis` repo-mode file selection threshold (§14 REC) | unspecified | Files with `search_redis` score ≥ **4** are parsed; the constant lives in one place and is surfaced in output metadata | Score 4 is the "imports a redis client" weight in §6.1's illustrative table — files below it contain only vocabulary hits. Phase 10 may re-tune and must update this constant in the same PR. |

### I.3 Global Definition of Done (applies to **every** phase)

1. `ruff check` and `ruff format --check` are clean; `pyright --strict` reports **zero** errors **project-wide**, not just in changed files.
2. Every new behavior has pytest coverage: happy path, edge case, and each named failure mode. The **full** suite passes locally and in CI.
3. No `Any`; no bare `dict`/`object` standing in for a known shape; no `# type: ignore` / `# pyright: ignore` without an error code and a comment explaining why no typed alternative exists.
4. No file contents, prompts, or secrets are logged, echoed, or committed. No network access is introduced at runtime.
5. Every `mcp`, `pydantic`, or stdlib API that is non-trivial or version-sensitive is verified against its documentation and the link is cited in a comment or the PR.
6. The PR description carries a **justification trail**: spec section, decision id, doc link, or measurement for every non-obvious choice.
7. Nothing outside the phase's declared **Ownership** is modified without an explicit note in the PR.
8. Any bug, host quirk, or hard-won convention discovered is recorded in `/memories/repo/` (repo facts) or `/memories/` (cross-project lessons) **before** merge.

### I.4 Vocabulary

- **Finding** — one detected issue with `rule_id`, severity, confidence, location, before/after, diff, rationale, doc refs (spec §6.2).
- **Fact** — an IR record (`RedisCall`, `ClientConstruction`, `DatastoreWrite`) produced by the parser (spec §6.2 behavior 2).
- **Golden test** — a committed input (`.py` snippet or fixture repo) paired with a committed expected output (`expected.json` or `.md`); the harness diffs actual vs. expected byte-for-byte.
- **Hook-eligible** — a finding with confidence ≥ medium; only these may appear in hook `additionalContext` (D15).
- **Gate (a)/(b)** — hook preconditions: (a) repo depends on Redis, (b) prompt/edit is Redis-related (D16).

---

## Part II — Tracks, Milestones, Critical Path

### II.1 Tracks

| Track | Name | Phases | Suggested owner profile | Can start after |
|---|---|---|---|---|
| **A** | Foundation & contracts | 1–7 | Senior; sets conventions all others inherit | day 0 |
| **B** | Discovery & `search_redis` | 8–12 | Backend / tooling | Phase 5 |
| **C** | Parser & IR | 13–16 | Static analysis / AST | Phase 5 |
| **D** | Rule catalog | 17–24 | Any engineer per rule after 17 | Phase 13 |
| **E** | Command mode, policy, render, `optimize_redis` | 25–29 | Backend | Phase 3 (25) / Phase 17 (27) |
| **F** | Knowledge base | 30–31 | Technical writer + engineer | Phase 1 |
| **G** | Hook pack | 32–37 | Tooling / DX | Phase 9 |
| **H** | `redis_architecture` | 38–41 | Backend + Redis SME | Phases 6, 31 |
| **I** | `redis_conversion` | 42–43 | Static analysis | Phases 16, 17 |
| **J** | CLI, docs, release | 44–45 | DX / release | Phase 36 |

### II.2 Milestones (integration gates)

| Milestone | Reached when | ACs proven | Unblocks |
|---|---|---|---|
| **M1 — Contracts frozen** | Phases 1–7 merged; Inspector lists four stub tools with `inputSchema` + `outputSchema` | AC1 (partial), AC2 | Every other track proceeds against stable types/schemas |
| **M2 — Search works** | Phase 12 merged | AC3, AC4, AC5 | 29 (repo mode), 34 (prompt hook), 41 (repo pre-fill) |
| **M3 — Optimize works** | Phase 29 merged | AC6, AC7, AC8, AC9 | 35 (edit hook), 42–43 (conversion) |
| **M4 — Hooks shipped** | Phase 37 merged | AC15, AC16, AC17, AC18 | 44 (`init` templates final) |
| **M5 — Architecture & conversion** | Phases 41 and 43 merged | AC10–AC14 | Release |
| **M6 — Release** | Phase 45 merged; PyPI publish succeeds | AC19, AC20 (all 20 green) | — |

### II.3 Critical path

`1 → 3 → 5 → 6 → 7 → 13 → 15 → 17 → 18 → 27 → 28 → 29 → 35 → 37 → 45`

Everything not on this path may proceed in parallel as soon as its listed dependencies merge. The widest fan-out is Phases 18–24 (seven rules) immediately after Phase 17: seven engineers can work simultaneously with zero file overlap.

### II.4 Dependency graph

```
A:  1 → 2
    1 → 3 → 4 → 5 → 6 → 7
B:  4,5 → 8 → 9 → 10 → 11 → 12            (12 also needs 7)
C:  5 → 13 → 14 → 15 → 16
D:  13,5 → 17 → {18,19,20,21,22,23,24}       (all need 15; 21,22,24 also need 16)
E:  3 → 25 → 26 ;  17 → 27 → 28 → 29        (26 needs 17; 28 needs 31; 29 needs 12,26,18–24)
F:  1 → 30 → 31
G:  9 → 32 → 33 → 34 → 35 → 36 → 37        (34 needs 12; 35 needs 29; 37 needs 2)
H:  6,31 → 38 → 39 → 40 → 41                (41 needs 7,12,16)
I:  16,17 → 42 → 43                          (43 needs 41)
J:  36,31,25 → 44 ;  all → 45
```

### II.5 Suggested staffing waves

| Wave | Concurrent phases | Headcount |
|---|---|---|
| 0 | 1 | 1 |
| 1 | 2, 3, 30 | 3 |
| 2 | 4, 25, 31 | 3 |
| 3 | 5 → 6 → 7 (serial, one owner) ; 13 in parallel once 5 lands | 2 |
| 4 | 8, 14, 17 | 3 |
| 5 | 9, 15, 18, 27 | 4 |
| 6 | 10, 16, 19, 20, 21, 22, 23, 24, 26, 28, 32, 33, 38 | up to 13 |
| 7 | 11, 39, 42 | 3 |
| 8 | 12, 40 | 2 |
| 9 | 29, 34 | 2 |
| 10 | 35, 41 | 2 |
| 11 | 36, 43 | 2 |
| 12 | 37, 44 | 2 |
| 13 | 45 | 1 |

---

## Part III — The 45 Phases

Each phase carries: **Delivers · Spec · Depends on · Architecture nodes · Done when · Ownership**.

---

### Track A — Foundation & Contracts

#### Phase 1 — Repository scaffold, tooling baseline, logging & configuration

**Delivers**
- `pyproject.toml`: PEP 621 metadata, `src/` layout, `requires-python >= 3.11`, runtime dependency `mcp>=2,<3` only, console script `ez-redis` → CLI entry, `[tool.ruff]` (lint + format, line length fixed), `[tool.pyright]` strict, `[tool.pytest.ini_options]`, `[tool.coverage]` with `engine/` threshold placeholder.
- `uv.lock` committed; `.python-version`.
- `.pre-commit-config.yaml` running ruff (lint + format), pyright, and a "no secrets" pattern check.
- `.gitignore` (Python, uv, `.env*`, editor files), `.editorconfig`, `LICENSE` (MIT).
- `src/ez_redis/__init__.py` exposing `__version__`.
- `src/ez_redis/logging.py`: a JSON-lines logger writing to **stderr only**, level from `EZ_REDIS_LOG_LEVEL` (default `WARNING`), fixed field set (`ts`, `level`, `event`, `component`, plus explicitly allowed context keys). A filter drops any field whose key is tagged as content (`content`, `excerpt`, `prompt`, `snippet`) so accidental logging of file text is impossible.
- `src/ez_redis/config.py`: typed reader for `EZ_REDIS_DISABLE_HOOKS`, `EZ_REDIS_LOG_LEVEL`, `XDG_CACHE_HOME` fallback rules.

**Spec** §3.1, §3.8, §8 (typing, lint, observability, packaging, license), §9, D12, D24, D25, D26.
**Depends on** nothing.
**Architecture nodes** `PKG`, `LOG`.
**Done when** `uv sync` succeeds on a clean checkout; `ruff check`, `ruff format --check`, `pyright --strict`, and `pre-commit run --all-files` pass on the empty package; unit tests prove the logger emits one valid JSON object per line, respects the level, and drops content-tagged fields.
**Ownership** repository-root config files, `src/ez_redis/__init__.py`, `src/ez_redis/logging.py`, `src/ez_redis/config.py`, `tests/unit/test_logging.py`, `tests/unit/test_config.py`.

---

#### Phase 2 — Continuous-integration pipeline skeleton

**Delivers**
- `.github/workflows/ci.yml` on push and pull request, matrix `{macos-latest, ubuntu-latest}` × Python 3.11 and 3.12, with uv caching. Jobs: `lint` (ruff check + format check), `types` (pyright strict), `test` (pytest with coverage XML; `engine/` threshold wired to 90 % once the package exists), `audit` (`pip-audit` against `uv.lock`), `build` (`uv build`, artifact upload).
- A `docs-current` job placeholder (used by Phase 45).
- Branch protection notes in `CONTRIBUTING.md` stub (Phase 45 finalizes).

**Spec** §8 quality gates, D24, D34 (CI on macOS/Linux only), AC19.
**Depends on** 1.
**Architecture nodes** `CI`.
**Done when** CI is green on the scaffold; a scratch branch with an intentional lint error and an intentional failing test turns the respective jobs red.
**Ownership** `.github/workflows/`.

---

#### Phase 3 — Test infrastructure and fixture-corpus design

**Delivers**
- `tests/` layout: `unit/`, `golden/`, `fixtures/`, `bench/`, `hooks/`, `_harness/`.
- `tests/_harness/repo_builder.py`: builds a synthetic repository into `tmp_path` from a declarative description (file path → content, optional mtime), including manifest files, so fixtures are reproducible and reviewable.
- `tests/_harness/golden.py`: golden-file comparison with a `--update-golden` pytest option; failure output shows a unified diff of expected vs. actual JSON/markdown.
- `tests/_harness/json_assert.py`: asserts a string is exactly one valid single-line JSON object (motivated by memory `hook-json-newline.md`).
- `tests/fixtures/CORPUS.md`: the fixture plan every later phase draws from — **redis-app** (redis-py sync + asyncio, pipelines, loops, TTL variants, destructive commands, cache-aside ordering cases), **non-redis-app**, **wrapper-heavy-app** (django-redis, fastapi-cache), **secrets-app** (`.env` with `REDIS_URL`, a `.pem`, a source file containing `redis://user:pass@host`), **broken-app** (syntax-error file, non-UTF-8 file), **framework-app** (Flask/FastAPI/Django handlers with ORM reads, lru_cache, counters, polling loop, ORDER BY LIMIT, session config) for Track I, and the **10k-synthetic** generator spec for Phase 37.
- Initial materialization of `redis-app`, `non-redis-app`, and `secrets-app`.

**Spec** §8 tests, §22 (fixture corpus delegated to Plan), AC3–AC6, AC13, AC16, AC18.
**Depends on** 1.
**Architecture nodes** `TESTS`.
**Done when** a sample golden test round-trips through the harness; the builder produces `secrets-app` with a `.env` and a credentialed URL; `CORPUS.md` lists every fixture with the phases that consume it.
**Ownership** `tests/conftest.py`, `tests/_harness/`, `tests/fixtures/`.

---

#### Phase 4 — Safety primitives: path boundary, secret denylist, redaction, caps

**Delivers** `src/ez_redis/safety.py`, pure functions only:
- `confine(path, repo_root)`: `Path.resolve()` both sides, then `is_relative_to`; rejects `..` escapes, symlinks resolving outside the root, and absolute entries in `paths[]`. Returns a typed result (`Confined | Rejected(reason)`), never raises for expected rejections.
- `is_secret_like(path)`: the denylist `.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `*secret*`, `*credential*` (case-insensitive on the basename).
- `redact_redis_urls(text)`: replaces userinfo in `redis://` and `rediss://` URLs with `user:***@`; handles user-only, user+pass, and percent-encoded forms.
- `sanitize_excerpt(text, max_len)`: strips control characters (U+0000–U+001F except `\t`), collapses `\r\n`, truncates with a marker.
- `Caps` (frozen dataclass of `Final` constants): `MAX_FILES`, `MAX_BYTES_PER_FILE`, `MAX_TOTAL_BYTES`, `MAX_WALL_MS`, `MAX_EXCERPT_CHARS = 200`; and `CapsHit` (which caps were hit) for output metadata.
- Module docstring: *"No code in this package may open, read, or list a user path except through this module."*

**Spec** §6 common rules, §13 (all mitigations rows), D18.
**Depends on** 3.
**Architecture nodes** `SAFE`.
**Done when** parametrized tests cover `..` traversal, symlink escape (created in `tmp_path`), absolute `paths`, every denylist glob (positive and near-miss negative), URL redaction variants, control-character stripping, truncation marker, and each cap. Every rejection **fails closed**.
**Ownership** `src/ez_redis/safety.py`, `tests/unit/test_safety.py`.

---

#### Phase 5 — Shared domain types

**Delivers** `src/ez_redis/types.py` — frozen dataclasses and `StrEnum`s that every track imports:
- `Severity` (`info | warning | critical`), `Confidence` (`low | medium | high`) with a total order for filtering.
- `Location(path: str | None, line: int | None, col: int | None)`.
- `DocRef(title, url)`.
- `RuleMeta(rule_id, title, family, default_severity, default_confidence, source, min_redis_version: str | None)`.
- `Finding(rule_id, title, severity, confidence, hook_eligible, location, before, after, unified_diff, rationale, doc_refs, min_redis_version)` with a `to_json()` that emits exactly the §6.2 finding object.
- `CapsHit` re-exported from `safety.py` for output metadata.

**Spec** §6.2 output shape, §7.2 rule metadata, §8 typing, D15, D20.
**Depends on** 4.
**Architecture nodes** `TYPES`.
**Done when** exhaustive `assert_never` tests over both enums; `Finding.to_json()` golden matches §6.2 field-for-field; ordering tests for `Confidence`/`Severity`.
**Ownership** `src/ez_redis/types.py`, `tests/unit/test_types.py`.

> **Contract freeze:** after M1, any change to this module requires a `contracts:` PR (see Part V).

---

#### Phase 6 — Tool I/O schemas

**Delivers** `src/ez_redis/schemas.py` — Pydantic v2 models (`model_config = ConfigDict(extra="forbid")`) for all four tools exactly as §6.1–6.4:
- `SearchRedisInput` (`repo_root`, `query ≤ 500`, `max_results 1–200 default 50`, `refresh`), `SearchRedisOutput`.
- `OptimizeRedisInput` with a `model_validator` enforcing **exactly one** of `command | snippet | repo_root` (`paths` only with `repo_root`), length caps (`command ≤ 2000`, `snippet ≤ 50 KB`), `min_confidence`, `min_severity`; `OptimizeRedisOutput`.
- `RedisArchitectureInput` (`goal ≤ 2000` required, optional `repo_root`, `answers`, `assume_defaults`), `RedisArchitectureOutput` including `Question`, `Assumption`, `Risk`, `Diagram`.
- `RedisConversionInput` with a validator requiring `user_requested_optimization is True` (literal) **and** non-empty `request_excerpt`; the error message explains that the tool only runs on explicit user request; `RedisConversionOutput`.
- `tests/golden/schemas/*.json`: committed JSON-Schema exports for every input and output model; a test regenerates and diffs them so **schema drift fails CI**.

**Spec** §6 (all four contracts), D9, D19, D20, D21 (layer 3), D23, AC2, AC13 (validation half).
**Depends on** 5.
**Architecture nodes** `SCHEMAS`.
**Done when** round-trip tests for each model; negative tests: unknown field, `max_results = 0` and `201`, two modes at once, zero modes, `paths` without `repo_root`, consent flag `false`/missing, empty `request_excerpt`; schema snapshot test passes.
**Ownership** `src/ez_redis/schemas.py`, `tests/unit/test_schemas.py`, `tests/golden/schemas/`.

> **Contract freeze** applies (Part V).

---

#### Phase 7 — MCP server skeleton with four tool stubs

**Delivers**
- `src/ez_redis/server.py`: constructs `mcp` v2 `MCPServer` over **stdio**; registers the four tools from `src/ez_redis/tools/{search,optimize,architecture,conversion}.py` (each module exposes a typed handler; bodies return a typed "not implemented in this phase" tool error until their track lands); tool descriptions include, for `redis_conversion`, the explicit sentence that it must never be called unless the user asked to optimize the repo/application (D21 layer 1); `inputSchema`/`outputSchema` derived from Phase 6 models.
- `src/ez_redis/tools/_dual.py`: helper producing `structuredContent` + a `text` block containing markdown, and the uniform mapping of validation/domain errors to `isError: true` with actionable messages (never a bare exception string).
- Startup check that `rg` is resolvable on `PATH`; failure prints an actionable message (install hints per OS) and exits non-zero.
- CI job `inspector-smoke`: launches the server via the MCP Inspector CLI, asserts exactly four tools, each with both schemas, and that `tools/call` with an unknown field returns a tool-execution error naming the field.
- Every `mcp` API used is checked against the v2 documentation and cited.

**Spec** §3.1, §6 common rules, §9 (`rg` required), §16, D12, D21 layer 1, AC1, AC2.
**Depends on** 6.
**Architecture nodes** `SERVER`, `DUAL`, and the four `T_*` placeholders.
**Done when** `uv run ez-redis` starts a stdio server; Inspector smoke passes in CI; unknown-field, non-existent `repo_root`, and traversal `paths` each yield a tool-execution error naming the field with no partial work; removing `rg` from `PATH` in a test yields the documented startup error. **→ Milestone M1.**
**Ownership** `src/ez_redis/server.py`, `src/ez_redis/tools/__init__.py`, `src/ez_redis/tools/_dual.py`, stub bodies in the four tool modules, CI `inspector-smoke` job.

---

### Track B — Discovery & `search_redis`

#### Phase 8 — ripgrep discovery wrapper

**Delivers** `src/ez_redis/engine/discover.py`:
- Invokes `rg` via `subprocess.run([...], shell=False, check=False, timeout=…)` with a **fixed argv**: `--json`, `--max-filesize`, `--max-count`, `-i`, `--no-messages`, one `-e <literal>` per term (`-F` fixed-strings), and the confined `repo_root`. User-provided strings are never interpolated into a shell and never used as regex.
- Streams `rg`'s JSON event lines (`begin`, `match`, `end`, `summary`) into typed records (`MatchRecord(path, line, submatch_text)`), applying `is_secret_like` **before** retaining any content and `confine()` on every path.
- Enforces `MAX_FILES`, `MAX_TOTAL_BYTES`, and wall-clock; returns `DiscoveryResult(matches, caps_hit, scanned_files)`.
- Raises `RgNotFound` when the binary is absent and `RgFailed(code, stderr_excerpt)` on non-zero exits other than "no matches".

**Spec** §6.1 behavior 1, §13 (DoS, command injection), D8, D18.
**Depends on** 4, 5.
**Architecture nodes** `DISC`, `RG`.
**Done when** tests with a fake `rg` script on `PATH` verify the exact argv (no shell), event parsing including multi-line and binary-skipped files, cap enforcement with `caps_hit` populated, denylist exclusion of `secrets-app/.env`, and timeout behavior; one integration test uses the real `rg` on `redis-app`.
**Ownership** `src/ez_redis/engine/__init__.py`, `src/ez_redis/engine/discover.py`, `tests/unit/test_discover.py`.

---

#### Phase 9 — Redis term catalog and manifest dependency detector

**Delivers**
- `src/ez_redis/engine/terms.py`: the §6.1 term list as `Final` frozensets grouped by weight class — *client imports* (`redis`, `StrictRedis`, `ConnectionPool`, `redis.asyncio`, `aioredis`, `django_redis`, `django-redis`, `fastapi_cache`, `rq`), *API vocabulary* (command method names), *URLs* (`redis://`, `rediss://`), *cache vocabulary* (`cache`, `caching`, `cached`, `ttl`, `expire`, `memoize`, `lru_cache`), plus `celery` co-occurring with `redis://`. Also exports `prompt_mentions_redis(text)` for hook gate (b).
- `src/ez_redis/engine/manifests.py`: reads **only** `requirements*.txt`, `pyproject.toml` (via `tomllib`), `poetry.lock`, `uv.lock`, `Pipfile`, `Pipfile.lock`, `setup.py` (regex on `install_requires`), `setup.cfg`, `environment.yml`, `docker-compose*.y*ml` (service image starting with `redis`); **never** `.env*`. Returns `DependencyFacts(uses_redis, client_name, client_version, manifest_mtimes)`.

**Spec** §6.1 term list, §7.3 gate (a) and manifest list, D16.
**Depends on** 8.
**Architecture nodes** `TERMS`, `MANIF`.
**Done when** parametrized positive/negative tests per manifest type; docker-compose image detection; a test proves `.env` is never opened (monkeypatched `open` records paths); `prompt_mentions_redis` tests for word-boundary behavior (`"reddish"` is not Redis).
**Ownership** `src/ez_redis/engine/terms.py`, `src/ez_redis/engine/manifests.py`, their tests.

---

#### Phase 10 — `search_redis` scoring heuristic

**Delivers** `src/ez_redis/engine/scoring.py`:
- Deterministic scoring from `DiscoveryResult` + `DependencyFacts` + optional `query`. Starting weights (§6.1 illustrative): client import +4, redis API call +3, `redis://` URL +2, cache/TTL vocabulary +1, query-term overlap in path or content +2, test/fixture/mock path −2, lockfile/manifest −3; clamp to `[1, 10]`. The owner tunes against the corpus and **records the final table and rationale in the module docstring**; if the client-import weight changes, the Phase 29 selection threshold constant (L6) is updated in the same PR.
- `reasons[]` strings are drawn from a fixed vocabulary (e.g., `"imports redis.asyncio"`, `"calls KEYS"`, `"matches query term 'session'"`).
- Stable sort key: score desc, then path asc (bytewise).

**Spec** §6.1 behavior 2–3, §22 (weights delegated), D9, D10, AC3.
**Depends on** 9.
**Architecture nodes** `SCORE`.
**Done when** a golden pins the exact ranking of `redis-app`; property tests assert `1 ≤ score ≤ 10`, byte-identical output across runs, and that ties break by path; a test shows a `query` boost reorders as intended.
**Ownership** `src/ez_redis/engine/scoring.py`, `tests/golden/search/scoring_*.json`.

---

#### Phase 11 — In-process result cache

**Delivers** `src/ez_redis/engine/cache.py` (in-process half): a bounded LRU (fixed entry count) keyed by `(resolved repo_root, query)`; each entry stores results plus `(mtime_ns, size)` fingerprints for every matched file and a creation timestamp; lookup revalidates fingerprints and a 10-minute TTL; `refresh=True` bypasses; clock and filesystem stat are injectable for tests.

**Spec** §6.1 behavior 4, D11, AC5.
**Depends on** 10.
**Architecture nodes** `LRU`.
**Done when** tests cover hit, TTL expiry, invalidation on mtime change, invalidation on size change with unchanged mtime, LRU eviction at the bound, `refresh` bypass, and key isolation between two queries.
**Ownership** `src/ez_redis/engine/cache.py` (in-process section), `tests/unit/test_cache_memory.py`.

---

#### Phase 12 — `search_redis` tool assembly

**Delivers** `src/ez_redis/tools/search.py`: validates input (Phase 6), confines `repo_root` (Phase 4), consults the cache (11), runs discovery (8) → dependency facts (9) → scoring (10), builds §6.1 output (`cached`, `truncated`, `scanned_files`, results with `reasons[]` and `matches[]` whose excerpts pass `redact_redis_urls` then `sanitize_excerpt(200)` **before** insertion), and renders markdown (ranked table + top reasons).

**Spec** §6.1 (all), AC3, AC4, AC5.
**Depends on** 7, 11.
**Architecture nodes** `T_SEARCH`.
**Done when** AC3–AC5 are automated tests through the real server call path; `secrets-app` yields redacted excerpts and never lists `.env`; Inspector call returns `structuredContent` that validates against the output schema. **→ Milestone M2.**
**Ownership** `src/ez_redis/tools/search.py`, `tests/golden/search/`.

---

### Track C — Parser & IR

#### Phase 13 — IR data model

**Delivers** `src/ez_redis/engine/ir.py` — frozen dataclasses:
- `RedisCall(command: str, receiver: Literal["client","pipeline","unknown"], args: tuple[LiteralArg, ...], kwargs: Mapping[str, LiteralArg], in_loop: bool, loop_depth: int, enclosing_function: str | None, decorators: tuple[str, ...], is_cache_like_key: bool, order_index: int, location: Location)`.
- `ClientConstruction(scope: Literal["module","function","loop"], has_connection_pool: bool, has_connect_timeout: bool, has_socket_timeout: bool, via_from_url: bool, order_index, location)`.
- `DatastoreWrite(kind: Literal["orm_commit","orm_save","orm_update","sql_write"], enclosing_function, order_index, location)`.
- `FileFacts(path, parse_status: Literal["ok","syntax_error","unreadable"], redis_calls, client_constructions, datastore_writes)`.
- Module docstring documents the two extension seams — a future `Parser` producing `FileFacts` for another language, and a future `EvidenceSource` adding facts — **as prose only**. No abstract classes, no registries (D27).

**Spec** §6.2 behavior 2, §7.1, D27.
**Depends on** 5.
**Architecture nodes** `IR`.
**Done when** construction tests for every dataclass; immutability tests; a review checklist item confirms no seam code exists.
**Ownership** `src/ez_redis/engine/ir.py`, `tests/unit/test_ir.py`.

> **Contract freeze** applies (Part V).

---

#### Phase 14 — Python parser, part 1: receiver resolution

**Delivers** `src/ez_redis/engine/parse_py.py` (receiver section) using stdlib `ast`:
- Import forms: `import redis`, `import redis as r`, `from redis import Redis, StrictRedis`, `from redis.asyncio import Redis`, `import redis.asyncio as aioredis`.
- Bindings: `x = redis.Redis(...)`, `x = Redis.from_url(...)`, `x = redis.Redis(connection_pool=pool)`, `p = x.pipeline()`, `async with x.pipeline() as p`, function parameters annotated `redis.Redis`/`Redis`, class attributes assigned in `__init__` and used via `self.x`.
- Scope tracking (module, function, nested function, class) with shadowing handled conservatively.
- Anything unresolvable is recorded as receiver `unknown` — never guessed. Wrapper libraries (django-redis, fastapi-cache) resolve to `unknown` per A3.
- `SyntaxError`/`UnicodeDecodeError` produce `FileFacts(parse_status="syntax_error" | "unreadable")`.

**Spec** §3.4, A3, D4.
**Depends on** 13.
**Architecture nodes** `PARSE`.
**Done when** goldens for each import/binding/scope form; `wrapper-heavy-app` resolves to `unknown`; `broken-app` yields the two failure statuses without raising.
**Ownership** `src/ez_redis/engine/parse_py.py` (receiver section), `tests/golden/parse/receivers_*`.

---

#### Phase 15 — Python parser, part 2: call extraction and control-flow context

**Delivers** `parse_py.py` (calls section):
- Emits `RedisCall` for method calls on resolved receivers; normalizes method → command (`keys`→`KEYS`, `scan_iter`→`SCAN`, `smembers`→`SMEMBERS`, `hgetall`→`HGETALL`, `lrange`→`LRANGE`, `set`/`setex`/`psetex`, `expire`, `delete`/`unlink`, `flushall`, `flushdb`, `execute_command("<NAME>", …)` with literal first arg).
- Literal argument resolution: `str`/`int`/`bool` constants, simple concatenations, f-string **prefixes** (`f"user:{id}"` → prefix `"user:"`), keyword capture (`ex=`, `px=`, `exat=`, `pxat=`, `nx=`, `count=`, `match=`).
- Control flow: `in_loop` and `loop_depth` across `for`, `while`, `async for`, list/set/dict comprehensions, generator expressions.
- Enclosing function name and decorator dotted names (groundwork for Track I route detection).
- `order_index`: statement ordering within the enclosing function body (needed by EZR021, EZR050).

**Spec** §6.2 behavior 2, A4 inputs, §7.2 rule inputs.
**Depends on** 14.
**Architecture nodes** `PARSE`.
**Done when** goldens for sync/async clients, pipelines, loops at depth 1–3, comprehensions, every TTL keyword, `execute_command` literal and dynamic forms, and ordering indices; parsing a generated 5 000-line file completes under a budget the owner measures and records in the PR.
**Ownership** `parse_py.py` (calls section), `tests/golden/parse/calls_*`.

---

#### Phase 16 — Python parser, part 3: client construction, datastore writes, cache-key heuristic

**Delivers** `parse_py.py` (construction/writes section) and `src/ez_redis/engine/heuristics.py`:
- `ClientConstruction` facts: scope classification (module / function / inside a loop), `connection_pool=` presence, `socket_connect_timeout` and `socket_timeout` presence, `from_url` form.
- `DatastoreWrite` facts: SQLAlchemy (`session.commit()`, `session.add()`, `session.execute(update(...))`), Django ORM (`.save()`, `.update()`, `.create()`, `.delete()` on querysets/models), raw SQL string literals matching anchored `^\s*(UPDATE|INSERT|DELETE)\b` (case-insensitive) passed to `execute`.
- `is_cache_like_key(literal_or_prefix, file_path)`: A4 heuristic — key contains any of `cache`, `sess`, `tmp`, `token`, `rate` (segment-aware, case-insensitive) **or** the file path contains `cache`.

**Spec** §6.2 behavior 2, §7.2 EZR030/031/050 inputs, A4.
**Depends on** 15.
**Architecture nodes** `PARSE`.
**Done when** goldens for each construction scope and each ORM/SQL write form; heuristic unit tests with positive keys (`"cache:user:1"`, `"session:abc"`) and negative keys (`"order:42"`, `"leaderboard"`).
**Ownership** `parse_py.py` (construction/writes section), `src/ez_redis/engine/heuristics.py`, `tests/golden/parse/construction_*`, `tests/unit/test_heuristics.py`.

---

### Track D — Rule Catalog

#### Phase 17 — Rule framework, registry, and golden harness

**Delivers**
- `src/ez_redis/engine/rules/__init__.py`: a `Rule` `Protocol` (`meta: RuleMeta`; `apply(facts: FileFacts) -> list[Finding]`), an **explicit** `REGISTRY: Final[tuple[Rule, ...]]` (no import-time scanning), and `export_catalog_markdown()` used by Phase 45.
- `tests/golden/rules/_harness.py`: convention `tests/golden/rules/<RULE_ID>/{positive,negative,edge}.py` + `expected.json`; runs the full parse → rule pipeline on each file and diffs findings.
- `docs/rule-authoring.md`: the checklist every rule PR must satisfy — detection description, `before`/`after` text, rationale paragraph, ≥1 `DocRef`, `min_redis_version` where applicable, positive/negative/edge goldens.

**Spec** §7.2 ("every rule ships with…"), §8 docs, D14, AC6 structure.
**Depends on** 13, 5.
**Architecture nodes** `RULES`.
**Done when** a trivial example rule (deleted before merge or kept as `_example`) passes the harness; registry order is deterministic and tested; the exporter produces a markdown table with one row per registered rule.
**Ownership** `src/ez_redis/engine/rules/__init__.py`, `tests/golden/rules/_harness.py`, `docs/rule-authoring.md`.

---

#### Phase 18 — Rule EZR001: `KEYS` → `SCAN` (reference rule)

**Delivers** `rules/ezr001_keys_to_scan.py`: flags `KEYS` on client or pipeline receivers (critical/high), and on `unknown` receivers (critical/medium); `after` renders a `scan_iter(match=<pattern>, count=<n>)` loop preserving the original pattern literal when available; rationale explains O(N) blocking on a single-threaded server; `DocRef`s: redis.io `SCAN`, redis.io `KEYS` warning, agent-skills *redis-connections* §3 (attributed, paraphrased). This is the **template** other rule authors copy.

**Spec** §7.2 EZR001, AC6, AC7 (shared path with command mode).
**Depends on** 17, 15.
**Architecture nodes** `R_SCAN`.
**Done when** goldens: positive (`r.keys("user:*")`), negative (`scan_iter` already used), edge (`KEYS` on `unknown` receiver → medium; `keys` as an unrelated dict method on a non-redis object → no finding).
**Ownership** `src/ez_redis/engine/rules/ezr001_keys_to_scan.py`, `tests/golden/rules/EZR001/`.

---

#### Phase 19 — Rules EZR002–EZR004: `SMEMBERS`, `HGETALL`, unbounded `LRANGE`

**Delivers** three modules: `SMEMBERS` → `SSCAN` (warning/medium); `HGETALL` → `HSCAN` or `HMGET` of named fields when the consuming code indexes specific fields (warning/medium); `LRANGE key 0 -1` (literal `0` and `-1`) → paginated `LRANGE` with a bounded window (warning/high).

**Spec** §7.2 EZR002–004, AC6.
**Depends on** 18, 15.
**Architecture nodes** `R_SCAN`.
**Done when** goldens per rule; negatives confirm bounded `LRANGE 0 99`, `HMGET`, and `SSCAN` are not flagged.
**Ownership** `rules/ezr002_smembers_to_sscan.py`, `rules/ezr003_hgetall_to_hscan.py`, `rules/ezr004_lrange_unbounded.py`, their goldens.

---

#### Phase 20 — Rule EZR010: loop round-trips → pipeline / multi-key

**Delivers** `rules/ezr010_loop_pipeline.py`: detects ≥ 2 `RedisCall`s in the same loop body (or one call inside a comprehension) whose results are not consumed within the same iteration by a subsequent redis call (independence check via simple name-use analysis on the loop body); proposes `pipeline()` for mixed commands (warning/medium) and `MGET`/`MSET`/`HMGET` when all calls share a command and target (warning/high); `after` shows the pipeline form and, when applicable, the multi-key form; negative when calls already occur on a pipeline receiver.

**Spec** §7.2 EZR010, AC6.
**Depends on** 17, 15.
**Architecture nodes** `R_PIPE`.
**Done when** goldens: same-command loop, mixed-command loop, comprehension, negatives (single call per loop, already pipelined, dependent calls where the second uses the first's result).
**Ownership** `rules/ezr010_loop_pipeline.py`, `tests/golden/rules/EZR010/`.

---

#### Phase 21 — Rules EZR020–EZR021: TTL hygiene

**Delivers**
- `rules/ezr020_set_without_ttl.py`: `SET` (and `MSET`) with no `ex/px/exat/pxat` on a cache-like key (warning/medium); when the heuristic is negative the finding is emitted at **low** confidence (never hook-eligible); `after` adds `ex=<placeholder>` with a rationale on TTL selection and jitter (Upstash guidance summarized, linked).
- `rules/ezr021_set_then_expire.py`: `SET k` followed by `EXPIRE k` on the same key literal/prefix within the same function (warning/high) → single atomic `set(k, v, ex=…)`; cites redis.io `SET` options and notes `SETEX` equivalence.

**Spec** §7.2 EZR020–021, A4, AC6.
**Depends on** 17, 16.
**Architecture nodes** `R_TTL`.
**Done when** goldens covering `nx=True` combinations, `setex`/`psetex` (negatives), `SET` then `EXPIRE` on a different key (negative), non-cache key (low confidence).
**Ownership** the two rule modules and goldens.

---

#### Phase 22 — Rules EZR030–EZR031: connection hygiene

**Delivers**
- `rules/ezr030_client_per_call.py`: `ClientConstruction` with scope `function` or `loop` (warning/high; medium when the function is a recognized factory called once at module level) → module-level client or shared `ConnectionPool`; cites agent-skills *redis-connections* §1 (paraphrased).
- `rules/ezr031_missing_timeouts.py`: construction lacking `socket_connect_timeout` or `socket_timeout` (info/high) → explicit values with connect < read and `retry_on_timeout` note; cites §5.

**Spec** §7.2 EZR030–031, AC6.
**Depends on** 17, 16.
**Architecture nodes** `R_CONN`.
**Done when** goldens: module-level (negative), function-level, loop-level, `from_url` forms, timeouts present (negative) / absent.
**Ownership** the two rule modules and goldens.

---

#### Phase 23 — Rule EZR040: destructive and debug commands

**Delivers** `rules/ezr040_destructive.py`: flags `FLUSHALL`, `FLUSHDB`, `DEBUG *`, `CONFIG SET`, `SAVE`, `BGSAVE`, `SHUTDOWN` — critical; confidence high for direct methods (`r.flushall()`), medium for `execute_command("FLUSHALL")` with a literal, low for dynamic command strings; rationale recommends removal or isolation behind explicit ops tooling and ACL/command-renaming (agent-skills *redis-security*, paraphrased). **Advisory only** — no hook ever blocks on it (D3).

**Spec** §7.2 EZR040, D3, AC6.
**Depends on** 17, 15.
**Architecture nodes** `R_DESTR`.
**Done when** goldens across every listed command and both call forms; a test shows Phase 27 policy lowers severity to `info` for files under `tests/`.
**Ownership** `rules/ezr040_destructive.py`, `tests/golden/rules/EZR040/`.

---

#### Phase 24 — Rule EZR050: cache-aside write ordering

**Delivers** `rules/ezr050_cache_aside_order.py`: a `DELETE`/`UNLINK` whose `order_index` precedes a `DatastoreWrite` in the same function (warning/medium) → reorder to write-then-delete; rationale summarizes the race (a concurrent read refills the cache with stale data between delete and write) with links to the Upstash summary and Microsoft's cache-aside guidance. Explicitly **does not** implement null-sentinel or stampede detection (D28).

**Spec** §7.2 EZR050, D28, AC6.
**Depends on** 17, 16.
**Architecture nodes** `R_CA`.
**Done when** goldens: delete-before-commit (positive), delete-after-commit (negative), delete and write in different functions (negative).
**Ownership** `rules/ezr050_cache_aside_order.py`, `tests/golden/rules/EZR050/`.

---

### Track E — Command Mode, Policy, Render, `optimize_redis`

#### Phase 25 — Redis command table build pipeline

**Delivers**
- `scripts/build_command_table.py` — **dev-time only**; the single place in the repository permitted network access. Fetches the redis.io command reference and emits `src/ez_redis/knowledge/data/commands.json` with, per command: canonical name, group, arity summary, `since` version, `complexity` text, and a curated `replacement_hint` for commands targeted by rules (`KEYS→SCAN`, `SMEMBERS→SSCAN`, `HGETALL→HSCAN`, …). The artifact carries `command_table_version` and `generated_from` (source URL + date).
- `tests/unit/test_command_table.py`: validates the committed artifact against a JSON Schema; asserts every command referenced by any rule exists with `since` populated; asserts the file is sorted for stable diffs.
- Documentation of the refresh procedure in `CONTRIBUTING.md` (Phase 45 finalizes).

**Spec** §3.7, §17 (build-time generation), D13, D31, latitude L5.
**Depends on** 3.
**Architecture nodes** `CMDTAB`.
**Done when** the artifact validates; regeneration on an unchanged source produces an empty diff; CI never runs the fetch.
**Ownership** `scripts/build_command_table.py`, `src/ez_redis/knowledge/data/commands.json`, `tests/unit/test_command_table.py`.

---

#### Phase 26 — redis-cli tokenizer and command-mode analysis

**Delivers** `src/ez_redis/engine/cli_command.py`:
- Strict tokenizer for redis-cli syntax: whitespace separation, single- and double-quoted arguments with backslash escapes, no shell constructs; rejects control characters and inputs over the schema cap; case-insensitive command lookup.
- Lookup in the command table; unknown → exactly one `unknown_command` finding with the offending token and **no** suggestion (D19).
- Converts a recognized command into a synthetic `FileFacts` containing one `RedisCall` (receiver `client`, literal args, `order_index 0`) so the **same rules** from Track D evaluate it; `min_redis_version` attached when the proposed replacement is newer than 7.2 (D31).

**Spec** §6.2 `command` mode, D19, D31, AC7.
**Depends on** 25, 17.
**Architecture nodes** `CLIPARSE`.
**Done when** tokenizer tests (quotes, escapes, empty string, oversized, control chars); `KEYS user:*` → exactly one EZR001 finding; `FOOBAR x` → exactly one `unknown_command`; `keys user:*` behaves identically to uppercase.
**Ownership** `src/ez_redis/engine/cli_command.py`, `tests/unit/test_cli_command.py`.

---

#### Phase 27 — Policy layer

**Delivers** `src/ez_redis/engine/policy.py`, pure functions:
- Applies `RuleMeta` defaults, then rule-provided per-finding overrides.
- Path-based adjustment: findings in paths matching `tests/`, `test_*.py`, `*_test.py`, `conftest.py` drop one severity level (never below `info`).
- Filters by `min_severity` and `min_confidence`.
- Sets `hook_eligible = confidence >= medium`.
- Stable ordering (path asc, line asc, rule_id asc); truncation to the output cap with `truncated=True`.
- Produces the `summary` counts (`by_severity`, `by_confidence`).

**Spec** §6.2 behavior 4, D15, AC9.
**Depends on** 17.
**Architecture nodes** `POLICY`.
**Done when** parametrized tests over every filter combination; eligibility boundary test (medium → eligible, low → not); path adjustment; byte-stable ordering across shuffled inputs.
**Ownership** `src/ez_redis/engine/policy.py`, `tests/unit/test_policy.py`.

---

#### Phase 28 — Render layer

**Delivers** `src/ez_redis/engine/render.py`:
- Per finding: `before` (exact source slice from the analyzed text), `after` (rule-provided replacement), `unified_diff` via stdlib `difflib.unified_diff` with fixed `fromfile`/`tofile` labels and **no timestamps**, `rationale`, `doc_refs` resolved through the KB loader (Phase 31) by `rule_id` and merged with rule-provided refs, `min_redis_version`.
- Markdown renderer for a whole result: summary table, then per-finding sections with fenced diffs; deterministic ordering from Phase 27.
- Redaction pass (Phase 4) on every `before`/`after`/`excerpt` string before it leaves the engine.

**Spec** §6.2 behavior 5, D20.
**Depends on** 27, 31.
**Architecture nodes** `RENDER`.
**Done when** markdown goldens for a multi-finding result; diff semantics verified against `difflib`; a test iterates `REGISTRY` and asserts every rule resolves ≥ 1 `DocRef`; redaction test with a credentialed URL inside `before`.
**Ownership** `src/ez_redis/engine/render.py`, `tests/golden/render/`.

---

#### Phase 29 — `optimize_redis` tool assembly

**Delivers** `src/ez_redis/tools/optimize.py` composing three modes:
- `command` → Phase 26 → rules → policy → render.
- `snippet` → parse (14–16) → rules → policy → render; `syntax_error` yields an `unparseable_file` finding and `isError: false`.
- `repo_root` (+ optional confined `paths`) → `search_redis` (Phase 12) selects files with score ≥ the L6 threshold (or the explicit `paths`) → per-file analysis; `syntax_error`/`unreadable` become `unparseable_file`/`unreadable_file` findings and analysis continues; caps enforced with `truncated`.
- Output per §6.2 with `mode`, `summary`, `findings`, `truncated`, plus markdown.

**Spec** §6.2 (all), §14 (selection), §15 (single-file failure is a finding), AC6–AC9.
**Depends on** 12, 26, 27, 28, 18–24.
**Architecture nodes** `T_OPT`.
**Done when** AC6–AC9 pass via the real server path; repo mode on a generated 500-Python-file fixture completes under the §8 recommended 10 s on CI hardware — the owner **measures** and records the number in the PR (never estimates). **→ Milestone M3.**
**Ownership** `src/ez_redis/tools/optimize.py`, `tests/golden/optimize/`.

---

### Track F — Knowledge Base

#### Phase 30 — Knowledge-base content curation

**Delivers** under `src/ez_redis/knowledge/data/`:
- `patterns.md`: cache-aside, write-through, write-behind, read-through — when to use, tradeoffs, main risk; TTL selection with jitter; null-sentinel; stampede protection (lock with token-checked release; probabilistic early refresh); versioned-namespace invalidation; hit-ratio measurement; common mistakes. **Summarized in our own words** from the Upstash guide with a link — no copied paragraphs or code.
- `rules_docs.md`: for each rule id — rationale text and `DocRef`s (redis.io command pages; agent-skills sections paraphrased with attribution).
- `checklist.md`: the design-time checklist required by AC12 — null-sentinel, stampede protection, TTL jitter, cache-down fall-through, `KEYS` prohibition, hit-ratio metric, key naming, ACL least privilege, TLS.
- `security_notes.md`: AUTH/ACL least privilege, TLS, network exposure, command renaming (agent-skills *redis-security*, paraphrased).
- `observability_notes.md`: `INFO` metrics to watch, `SLOWLOG`, `MEMORY DOCTOR` (agent-skills *redis-observability*, paraphrased).
- `ATTRIBUTIONS.md` at repo root listing every source and license.

**Spec** §3.6, §6.3 (checklist and plan sections), D13, D26, F6, F7.
**Depends on** 1.
**Architecture nodes** `KBDATA`.
**Done when** a second reviewer confirms paraphrase/summary; every rule id in the plan has an entry with ≥ 1 URL; attributions complete; a lint test asserts no line in the KB exceeds a length that would indicate a pasted block and that every URL is `https`.
**Ownership** `src/ez_redis/knowledge/data/*.md`, `ATTRIBUTIONS.md`.

---

#### Phase 31 — Knowledge-base loader and doc-ref resolution

**Delivers** `src/ez_redis/knowledge/kb.py`: loads bundled files via `importlib.resources`; parses `rules_docs.md` into a typed mapping once (module-level cache); exposes `doc_refs_for(rule_id) -> tuple[DocRef, ...]`, `pattern(name)`, `checklist() -> tuple[str, ...]`, `security_notes()`, `observability_notes()`, `kb_version`, `command_table_version`; malformed content raises at first access with a message naming the file and line.

**Spec** §16 (`--version` surfaces versions), D13.
**Depends on** 30.
**Architecture nodes** `KB`.
**Done when** accessor tests; a test asserts every registered rule id (Phase 17 registry) has refs; version strings surface; malformed-file test raises the documented error.
**Ownership** `src/ez_redis/knowledge/__init__.py`, `src/ez_redis/knowledge/kb.py`, `tests/unit/test_kb.py`.

---

### Track G — Hook Pack

#### Phase 32 — Hook host adapters

**Delivers**
- `src/ez_redis/hosts/__init__.py`, `hosts/claude.py`, `hosts/vscode.py`, `hosts/common.py`: parse hook stdin JSON into one internal `HookEvent(kind: Literal["prompt","pre_edit","session_start"], cwd: Path, prompt: str | None, edit_target_path: Path | None, edit_new_content: str | None)`.
- Host detection by **field shapes** (L2): Claude Code payloads carry `tool_input.file_path` / `content` / `new_string`; VS Code carries `tool_input.filePath` / `newString` / `code`. `tool_name` is never read.
- `hook_event_name` selects `kind`; unknown events → `None`.
- Tolerant parsing: unknown fields ignored; every string capped in length; malformed JSON, missing `cwd`, or oversized payload → `None` (caller treats as silent no-op).
- Recorded real payloads for both hosts committed under `tests/hooks/payloads/{claude,vscode}/*.json`.

**Spec** §7.3 host normalization, §13 entry point 2, A5, F2, AC18.
**Depends on** 9.
**Architecture nodes** `HOSTS`.
**Done when** every recorded payload normalizes to the expected `HookEvent`; malformed/oversized/unknown-event payloads yield `None`; a static test greps the `hosts/` package to prove `tool_name` is never referenced.
**Ownership** `src/ez_redis/hosts/`, `tests/hooks/payloads/`, `tests/hooks/test_hosts.py`.

---

#### Phase 33 — Dependency-gate disk cache

**Delivers** `src/ez_redis/engine/cache.py` (disk half): `gate_lookup(repo_root) -> DependencyFacts | None` and `gate_store(...)` using `$XDG_CACHE_HOME/ez-redis/<sha256(resolved repo_root)>.json` (fallback `~/.cache`); stored fields limited to `uses_redis`, `client_name`, `client_version`, `manifest_mtimes`, `written_at`; validity requires every recorded manifest mtime unchanged; corrupt/unreadable file → miss and atomic rewrite (write temp + rename); directory created `0700`; **never** writes under the repo.

**Spec** §7.3 gate cache, §15 (corruption → miss), D29.
**Depends on** 9.
**Architecture nodes** `GATE`.
**Done when** tests with `XDG_CACHE_HOME` pointed at `tmp_path` cover hit, mtime invalidation, corruption, permission-denied directory (→ miss, logged, no raise), and assert no file is created under the fixture repo.
**Ownership** `src/ez_redis/engine/cache.py` (disk section), `tests/unit/test_cache_disk.py`.

---

#### Phase 34 — `UserPromptSubmit` shim

**Delivers** `src/ez_redis/hook.py` (`python -m ez_redis.hook`), prompt path:
1. If `EZ_REDIS_DISABLE_HOOKS` is truthy → exit 0, empty stdout.
2. Parse stdin via Phase 32; `None` → exit 0, empty stdout.
3. Gate (a): Phase 33 lookup, falling back to Phase 9 detection + store. `uses_redis=False` → exit 0, empty.
4. Gate (b): `prompt_mentions_redis(prompt)`; false → exit 0, empty.
5. Run `search_redis` (Phase 12, cached) with `query=prompt`, `max_results=5`.
6. Emit **one line** of JSON: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "<facts>"}}` where `<facts>` is ≤ 600 characters of **declarative statements** (F9): detected client and version, top files with scores, and the sentence that `optimize_redis` and `redis_architecture` are available. The string `redis_conversion` does not exist in any template (D21 layer 2).
7. Any exception anywhere → one stderr JSON log line, exit 0, empty stdout.
- Imports of the engine are lazy and occur only after gate (a) so the common no-op path stays fast (§14).

**Spec** §7.3 UserPromptSubmit row and failure policy, §14, F9, D3, D16, D17, D21 layer 2, AC14, AC16.
**Depends on** 32, 33, 12.
**Architecture nodes** `HOOK`, `H_PROMPT`.
**Done when** corpus tests: non-Redis repo → empty stdout; Redis repo + non-Redis prompt → empty; Redis repo + Redis prompt → single valid JSON line ≤ 600 chars containing no `redis_conversion`; injected exception → exit 0 + stderr line; a test asserts the no-op path imports no `engine.parse_py`/`rules` modules.
**Ownership** `src/ez_redis/hook.py` (prompt path and `__main__`), `tests/hooks/test_prompt_hook.py`.

---

#### Phase 35 — `PreToolUse` shim

**Delivers** `hook.py`, edit path:
1. Same disable/parse/gate (a) steps as Phase 34.
2. Self-filter (VS Code ignores matchers): `edit_target_path` must end in `.py` **and** `edit_new_content` must contain a Redis term; otherwise exit 0, empty.
3. Run `optimize_redis` in `snippet` mode on `edit_new_content`; `unparseable_file` (fragments are common) → exit 0, empty.
4. Keep only `hook_eligible` findings; none → exit 0, empty.
5. Emit one JSON line with `additionalContext` ≤ 600 chars listing findings as facts (rule id, line, one-sentence issue, one-sentence fix). The output object **never** contains `permissionDecision`, `permissionDecisionReason`, `updatedInput`, `decision`, or `continue` (D3).

**Spec** §7.3 PreToolUse row, D2, D3, D15, D16, AC17, AC18.
**Depends on** 34, 29.
**Architecture nodes** `HOOK`, `H_EDIT`.
**Done when** corpus tests: `.py` with `KEYS` → context emitted; non-`.py` → silent; `.py` without Redis terms → silent; unparseable fragment → silent; only-low-confidence findings → silent; a key-allowlist test over every emitted object in the corpus asserts only `hookSpecificOutput.hookEventName` and `hookSpecificOutput.additionalContext` appear.
**Ownership** `hook.py` (edit path), `tests/hooks/test_edit_hook.py`.

---

#### Phase 36 — Hook configuration files, `SessionStart` warmer, hook documentation

**Delivers**
- `hooks/claude/settings.hooks.json`: `UserPromptSubmit`, `PreToolUse` (matcher `Write|Edit|MultiEdit`), optional `SessionStart`; command `python -m ez_redis.hook` (exec form with `args`).
- `hooks/vscode/ez-redis.hooks.json` (`.github/hooks` format): same events with `osx`/`linux` command and a `windows` PowerShell variant (D34).
- `hook.py` session path: warms the gate cache; emits at most one factual line (`additionalContext`) when the repo uses Redis; otherwise nothing.
- `docs/hooks.md`: installation per host, what each hook does and does not do, the 300 ms / 600-char budgets, `EZ_REDIS_DISABLE_HOOKS`, host trust settings (VS Code `chat.tools.edits.autoApprove` exclusion for hook scripts; Claude workspace trust), and the note that hook files are loaded at session start (memory `vscode-agent-hooks.md`).

**Spec** §3.3, §7.3 SessionStart row, §13 (hook tampering guidance), D1, D32, D34.
**Depends on** 35.
**Architecture nodes** `HOOKCFG`.
**Done when** both JSON files pass schema snapshot tests against the hosts' documented shapes; `SessionStart` behavior tests on Redis and non-Redis fixtures; manual verification in Claude Code and VS Code recorded in the PR with the host log lines proving the hooks loaded.
**Ownership** `hooks/`, `hook.py` (session path), `docs/hooks.md`, `tests/hooks/test_hook_configs.py`.

---

#### Phase 37 — Hook latency benchmark and 10k-file synthetic fixture

**Delivers**
- `tests/bench/generate_fixture.py`: deterministic (seeded) generator for a 10 000-file repository with a Redis-declaring `pyproject.toml`, a realistic directory spread, and ~2 % Redis-using Python files.
- `tests/bench/bench_hooks.py`: invokes the shim as a **real subprocess** 200× per event kind with recorded payloads, computes p50/p95 wall-clock in code, asserts p95 < 300 ms and every emitted context ≤ 600 chars; also records `search_redis` cold time on the fixture (informational, §8 REC).
- CI job `bench` (Linux) running the benchmark and publishing the numbers as a job summary.

**Spec** §7.3 latency budget, §8 performance, §14, D16, AC15.
**Depends on** 36, 2.
**Architecture nodes** `BENCH`, `CI`.
**Done when** CI `bench` is green with recorded p95; fixture generation is reproducible (same seed → same tree hash). **→ Milestone M4.**
**Ownership** `tests/bench/`, CI `bench` job.

---

### Track H — `redis_architecture`

#### Phase 38 — Architecture question bank

**Delivers** `src/ez_redis/architecture/questions.py`:
- Typed `Question(id, text, kind: single|multi|text|number, options: tuple[Option, ...], recommended, why_it_matters)`.
- **Mandatory eight:** `workload_type`, `read_write_ratio`, `scale` (RPS, key count, value size — numeric sub-fields), `staleness_tolerance`, `ttl_expectation`, `invalidation_trigger`, `consistency_needs`, `deployment_topology`.
- **Conditional follow-ups:** hot-key expectation → stampede strategy; multi-tenant → key prefixing/ACL; goal mentions search → RQE index fields and dialect; topology cluster → hash-tag requirements; write-heavy → write-behind durability tolerance.
- `next_questions(goal, answers, round_number) -> tuple[Question, ...]` — pure; returns empty when nothing remains or `round_number == 3`.
- `apply_defaults(answers) -> tuple[Answers, tuple[Assumption, ...]]` for `assume_defaults`.

**Spec** §6.3 question bank, D7, D23, AC10, AC11.
**Depends on** 6, 31.
**Architecture nodes** `QBANK`.
**Done when** round 1 yields ≥ 8 questions each with `recommended` and `why_it_matters`; conditional triggering tests per follow-up; a property test over random answer sequences proves termination within 3 rounds; defaults produce `Assumption(source="default")` entries.
**Ownership** `src/ez_redis/architecture/__init__.py`, `src/ez_redis/architecture/questions.py`, `tests/unit/test_questions.py`.

---

#### Phase 39 — Architecture planner

**Delivers** `src/ez_redis/architecture/planner.py` — pure planning from answers + optional repo facts:
- Pattern selection: cache-aside default; write-through when reads-after-writes must hit; write-behind only when write-heavy and durability tolerance is explicit; read-through as an organizational wrapper note.
- Key schema: colon-separated lowercase `{entity}:{id}:{attribute}`, tenant prefix when multi-tenant, hash tags when cluster + multi-key.
- TTL table by data class with jitter percentage; invalidation strategy (delete-on-write, event, versioned namespace) mapped from `invalidation_trigger`.
- Consistency and failure modes: cache-down fall-through to the datastore; DB-write-then-cache-delete ordering; stampede strategy when hot keys expected.
- **Capacity estimate computed in code** (keys × avg value size × overhead factor, ops/s from RPS and hit-ratio assumption) with all inputs echoed in the plan.
- Observability section (hit ratio, `used_memory`, `SLOWLOG`, `rejected_connections`); security section (ACL least privilege, TLS); risks with mitigations; the AC12 checklist from `kb.checklist()`.
- `render_plan_markdown(plan) -> str` from a template with fixed section order.

**Spec** §6.3 plan sections, D22, AC12 (checklist half).
**Depends on** 38, 31.
**Architecture nodes** `PLANNER`.
**Done when** golden plans for three profiles (read-heavy web, write-heavy counters, multi-tenant cluster); capacity arithmetic verified by an independent computation in the test; checklist contains all five AC12 items.
**Ownership** `src/ez_redis/architecture/planner.py`, `tests/golden/architecture/`.

---

#### Phase 40 — Mermaid diagram generation and minimal validator

**Delivers** `src/ez_redis/architecture/mermaid.py`:
- Generators producing 3–5 diagrams from a plan: data-flow (`flowchart`), read/write path (`sequenceDiagram`), key model (`flowchart` or `erDiagram`), failure/fallback (`flowchart`), and invalidation flow when a non-TTL strategy is chosen.
- **Bundled minimal validator** (L3): recognized diagram-type header; balanced `[]`, `()`, `{}`, quotes; node ids restricted to `[A-Za-z0-9_]`; no control characters; total size cap; labels escaped. Diagrams that fail validation are omitted and replaced by a note in `plan_markdown` — never returned broken (§15).

**Spec** §6.3 diagrams, §15, §22, D22, AC12 (diagram half).
**Depends on** 39.
**Architecture nodes** `MERMAID`.
**Done when** every generated diagram for the golden profiles passes the validator and is snapshot-tested; validator negative tests (unbalanced brackets, bad header, control chars, oversized); omission path test.
**Ownership** `src/ez_redis/architecture/mermaid.py`, `tests/unit/test_mermaid.py`, `tests/golden/architecture/diagrams/`.

---

#### Phase 41 — `redis_architecture` tool assembly

**Delivers** `src/ez_redis/tools/architecture.py`: optional repo pre-fill (Phase 12 ranking + Phase 16 facts → detected client, patterns, frameworks as `Assumption(source="repo")`), merge of `answers`, `assume_defaults` handling, round counting (`answers` carries `_round` metadata or the tool infers from answered ids), `status: needs_input` with the next questions or `status: complete` with `plan_markdown`, `diagrams`, `assumptions`, `risks`, `checklist`; markdown rendering of either state.

**Spec** §6.3 (all), D7, D23, AC10–AC12.
**Depends on** 7, 38, 39, 40, 12, 16.
**Architecture nodes** `T_ARCH`.
**Done when** AC10–AC12 pass through the real server path; a scripted three-round conversation test reaches `complete`; `assume_defaults` reaches `complete` in one call with defaults listed.
**Ownership** `src/ez_redis/tools/architecture.py`, `tests/golden/architecture/tool_*`.

---

### Track I — `redis_conversion`

#### Phase 42 — Conversion candidate detectors

**Delivers** `src/ez_redis/conversion/detectors.py` reusing Phase 15/16 facts plus a small **DB-read heuristic** (SQLAlchemy `select`/`query`, Django `.objects.filter/get/all`, raw `SELECT`):
- **EZC001** — function with a route decorator (`@app.route`, `@router.get/post…`, Django view patterns) containing a DB read and no redis/cache call → cache-aside candidate (medium).
- **EZC002** — module-level `dict` mutated inside handlers, or `functools.lru_cache`/`cache` on request-path functions → shared-cache candidate (medium).
- **EZC003** — DB increments (`UPDATE … +1`, `F('count') + 1`) or in-memory counters in handlers → `INCR`/`INCRBY` + `EXPIRE` candidate (medium).
- **EZC004** — session backend configured to DB or filesystem (Django `SESSION_ENGINE`, Flask-Session `SESSION_TYPE`) → Redis session store candidate (high).
- **EZC005** — `while True:` with `time.sleep` and a DB read → Pub/Sub or Streams candidate (**low**).
- **EZC006** — `order_by(...)[:n]` or SQL `ORDER BY … LIMIT` in a handler → sorted-set candidate (**low**).
- Each candidate carries `why` and `suggested_redis_primitive`.

**Spec** §6.4 detector table, D30.
**Depends on** 16, 17.
**Architecture nodes** `DETECT`.
**Done when** `framework-app` yields ≥ 1 candidate for each of EZC001–EZC004; EZC005/EZC006 candidates are `low`; negatives: a handler that already calls redis, a non-handler module-level dict.
**Ownership** `src/ez_redis/conversion/__init__.py`, `src/ez_redis/conversion/detectors.py`, `tests/golden/conversion/`.

---

#### Phase 43 — `redis_conversion` tool assembly and consent guard

**Delivers** `src/ez_redis/tools/conversion.py`: re-asserts D21 layer 3 (schema already rejects; the handler adds an actionable message explaining the tool runs only on explicit user request), discovers all Python files under `repo_root` within caps (independent of `search_redis` ranking, since candidates are by definition non-Redis code), runs detectors, groups the top candidates by suggested primitive, synthesizes `goal` from the group and `request_excerpt`, and delegates to the Phase 41 flow; output = `candidates[]` + the architecture response.

**Spec** §6.4 (all), D21, AC13, AC14.
**Depends on** 42, 41.
**Architecture nodes** `T_CONV`.
**Done when** AC13 passes via the real server path; a repository-wide test asserts the string `redis_conversion` appears nowhere in `hook.py`, `hosts/`, or `hooks/` (AC14). **→ Milestone M5 (together with 41).**
**Ownership** `src/ez_redis/tools/conversion.py`, `tests/golden/conversion/tool_*`, `tests/hooks/test_no_conversion_mention.py`.

---

### Track J — CLI, Documentation, Release

#### Phase 44 — CLI: `init`, `doctor`, `--version`

**Delivers** `src/ez_redis/cli.py` (argparse):
- Default invocation (no subcommand) runs the stdio server.
- `ez-redis init --host {claude,vscode,both} [--dry-run] [--force]`: prints the exact target paths and JSON it will write; `--dry-run` writes nothing; Claude target merges into `.claude/settings.json` non-destructively (existing hooks preserved, ez-redis entries added or updated in place); VS Code target writes `.github/hooks/ez-redis.json`; refuses to overwrite unrecognized content without `--force`; emits the PowerShell variant for VS Code (D34).
- `ez-redis doctor`: checks `rg` on `PATH` (with version), Python version, presence and validity of hook files per host, cache directory writability, `mcp` version; prints actionable fixes; exit code reflects health.
- `ez-redis --version`: package, KB, and command-table versions.

**Spec** §3.9, §16, D33, D34.
**Depends on** 36, 31, 25.
**Architecture nodes** `CLI`.
**Done when** tests in `tmp_path` repos cover dry-run (no writes), fresh write for each host, merge with pre-existing unrelated hooks, refusal without `--force`, and idempotent re-run; `doctor` output snapshots for healthy and unhealthy environments; `--version` test.
**Ownership** `src/ez_redis/cli.py`, `tests/unit/test_cli.py`.

---

#### Phase 45 — Documentation, rule-catalog generation, release hardening

**Delivers**
- `README.md`: what ez-redis is; install via `uvx ez-redis`; host configuration snippets for Claude Code and VS Code; `ez-redis init`; tool reference (purpose, inputs, outputs, examples for all four tools); hook behavior, budgets, and how to disable; security posture summary (§13); troubleshooting (`doctor`).
- `CONTRIBUTING.md`: development setup, quality gates, rule-authoring checklist (from Phase 17), golden workflow, KB attribution rules, command-table refresh procedure, phase/PR conventions from Part V.
- `docs/rules.md` **auto-generated** from `export_catalog_markdown()`; CI `docs-current` job regenerates and fails on diff.
- `CHANGELOG.md` (Keep-a-Changelog format) with `0.1.0`.
- `.github/workflows/release.yml`: on tag — `uv build`, `pip-audit`, full test suite, PyPI **trusted publishing**.
- Final acceptance sweep: a CI job or documented script that runs every AC1–AC20 check; repository history audit for secrets (AC20).

**Spec** §8 docs and packaging, §16, D12, D24, D26, AC19, AC20.
**Depends on** all prior phases.
**Architecture nodes** `DOCS`, `CI`, `PKG`.
**Done when** AC1–AC20 are green on the release commit; `git log -p` contains no secrets; PyPI publish succeeds from CI; on a clean machine `uvx ez-redis doctor` reports healthy. **→ Milestone M6.**
**Ownership** `README.md`, `CONTRIBUTING.md`, `docs/rules.md`, `CHANGELOG.md`, `.github/workflows/release.yml`, CI `docs-current` job.

---

## Part IV — Traceability

### IV.1 Acceptance criteria → phases

| AC | Requirement (abridged) | Phases |
|---|---|---|
| AC1 | Server starts; Inspector lists four tools with both schemas; outputs validate | 7, 12, 29, 41, 43, 45 |
| AC2 | Unknown field / bad `repo_root` / traversal → error naming field, no partial work | 4, 6, 7 |
| AC3 | Ranked list, unique paths, scores in [1,10], ≤ `max_results` | 10, 12 |
| AC4 | Credentialed URL redacted; `.env` never appears | 4, 8, 12 |
| AC5 | Cache hit on second call; invalidation on mtime or `refresh` | 11, 12 |
| AC6 | Every rule has positive+negative goldens; engine coverage ≥ 90 % | 17–24, 29 |
| AC7 | `KEYS user:*` → one EZR001 with SCAN; `FOOBAR x` → one `unknown_command` | 18, 25, 26, 29 |
| AC8 | Syntax error → `unparseable_file`, `isError: false` | 14, 29 |
| AC9 | Low confidence → not hook-eligible; medium/high → eligible | 27, 29 |
| AC10 | First call → `needs_input` with ≥ 8 questions; ≤ 3 rounds | 38, 41 |
| AC11 | `assume_defaults` → `complete` with defaults as assumptions | 38, 41 |
| AC12 | 3–5 valid diagrams; checklist contains the five items | 30, 39, 40, 41 |
| AC13 | Consent guard; candidates per EZC001–004; 005/006 low | 6, 42, 43 |
| AC14 | `redis_conversion` never in hook output | 34, 43 |
| AC15 | Hook p95 < 300 ms; ≤ 600 chars | 37 |
| AC16 | Non-Redis repo → hooks silent | 33, 34 |
| AC17 | No `permissionDecision`/`updatedInput`; context only with eligible findings | 35 |
| AC18 | Both hosts' payloads handled | 32, 35 |
| AC19 | CI green: lint, types, tests, audit, Inspector, bench | 2, 37, 45 |
| AC20 | No secrets in repo or history | 45 |

### IV.2 Decisions → enforcing phases

| Decision | Phases |
|---|---|
| D1, D32 two artifacts; Claude Code + VS Code | 32, 36, 44 |
| D2, D3 intercept file edits; advise only | 35 |
| D4 Python / redis-py only | 14, 15, 16 |
| D5 no live Redis | global guardrail (Part VI); dependency check in 45 |
| D6 server never writes to the repo | 7 (no write helpers in server/tools), 44 (`init` is CLI, prints first) |
| D7, D23 agent-mediated questions; `assume_defaults` | 38, 41 |
| D8 `rg`, no `jq` | 8 |
| D9, D10, D11 ranked list; heuristic; in-process cache | 10, 11, 12 |
| D12 PyPI / uvx / stdio / ≥ 3.11 | 1, 7, 45 |
| D13 bundled offline KB | 25, 30, 31 |
| D14, D28 six families; ordering-only cache-aside | 18–24 |
| D15 severity × confidence; eligibility | 27, 35 |
| D16, D17, D29 hook budget; in-process import; disk gate cache | 33, 34, 35, 37 |
| D18 boundary, secrets, caps | 4, 8, 12, 29 |
| D19 strict CLI parser | 26 |
| D20 structured + markdown | 7, 28 |
| D21 three-layer guard | 6, 7, 34, 43 |
| D22 plan + 3–5 validated diagrams | 39, 40 |
| D24 quality gates | 1, 2, 37, 45 |
| D25 stderr JSON logs | 1 |
| D26 MIT + attribution | 1, 30 |
| D27 simplified pipeline; seams as prose | 13 |
| D30 six conversion candidates; two low | 42 |
| D31 Redis ≥ 7.2; min-version notes | 25, 26, 28 |
| D33 `init` | 44 |
| D34 Windows best-effort | 2, 36, 44 |

### IV.3 Architecture nodes → phases

| Node | Phase | Node | Phase | Node | Phase |
|---|---|---|---|---|---|
| `PKG` | 1, 45 | `LOG` | 1 | `CI` | 2, 37, 45 |
| `TESTS` | 3 | `SAFE` | 4 | `TYPES` | 5 |
| `SCHEMAS` | 6 | `SERVER`, `DUAL` | 7 | `DISC`, `RG` | 8 |
| `TERMS`, `MANIF` | 9 | `SCORE` | 10 | `LRU` | 11 |
| `T_SEARCH` | 12 | `IR` | 13 | `PARSE` | 14–16 |
| `RULES` | 17 | `R_SCAN` | 18, 19 | `R_PIPE` | 20 |
| `R_TTL` | 21 | `R_CONN` | 22 | `R_DESTR` | 23 |
| `R_CA` | 24 | `CMDTAB` | 25 | `CLIPARSE` | 26 |
| `POLICY` | 27 | `RENDER` | 28 | `T_OPT` | 29 |
| `KBDATA` | 30 | `KB` | 31 | `HOSTS` | 32 |
| `GATE` | 33 | `H_PROMPT` | 34 | `H_EDIT` | 35 |
| `HOOKCFG` | 36 | `BENCH` | 37 | `QBANK` | 38 |
| `PLANNER` | 39 | `MERMAID` | 40 | `T_ARCH` | 41 |
| `DETECT` | 42 | `T_CONV` | 43 | `CLI` | 44 |
| `DOCS` | 36, 45 | `HOOK` | 34–36 | `SEAM1`, `SEAM2` | 13 (prose only) |

---

## Part V — Phase Handoff Protocol (for parallel teams)

1. **Claim.** Open a draft PR titled `phase-NN: <name>`; the body links this plan, the spec sections satisfied, and the `.mmd` node ids delivered.
2. **Contracts first.** After M1, any change to Phase 5 (`types.py`), Phase 6 (`schemas.py`), or Phase 13 (`ir.py`) goes in a separate PR titled `contracts: <change>` and requires sign-off from the owners of every dependent phase currently in flight.
3. **Architecture drift check.** A PR that adds, removes, or re-wires a component edits `docs/plans/ez-redis-architecture.mmd` in the same PR, re-validates it, and cites the node ids.
4. **Evidence, not assertion.** The PR includes the exact commands run and their output: `ruff check`, `ruff format --check`, `pyright --strict`, `pytest` (with coverage for engine phases), benchmarks where applicable. "Should pass" is not evidence.
5. **Numbers come from code.** Any latency, size, or capacity figure in a PR or doc is produced by a script or test, never derived by hand.
6. **Memory.** Bugs, host quirks, and conventions discovered during the phase are recorded in `/memories/repo/` or `/memories/` before merge.
7. **Return-to-Brainstorm trigger.** If a phase uncovers an implementation-critical contradiction or a missing requirement in the spec, **stop**, do not guess, and raise it for a spec v2 revision. Examples that qualify: a host hook schema that cannot carry `additionalContext`; an `mcp` v2 API that cannot express `outputSchema`; a rule that cannot be made deterministic.

---

## Part VI — Guardrails Binding Every Phase

- No live Redis connection code; no `redis` package in runtime dependencies (D5).
- No writes to the analyzed repository from server, tool, or hook code paths; only `ez-redis init` writes, and only after printing what it will write (D6, D33).
- No `updatedInput`, `permissionDecision`, `decision: block`, or `continue: false` in any hook output (D3).
- No runtime network access; Phase 25's build script is the sole dev-time exception and is never invoked by the package or CI (§9, L5).
- No new runtime dependencies beyond `mcp` (and its transitive `pydantic`) without a spec revision (§17).
- No additional languages, rule families, transports, or MCP features marked deprecated (Sampling, Roots, Logging) (§4, §5).
- No secret-like file is ever opened; every excerpt is redacted and sanitized before it leaves the engine (§13).

---

## Part VII — Risk Register for Execution

| Risk | Signal | Response |
|---|---|---|
| `mcp` v2 API differs from README expectations | Phase 7 cannot register `outputSchema` or structured output as planned | Verify against v2 docs first; if the capability is absent, this is a return-to-Brainstorm trigger (spec D20). |
| Rule false positives erode trust | Golden negatives fail to cover real code shapes | Every rule PR must include at least one negative drawn from a real open-source pattern; low confidence keeps doubtful findings out of hooks. |
| 300 ms budget missed | Phase 37 benchmark red | Profile the no-op path first (import time), then gate cache, then `rg` argv; never widen the budget without a spec revision. |
| Host hook schemas change mid-project | Phase 32 payload fixtures stop matching a live host | Re-record payloads; adapters are tolerant by design; `doctor` surfaces mismatches. |
| Merge conflicts on shared modules | Two phases editing `parse_py.py` or `cache.py` concurrently | Sections are assigned (14/15/16; 11/33); owners coordinate in the PR; if contention persists, split files — an internal refactor, no spec impact. |
| Scope creep toward live Redis or auto-apply | Reviewer sees a Redis client import or file write in a tool path | Guardrails in Part VI are CI-checked in Phase 45 (dependency list, grep for write calls in `tools/` and `hook.py`). |

---

*End of plan. No code, configuration, or build artifacts were created by this document.*
