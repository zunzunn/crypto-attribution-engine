# Architecture — Crypto Attribution Engine

> **As-built status: Phase 1 (backend foundation + Ethereum ingestion)**. This document is the living design contract; sections marked *Phase 1 (implemented)* describe code that exists in the repository, the rest describe planned components.

---

## 1. Architectural Goals

- **Evidence-first**: every derived fact (attribution, score) links to source transactions and tag versions.
- **Adapter isolation**: chain specifics do not leak into traversal, attribution, or scoring.
- **Thesis-realistic**: PostgreSQL-first, single-deployment, no full-chain indexing; graph store introduced only if benchmarks justify it.
- **Reproducibility**: a report can be re-derived from its recorded snapshot + code version.

---

## 2. High-Level Data Flow

```
                         +-------------------+
                         |  Blockchain APIs  |
                         | (per-chain, e.g. |
                         |  Bitcoin, Ethereum|
                         |  + future EVM)    |
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         |  Ingestion Layer  |  adapters + normalization
                         |  (Python async)   |  provenance + idempotent writes
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         |   PostgreSQL      |  addresses, transactions,
                         |   (primary store) |  entities/tags, investigations,
                         |                   |  traces, evidence bundles
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         | Transaction Graph |  directed graph built from
                         |  Construction     |  persisted edges
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         | Traversal Engine  |  BFS/DFS with hop/time/value
                         | (bounded)         |  constraints, cycle handling
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         | Entity Attribution|  VASP/mixer/bridge/swap matching
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         |  Risk & Confidence|  explainable scoring
                         |     Scoring       |
                         +--------+----------+
                                  |
                                  v
                         +--------+----------+
                         |  FastAPI Backend  |  REST API, auth, jobs
                         +--------+----------+
                                  |
                       +----------+----------+
                       |                     |
                       v                     v
              +--------+--------+   +--------+--------+
              | React Dashboard |   | Reporting &     |
              | (Cytoscape.js)  |   | SAHYOG Export   |
              |  graph + evidence|  | PDF + JSON      |
              +-----------------+   +-----------------+
```

---

## 3. Components

### 3.1 Blockchain APIs (External)

- One adapter per chain under `backend/app/services/ingestion/`.
- **Phase 1 (implemented)** — Ethereum via the Etherscan V2 endpoint
  (`https://api.etherscan.io/v2/api`, `chainid`-parameterized, API key via env).
  `EtherscanClient` handles pagination (`page`/`offset` with `page_size` and
  `max_pages` guards), rate-limit detection, and typed provider errors.
- Each future adapter exposes the `ChainAdapter` protocol:
  `get_normalized_transactions(address) -> list[Transaction]`, isolating all
  chain/provider specifics behind a single interface.
- No chain logic outside the adapter. Provider selection for Ethereum is
  Etherscan (publicly documented REST API); other chains select providers in
  their own phases.

### 3.2 Ingestion Layer *(Phase 1 — implemented)*

**Responsibilities**

- API boundaries validate chain + address via `app.utils.addresses`
  (regex-based Ethereum validation, lowercase normalization; EIP-55 checksum
  validation is a documented future enhancement).
- `IngestionRegistry` maps a chain id → adapter. Only `ethereum` is registered.
- `EthereumAdapter` fetches native (ETH) `txlist` records, then
  `ethereum_normalizer` converts each raw record into the canonical model:

  ```
  Transaction (canonical, blockchain-agnostic)
    chain_id, network, tx_hash, block_number, block_hash, block_timestamp,
    status, transaction_type, from_address, to_address,
    value (str, base units), value_decimals, fee, input_data,
    senders[], recipients[], token_transfers[],
    source, fetched_at
  ```
- `IngestionService` orchestrates: validate → create `ingestion_runs` audit
  row → adapter fetch+normalize → `TransactionRepository.upsert_many`
  (idempotent) → close the run with inserted/skipped counts.
- Idempotency: `transactions` has a unique key `(chain_id, network, tx_hash)`;
  re-ingesting an address inserts only missing hashes and records a fresh,
  auditable ingestion run.
- Token transfers (`tokentx`, ERC-20) are modeled (schema + `token_transfers`
  table) but not yet fetched — a documented Phase 1 follow-on.

**Modules**: `backend/app/services/ingestion/`, `backend/app/schemas/`,
`backend/app/repositories/`, `backend/app/services/ingestion_service.py`.

### 3.3 PostgreSQL — Primary Store *(Phase 1 — implemented)*

**Why PostgreSQL initially**

- Sufficient for thesis-scale (thousands of edges per investigation).
- Relational integrity for investigations, users, and audit logs.
- `ltree` / recursive CTEs can handle bounded traversals without a dedicated graph DB. A graph extension (e.g., Apache AGE) or external graph store is an optional later step, gated on benchmarks.

**Implemented tables (Alembic `0001_initial`; async via asyncpg)**

| Table | Purpose |
|---|---|
| `transactions` | Canonical tx model (JSON `senders`/`recipients`), unique `(chain_id, network, tx_hash)` idempotency key, address and time indexes |
| `token_transfers` | ERC-20-style transfers (schema in place; ingestion is a follow-on) |
| `ingestion_runs` | Audit trail per address ingestion: status + inserted/skipped counts |

**Planned tables (later phases)**

| Table | Purpose |
|---|---|
| `investigations` | Case container: seed address, chain, params, status, owner |
| `addresses` | Normalized address + chain, first/last seen, derived entity pointer |
| `transaction_edges` | Directed edges derived from transactions (one row per address→address transfer) |
| `entities` | Entity catalog: category, name, risk tier, tag source/version |
| `address_entity_map` | Address → entity attribution with confidence + evidence bundle |
| `traces` / `trace_runs` | Traversal run metadata, parameters, snapshot IDs (Phase 3) |
| `reports` | Generated artifacts + payload hashes (Phase 8) |

Data access uses a small repository layer (`app/repositories/`): async
sessions, `AsyncSessionFactory` owning engine + maker, no raw SQL outside
migrations/health probe.

### 3.4 Transaction Graph Construction

- Built on demand from `transaction_edges` for a given investigation/trace run.
- In-memory directed graph (e.g., `networkx.DiGraph` or lightweight adjacency structure) for traversal; persisted edges remain the source of truth.
- Nodes carry: address, entity category (if attributed), risk level. Edges carry: tx hash, value, block time, hop depth.

### 3.5 Traversal Engine

- **Default**: BFS forward from seed address.
- **Constraints** (all configurable per trace run):
  - `max_hops` — hard cutoff (e.g., 3–6 for thesis demos).
  - `time_window` — only edges within `[seed_tx_time, seed_tx_time + window]` or an explicit date range.
  - `min_value` / `value_propagation` — ignore dust; optionally require value continuity within a tolerance.
  - `max_edges_per_hop` — cap fan-out to avoid explosion.
- **Cycle handling**: visited-set per path + global visited for BFS frontier; cycles flagged, not re-expanded infinitely.
- **UTXO specifics**: change-address heuristics are optional, clearly labeled as probabilistic, and never silently merge addresses.
- **Output**: ordered paths (list of edges) with per-hop metadata, plus the merged graph for visualization.

**Module**: `backend/app/services/traversal/`.

### 3.6 Entity Attribution

- Input: addresses encountered during traversal.
- Matching layers (in order):
  1. **Exact address match** against curated VASP/mixer/bridge address lists (highest signal).
  2. **Cluster heuristic** (e.g., co-spend clustering on UTXO chains) — lower confidence, explicitly marked as heuristic.
  3. **Behavioral tag** (e.g., known bridge contract address, mixer interaction pattern) — category-level attribution.
  4. **Unknown/unhosted** — default when no tag matches.
- Every attribution records: `entity_id`, `match_type`, `tag_source`, `tag_version`, `evidence_tx_hashes`.

Detailed methodology in [ATTRIBUTION.md](ATTRIBUTION.md).

**Module**: `backend/app/services/attribution/`.

### 3.7 Risk & Confidence Scoring

- **Confidence** — likelihood that an address→entity linkage is correct, given match type, tag freshness, corroborating evidence, and hop distance.
- **Risk** — exposure of a path/address to high-risk categories (mixer, high-risk VASP, rapid cross-chain hop).
- Both scores are explainable: factor breakdowns are persisted and returned by the API.

See [ATTRIBUTION.md](ATTRIBUTION.md) for the scoring model.

**Module**: `backend/app/services/scoring/`.

### 3.8 FastAPI Backend *(Phase 1 — implemented)*

**Responsibilities**

- REST API for ingestion, investigations, traces, entities, and reports.
- Authentication/authorization (planned: JWT or session; roles: investigator, reviewer, admin).
- Async job handling for ingestion/trace runs (create job → poll status → fetch result).
- Input validation (Pydantic), error mapping, rate limiting, and audit logging.

**Implemented routes**

```
GET    /health                    — liveness + DB readiness
POST   /api/v1/ingest/{chain}/{address}  — fetch -> normalize -> idempotent persist
GET    /api/v1/ingest/{chain}/{address}  — list persisted txs for an address
GET    /api/v1/ingestion-runs/{id}       — audit record for an ingest run
GET    /api/v1/transactions/{tx_hash}    — fetch one canonical tx (address-aware chain)
```

**Planned route groups (later phases)**

```
/api/v1/investigations   — CRUD + list
/api/v1/traces           — create/run, status, results (graph + paths + scores)
/api/v1/entities         — lookup, tag management (curated)
/api/v1/reports          — generate PDF/JSON, SAHYOG payload, download
```

**Implementation notes**

- `app.main.create_app` is a factory (settings + `AsyncSessionFactory` + registry
  are injected), so the app runs with `uvicorn app.main:create_app --factory`.
- DB errors map to 5xx, validation/config failures to clean 4xx/5xx with JSON detail.
- CORS middleware is config-driven (`CORS_ORIGINS`).

**Module**: `backend/app/api/` + `backend/app/core/` (config, security, logging).

### 3.9 React Dashboard

- **Stack**: React + TypeScript + Vite, state via React Query or similar for API caching.
- **Key views**:
  - Case list / case detail.
  - Trace configuration form (seed, chain, hop/time/value params).
  - Graph view (Cytoscape.js): pan/zoom, node/edge selection, category coloring, hop-depth layering.
  - Evidence drawer: per-selection tx list, attribution reason, confidence/risk breakdown.
  - Report/export panel: download PDF/JSON, copy SAHYOG payload.
- **Cytoscape.js**: retained unless a strong reason emerges (e.g., need for WebGL at >10k nodes, which is outside thesis scope). Layouts: `breadthfirst` or `dagre` for hop-layered display.

**Module**: `frontend/src/`.

### 3.10 Reporting & SAHYOG Integration

- **PDF/JSON report**: server-side generation (e.g., WeasyPrint or ReportLab for PDF; Pydantic serialization for JSON). Content defined in REQUIREMENTS.md §3.8.
- **SAHYOG-compatible payload**: JSON mapping of investigation findings to the portal's expected schema. Phase 8 produces the mapper and a validator; live submission requires portal credentials and is out of scope for the bootstrap. The payload structure and field mapping will be documented in `docs/sahyog-mapping.md` when the schema is available.

**Module**: `backend/app/services/reporting/`.

---

## 4. Cross-Cutting Concerns

### 4.1 Configuration *(Phase 1 — implemented)*

- `backend/app/core/config.py` (Pydantic Settings) — DB URLs, Etherscan API key/base URL/chain id/timeout/pagination, CORS origins, log level, DB auto-create. All secrets via environment variables; `.env` is gitignored. See `backend/.env.example` for the full surface.

### 4.2 Security

- Input validation at the API boundary (Pydantic).
- SQL via ORM / parameterized queries only.
- No private key handling anywhere.
- API keys live in env only; never logged.
- Audit log for investigation mutations and exports.

### 4.3 Observability

- Structured logging (JSON) with correlation IDs per request/job.
- Health endpoint; metrics endpoint as optional follow-on.

### 4.4 Testing Strategy *(Phase 1 — implemented)*

- Pytest suite in `backend/tests/` — 59 tests covering normalizers, client (stubbed HTTP), address validation, canonical schema, repositories/idempotency, config, and API routes.
- Runs against a real PostgreSQL test database (`TEST_DATABASE_URL`) or a SQLite in-memory fallback when unset; both green.
- Ruff linting clean.
- Profiling/attribution/scoring tests are deferred to their phases.

---

## 5. Deployment (Thesis Scope)

- **Local development (working today)**: `uvicorn app.main:create_app --factory`
  for the API (see Makefile), local PostgreSQL. A `compose.yaml` + Postgres init
  script are included for optional Docker local orchestration.
- **No production deployment** in the bootstrap.

---

## 6. Evolution & Decision Records

- Stack changes (e.g., introducing a graph extension or switching visualization libraries) require a short ADR in `docs/adr-*.md` with rationale, alternatives, and trade-offs.
- SAHYOG schema mapping will be versioned alongside the payload generator.

---

*Next: ATTRIBUTION.md for the formal methodology and ROADMAP.md for the phase plan.*
