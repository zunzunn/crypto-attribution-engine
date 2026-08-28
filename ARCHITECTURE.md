# Architecture — Crypto Attribution Engine

> Phase 0 blueprint. No implementation yet — this document is the build contract.

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

- One adapter per chain (e.g., `bitcoin.py`, `ethereum.py` under `backend/app/services/ingestion/`).
- Each adapter: `fetch_transactions(address, params) -> list[RawTx]`, `fetch_transaction(tx_hash) -> RawTx`, handling pagination, rate limits, and retries with exponential backoff.
- No chain logic outside the adapter. Provider selection is deferred to Phase 1; adapters target publicly documented REST APIs.

### 3.2 Ingestion Layer

**Responsibilities**

- Validate input (address format, chain, numeric bounds) via Pydantic schemas.
- Call the appropriate chain adapter.
- Normalize `RawTx` into a canonical `Transaction` model:

  ```
  Transaction { tx_hash, chain_id, block_height, block_time, fee,
                inputs: [{address, value}], outputs: [{address, value}]
                // account-based chains: from_address, to_address, value
              }
  ```
- Persist with provenance (`source`, `fetched_at`, `request_params`) and idempotent upserts on `tx_hash + chain_id`.
- Cache recent fetches to respect rate limits; background refresh is out of scope for MVP.

**Module**: `backend/app/services/ingestion/` + `backend/app/schemas/`.

### 3.3 PostgreSQL — Primary Store

**Why PostgreSQL initially**

- Sufficient for thesis-scale (thousands of edges per investigation).
- Relational integrity for investigations, users, and audit logs.
- `ltree` / recursive CTEs can handle bounded traversals without a dedicated graph DB. A graph extension (e.g., Apache AGE) or external graph store is an optional later step, gated on benchmarks.

**Core tables (planned)**

| Table | Purpose |
|---|---|
| `investigations` | Case container: seed address, chain, params, status, owner |
| `addresses` | Normalized address + chain, first/last seen, derived entity pointer |
| `transactions` | Canonical tx model + raw payload reference + provenance |
| `transaction_edges` | Directed edges derived from transactions (one row per address→address transfer) |
| `entities` | Entity catalog: category, name, risk tier, tag source/version |
| `address_entity_map` | Address → entity attribution with confidence + evidence bundle |
| `traces` / `trace_runs` | Traversal run metadata, parameters, snapshot IDs |
| `reports` | Generated artifacts + payload hashes |

Migrations via Alembic (planned).

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

### 3.8 FastAPI Backend

**Responsibilities**

- REST API for investigations, traces, entities, and reports.
- Authentication/authorization (planned: JWT or session; roles: investigator, reviewer, admin).
- Async job handling for ingestion/trace runs (create job → poll status → fetch result).
- Input validation (Pydantic), error mapping, rate limiting, and audit logging.

**Planned route groups**

```
/api/v1/investigations   — CRUD + list
/api/v1/traces           — create/run, status, results (graph + paths + scores)
/api/v1/entities         — lookup, tag management (curated)
/api/v1/reports          — generate PDF/JSON, SAHYOG payload, download
/api/v1/health           — liveness/readiness
```

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

### 4.1 Configuration

- `backend/app/core/config.py` (Pydantic Settings) — DB URL, API keys, scoring weights, hop defaults. All secrets via environment variables; `.env` is gitignored.

### 4.2 Security

- Input validation at the API boundary (Pydantic).
- SQL via ORM / parameterized queries only.
- No private key handling anywhere.
- Audit log for investigation mutations and exports.

### 4.3 Observability

- Structured logging (JSON) with correlation IDs per request/job.
- Health endpoint; metrics endpoint as optional follow-on.

### 4.4 Testing Strategy

- Unit tests for traversal, attribution, and scoring against synthetic fixtures (`data/fixtures/`).
- API integration tests with a test database.
- Frontend component tests for graph rendering and evidence drawer logic.

---

## 5. Deployment (Thesis Scope)

- **Local development**: `uvicorn` for FastAPI, `vite dev` for React, local PostgreSQL (Docker Compose planned in Phase 1).
- **No production deployment** in the bootstrap. A `docker-compose.yml` for local orchestration will be added when the first service is implemented.

---

## 6. Evolution & Decision Records

- Stack changes (e.g., introducing a graph extension or switching visualization libraries) require a short ADR in `docs/adr-*.md` with rationale, alternatives, and trade-offs.
- SAHYOG schema mapping will be versioned alongside the payload generator.

---

*Next: ATTRIBUTION.md for the formal methodology and ROADMAP.md for the phase plan.*
