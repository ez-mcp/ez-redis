# ez-redis — Architecture Diagrams

Companion to `2026-09-01-ez-redis-mcp-server.md` (spec v1, **APPROVED 2026-09-01**). Every diagram reflects user-approved decisions D1–D34; nothing here introduces new requirements.

---

## 1. System context — two artifacts, one engine

Shows why ez-redis ships **two** deliverables (D1): the MCP server (model-invoked tools) and the hook pack (host-invoked shell shim). Both import the same pure engine library in-process (D17). The server never sees prompts; only hooks do (F1).

```mermaid
flowchart TB
    subgraph Host["Agent host (Claude Code / VS Code)"]
        U[Developer prompt]
        A[LLM agent]
        HE[Hook events\nUserPromptSubmit / PreToolUse]
    end

    subgraph EZ["ez-redis package (PyPI)"]
        S["MCP server\n(stdio, mcp v2)"]
        H["Hook shim\npython -m ez_redis.hook"]
        E["Core engine\n(pure library)"]
        KB["Bundled knowledge base\n+ command table"]
    end

    FS[("User repository\n(read-only)")]
    RG["ripgrep (rg)"]

    U --> A
    U --> HE
    A -- "tools/call" --> S
    HE -- "stdin JSON" --> H
    H -- "additionalContext (facts, ≤600 chars)" --> A
    S --> E
    H --> E
    E --> KB
    E -- "argv-only subprocess" --> RG
    RG --> FS
    E -- "bounded reads" --> FS
```

---

## 2. Core engine pipeline (simplified per D27)

The reference diagram's Dynamic Analysis, Evidence Fusion, and Change/Execution Manager were removed because v1 has no live Redis (D5) and never writes to the repo (D6). The **IR** is the documented seam for a future second language or dynamic evidence source.

```mermaid
flowchart LR
    IN["Input\ncommand | snippet | repo_root"]
    D["Discover\nrg + term list + caps"]
    P["Parse\nPython ast"]
    IR["IR\nRedisCall · ClientConstruction · DatastoreWrite"]
    R["Rules\nEZR001–EZR050"]
    PO["Policy\nseverity × confidence\nhook eligibility · filters"]
    RE["Render\nbefore/after · unified diff\nrationale · doc_refs · min version"]
    OUT["structuredContent + markdown"]

    IN --> D --> P --> IR --> R --> PO --> RE --> OUT

    X1["(v2 seam) other-language parser"]:::seam -.-> IR
    X2["(v2 seam) dynamic evidence source"]:::seam -.-> IR

    classDef seam fill:none,stroke-dasharray: 4 4,stroke:#888,color:#888
```

---

## 3. Hook decision flow (D16, D3)

Both hooks are gated twice and fail open to silence. No `permissionDecision`, no `updatedInput`, ever.

```mermaid
flowchart TD
    EV[Hook event fires] --> HOST{Detect host\nby field casing / tool names}
    HOST --> NORM[Normalize to internal event]
    NORM --> G1{Gate A\nrepo depends on Redis?\ndisk-cached manifest scan}
    G1 -- no --> QUIET[exit 0, empty stdout]
    G1 -- yes --> KIND{Event kind}

    KIND -- UserPromptSubmit --> G2a{Gate B\nprompt mentions\nRedis / caching terms?}
    G2a -- no --> QUIET
    G2a -- yes --> SR[search_redis · cached]
    SR --> CTX1["additionalContext:\nfactual file list + scores\n+ available tools"]

    KIND -- PreToolUse file edit --> G2b{Gate B\n.py target AND\nnew content has Redis terms?}
    G2b -- no --> QUIET
    G2b -- yes --> OR[optimize_redis · snippet mode]
    OR --> F{≥1 hook_eligible\nfinding?}
    F -- no --> QUIET
    F -- yes --> CTX2["additionalContext:\nfindings, ≤600 chars"]

    CTX1 --> DONE[exit 0]
    CTX2 --> DONE
    ERR[Any exception] --> LOG[stderr JSON line] --> QUIET
```

---

## 4. `search_redis` sequence (D9, D10, D11)

```mermaid
sequenceDiagram
    participant Agent
    participant Server as MCP server
    participant Cache as In-process LRU
    participant RG as rg
    participant FS as Repo files

    Agent->>Server: search_redis(repo_root, query?, max_results?)
    Server->>Server: validate schema, resolve repo_root
    Server->>Cache: lookup (repo_root, query)
    alt hit and fingerprints unchanged and TTL valid
        Cache-->>Server: ranked results (cached=true)
    else miss / stale / refresh
        Server->>RG: rg --json -e term1 -e term2 ... --max-filesize
        RG->>FS: gitignore-aware scan
        RG-->>Server: match stream
        Server->>Server: skip secret-like files, redact URLs, apply caps
        Server->>Server: score 1–10 (deterministic heuristic + query boost)
        Server->>Cache: store with (mtime,size) fingerprints
    end
    Server-->>Agent: structuredContent {results[...], cached, truncated} + markdown
```

---

## 5. `optimize_redis` — three entry modes

```mermaid
flowchart TD
    CALL[optimize_redis call] --> MODE{exactly one of\ncommand | snippet | repo_root}
    MODE -- none or >1 --> VERR[validation error]

    MODE -- command --> CP[redis-cli tokenizer]
    CP --> CT{in bundled\ncommand table?}
    CT -- no --> UNK[finding: unknown_command\nno suggestion]
    CT -- yes --> RULES

    MODE -- snippet --> AST1[ast.parse]
    AST1 -- SyntaxError --> UNP[finding: unparseable_file]
    AST1 -- ok --> IRB[build IR]

    MODE -- repo_root --> SR[search_redis · select files]
    SR --> AST2[ast.parse each file]
    AST2 --> IRB

    IRB --> RULES[apply EZR rules]
    RULES --> POL[policy: severity × confidence\nmin_* filters · hook_eligible]
    POL --> REN[render diff · rationale · doc_refs]
    REN --> OUT[structuredContent + markdown]
```

---

## 6. `redis_architecture` multi-round flow (D7, D23)

Agent-mediated questions; bounded to three rounds; `assume_defaults` short-circuits with every default recorded as an assumption.

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Tool as redis_architecture
    participant KB as Knowledge base

    Agent->>Tool: call(goal, repo_root?)
    Tool->>Tool: pre-fill facts from repo (optional)
    alt assume_defaults = true
        Tool->>KB: patterns, checklist
        Tool-->>Agent: status=complete, plan, diagrams, assumptions(source=default)
    else
        Tool-->>Agent: status=needs_input, questions[≥8] with recommended defaults
        Agent->>User: ask questions (host UI)
        User-->>Agent: answers
        Agent->>Tool: call(goal, answers)
        opt conditional follow-ups (max 2 more rounds)
            Tool-->>Agent: needs_input (follow-ups)
            Agent->>User: ask
            User-->>Agent: answers
            Agent->>Tool: call(goal, answers)
        end
        Tool->>KB: patterns, checklist, doc refs
        Tool->>Tool: choose pattern, key schema, TTL table, invalidation, capacity calc
        Tool->>Tool: generate 3–5 mermaid diagrams, validate syntax
        Tool-->>Agent: status=complete, plan_markdown, diagrams, assumptions, risks, checklist
    end
    Agent-->>User: plan + diagrams
```

---

## 7. `redis_conversion` guard and delegation (D21, D30)

```mermaid
flowchart TD
    CALL[redis_conversion call] --> G{user_requested_optimization == true\nAND request_excerpt present?}
    G -- no --> ERR[validation error:\nrequires explicit user request]
    G -- yes --> DET[run detectors EZC001–EZC006]
    DET --> C{any candidates?}
    C -- no --> NONE[return empty candidates + explanation]
    C -- yes --> GROUP[group top candidates\nsynthesize goal]
    GROUP --> ARCH[delegate to redis_architecture\nquestion flow]
    ARCH --> OUT[candidates + architecture response]

    NOTE["Hook context never names this tool\nTool description forbids unsolicited use"]:::note
    classDef note fill:#fff8e1,stroke:#f0c000,color:#333
```

---

## 8. Trust boundaries and data flow (security §13)

```mermaid
flowchart LR
    subgraph Untrusted
        TA["tool arguments\n(agent)"]
        HI["hook stdin\n(host)"]
        RF["repo file contents"]
    end

    subgraph Boundary["Validation boundary"]
        V1["schema validate\nreject unknown fields\nlength caps"]
        V2["resolve + is_relative_to(repo_root)\nreject symlink escape"]
        V3["secret-file denylist\nURL userinfo redaction\nexcerpt cap + control-char strip"]
        V4["argv-only rg\nshell=False"]
    end

    subgraph Trusted
        ENG["engine (pure)"]
        KBt["bundled KB"]
    end

    OUT["outputs:\nstructuredContent · additionalContext · stderr logs"]

    TA --> V1 --> V2 --> ENG
    HI --> V1
    RF --> V3 --> ENG
    ENG --> V4
    ENG --> KBt
    ENG --> OUT
```

---

## 9. Delivery phases

```mermaid
flowchart LR
    P1["1 Foundation\nscaffold · CI · empty server"] --> P2["2 Discover + search\nrg · scoring · cache"]
    P2 --> P3["3 IR + rules\nEZR001–004, 010"]
    P3 --> P4["4 Remaining rules\nEZR020–050 · command parser"]
    P4 --> P5["5 Hook pack\nshim · hosts · gate cache · benchmark"]
    P5 --> P6["6 Architecture tool\nquestions · planner · mermaid"]
    P6 --> P7["7 Conversion tool\ndetectors · guard · delegation"]
    P7 --> P8["8 Hardening + release\ndocs · doctor · init · PyPI"]
```
