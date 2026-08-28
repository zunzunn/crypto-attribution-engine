# Crypto Attribution Engine

> A thesis project for evidence-based cryptocurrency transaction tracing and entity attribution to support investigators.

**Status:** `Phase 2 — Graph, traversal & entity attribution` — Ethereum (Etherscan) ingestion, plus a deterministic traversal engine, entity registry, confidence scoring, and the `POST /api/v1/attribution/investigate` API are live with 132 passing tests. Risk scoring, dashboard, and reporting are not started. See [ROADMAP.md](ROADMAP.md).

---

## 1. Purpose

The Crypto Attribution Engine is an investigative support system that traces cryptocurrency fund flows originating from a suspect or unhosted wallet, identifies likely intermediary entities (exchanges/VASPs, mixers, bridges, swap services), and produces auditable, evidence-backed outputs for investigators.

It does **not** claim to prove wallet ownership. It provides **probable attribution** with explicit confidence levels and linked evidence — suitable for further investigation and lawful information requests.

Planned downstream outputs:

- Visual transaction graph with hop-by-hop evidence.
- Attribution and risk scores per path and per entity.
- Investigation-ready report (PDF/JSON).
- SAHYOG-compatible payload for inter-agency sharing (schema-aligned, not yet integrated with a live portal).

---

## 2. Problem Statement

Cryptocurrency investigations face recurring challenges:

1. **Pseudonymity** — Addresses are not directly tied to real-world identities; attribution requires corroborating evidence.
2. **High transaction volume and speed** — Manual tracing across hops does not scale.
3. **Obfuscation techniques** — Mixers, chain-hopping via bridges, and rapid swaps are used to break the trail.
4. **Fragmented tooling** — Investigators switch between block explorers, spreadsheets, and ad-hoc scripts; provenance and reproducibility suffer.
5. **Reporting gap** — Findings must be converted into a defensible, shareable report and — in the Indian LEA context — into a format compatible with the SAHYOG portal workflow.

This project addresses these gaps with a single, auditable pipeline from ingestion to reporting.

---

## 3. Goals

### Primary goals

- Trace fund flows forward (and optionally backward) from a seed address within bounded, explainable constraints.
- Attribute intermediary hops to entity categories with a transparent confidence score and evidence bundle.
- Surface risk signals (e.g., mixer interaction, high-risk VASP, rapid peel chains).
- Visualize paths as an interactive graph for investigative review.
- Export reproducible reports and a SAHYOG-compatible JSON payload.

### Non-goals (for this thesis scope)

- Real-time mempool monitoring or cross-border live enforcement integration.
- Custodial key management or transaction signing.
- Claiming definitive ownership of any address.
- Replacing legal process — the system supports, but does not substitute, lawful requests to VASPs/LEAs.

---

## 4. Planned Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend API | **Python 3.11+ + FastAPI** | Async-friendly, strong typing via Pydantic, good fit for data-heavy services. |
| Storage (initial) | **PostgreSQL 15+** | Relational core for transactions, addresses, entities, investigations. Sufficient for thesis scale; graph extensions or a dedicated graph store can be introduced later if traversal performance demands it. |
| Frontend | **React + TypeScript + Vite** | Modern, well-documented, large ecosystem. |
| Graph visualization | **Cytoscape.js** | Mature, supports directed graphs, layouts, and investigator-friendly interactions. Kept unless a strong technical reason emerges (e.g., WebGL scale needs). |
| Auth (planned) | JWT or session-based, role-gated | Investigator / reviewer roles. Exact choice deferred to API phase. |
| Reporting | PDF generation from backend (e.g., WeasyPrint/ReportLab) + JSON export | Deterministic, server-side rendering. |

> Stack may evolve with justification; changes will be documented in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 5. High-Level Workflow

```
Investigator input (seed address, chain, time/case context)
        |
        v
  Blockchain data ingestion (per-chain adapter -> normalized TX model)
        |
        v
  PostgreSQL persistence (addresses, transactions, entities, investigations)
        |
        v
  Transaction graph construction
        |
        v
  Traversal engine (BFS/DFS with hop, time, and value constraints)
        |
        v
  Entity attribution (VASP/mixer/bridge/swap tagging + matching)
        |
        v
  Risk & confidence scoring
        |
        v
  FastAPI backend (REST: investigations, traces, entities, reports)
        |
        v
  React dashboard (Cytoscape.js graph, evidence panel, case view)
        |
        v
  Reporting & SAHYOG-compatible export
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for component details and [ATTRIBUTION.md](ATTRIBUTION.md) for the scoring methodology.

---

## 6. Repository Structure

```
crypto_attribution_engine/
├── README.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── ATTRIBUTION.md
├── ROADMAP.md
├── compose.yaml             # optional local PostgreSQL (Docker)
├── docker/postgres/init/    # dev-only: creates crypto_attribution_test
├── Makefile
├── backend/                 # Python + FastAPI (Phase 1)
│   ├── .env.example         # documented placeholders; copy to .env
│   ├── requirements.txt / requirements-dev.txt
│   ├── pytest.ini
│   ├── alembic.ini / alembic/  # DB migrations (versions/0001_initial.py)
│   ├── app/
│   │   ├── main.py          # app factory
│   │   ├── api/routes/      # health, ingest, transactions endpoints
│   │   ├── core/            # settings (env-driven), logging, errors
│   │   ├── db/              # engine, session, declarative base
│   │   ├── models/          # transactions, token_transfers, ingestion_runs
│   │   ├── repositories/    # idempotent upserts + audit runs
│   │   ├── schemas/         # canonical transaction schema (chain-agnostic)
│   │   ├── services/ingestion/  # Etherscan client, normalizer, adapter, registry
│   │   └── utils/           # address validation, time helpers
│   └── tests/               # unit + API tests (pytest)
├── frontend/                # React scaffold (not started)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/        # API clients
│   │   ├── hooks/
│   │   └── utils/
│   └── public/
├── docs/                    # supplementary docs, diagrams, ADRs
├── data/
│   ├── raw/                 # ignored; local chain exports
│   ├── processed/           # ignored; derived datasets
│   └── fixtures/            # synthetic examples (no real PII)
└── scripts/                 # one-off maintenance scripts
```

---

## 7. Current Development Status

| Phase | Status |
|---|---|
| 0 — Documentation & repo bootstrap | **Completed** |
| 1 — Data ingestion (backend foundation) | **Completed** — Ethereum (Etherscan V2) adapter, canonical model, idempotent PostgreSQL persistence, `/health` + ingestion API. Token-transfer (`tokentx`) ingestion is a documented follow-on. |
| 2 — Database / graph construction | **Completed** — `GraphBuilder` derives a directed transaction graph from persisted rows; `DatabaseGraphExpander` loads outgoing edges (native + token evidence) on demand. |
| 3 — Traversal engine | **Completed** — deterministic bounded BFS (`TraversalEngine`): hop limits, time window, min value, per-hop/global edge caps, cycle & revisit handling, evidence-preserving paths. |
| 4 — Entity attribution | **Completed** — local `entities` / `entity_addresses` registry with exact-match lookup, `ConfidenceScorer` (probabilistic score + tier + factors), and `AttributionService` combining traversal + registry + scoring. |
| 5 — Risk scoring | Not started |
| 6 — API | Partial — Phase 1 base routes live plus `POST /api/v1/attribution/investigate`; auth/reporting endpoints in later phases |
| 7 — Dashboard | Not started |
| 8 — Reporting & SAHYOG export | Not started |
| 9 — Testing & hardening | Partial — unit + API tests for Phases 1–4 are in place (132 tests) |

**Working today:**

- `GET /health` — liveness + DB readiness probe.
- `POST /api/v1/ingest/{chain}/{address}` — fetch (Etherscan V2) → normalize → persist idempotently; returns an ingestion-run summary with inserted/skipped counts.
- `GET /api/v1/ingest/{chain}/{address}` — list persisted transactions for an address.
- `GET /api/v1/ingestion-runs/{id}` and `GET /api/v1/transactions/{hash}` — audit/query endpoints.
- `POST /api/v1/attribution/investigate` — traversal + entity attribution for a seed address; returns ranked candidates with confidence scores, hop-by-hop evidence, token-transfer evidence, and traversal stats. Supports `max_hops`, `min_value`, and a `time_from`/`time_to` window.
- Chain-agnostic canonical `Transaction` model, `transactions` / `token_transfers` / `ingestion_runs` tables, Alembic migrations `0001_initial` / `0002_entities`.

No Ethereum API key or committed secrets are bundled; Etherscan without a key returns a clear configuration error. Bitcoin / Tron / Polygon / Solana adapters are not started (Ethereum must be working first).

---

## 8. Getting Started (Repository Only — No Live Ingestion Yet)

Prerequisites: Python 3.11+, PostgreSQL 15+ running locally (or Docker; see
`compose.yaml`). Docker is optional.

```bash
# 1) Backend virtualenv + dependencies
make backend-install                      # or: python3 -m venv backend/.venv && \
                                          # backward compat: see Makefile

# 2) PostgreSQL
#   - Local Homebrew Postgres is already running for this setup; or:
#       docker compose up -d postgres     # if you use the Docker service
#   - Create databases (once):
#       createdb crypto_attribution
#       createdb crypto_attribution_test
#   - Or apply the Alembic migration instead (recommended once on dev DB):
#       make migrate-db                    # creates tables via alembic upgrade head

# 3) Configuration
cp backend/.env.example backend/.env       # then fill in ETHERSCAN_API_KEY
# DATABASE_URL and TEST_DATABASE_URL point at local profiles by default.

# 4) Run the API
make dev                                   # uvicorn on http://127.0.0.1:8000

# 5) Check it
curl http://127.0.0.1:8000/health          # {"status":"ok", ...}
curl http://127.0.0.1:8000/docs            # interactive OpenAPI
```

### Tests

```bash
# Against a real PostgreSQL test database (recommended)
TEST_DATABASE_URL=postgresql+asyncpg://<user>@localhost:5432/crypto_attribution_test \
  .venv/bin/pytest                          # from backend/

# Or SQLite fallback (no Postgres needed)
cd backend && .venv/bin/pytest
```

See `backend/.env.example` for the complete configuration surface.

---

## 9. Contributing & Thesis Notes

- Keep commits scoped to one ROADMAP phase at a time.
- No fake data, keys, or integrations should be committed. Synthetic fixtures must be clearly labeled as synthetic.
- All attribution outputs must carry confidence and evidence — see [ATTRIBUTION.md](ATTRIBUTION.md).
- Security and PII handling: see [REQUIREMENTS.md](REQUIREMENTS.md).

---

## 10. References

- SAHYOG portal — inter-agency coordination workflow for cybercrime investigations (payload alignment is planned; live portal integration is out of scope for the bootstrap).
- Relevant standards/concepts: FATF VASP definitions, UTXO vs. account-based models, chain-hopping via bridges.

---

*This README will be updated as each phase lands. For detailed specs, see REQUIREMENTS.md, ARCHITECTURE.md, ATTRIBUTION.md, and ROADMAP.md.*
