# Roadmap — Crypto Attribution Engine

> Phased plan from bootstrap to thesis demo. Each phase has clear entry criteria, deliverables, and exit criteria. No phase should introduce fake keys, datasets, or unsupported claims.

---

## Phase 0 — Documentation & Repository Bootstrap

**Status: In progress (this commit)**

| Item | Detail |
|---|---|
| Goal | Clean repo structure, scaffolding, and design contracts before any application code. |
| Deliverables | `README.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `ATTRIBUTION.md`, `ROADMAP.md`, `.gitignore`, directory scaffolding (`backend/`, `frontend/`, `data/`, `docs/`, `scripts/`). |
| Exit criteria | All five Markdown files reviewed; directories created; no application logic committed; `.gitignore` covers secrets and local data. |

---

## Phase 1 — Data Ingestion

**Status: Not started — do not begin until explicitly requested.**

| Item | Detail |
|---|---|
| Goal | Fetch and normalize blockchain data per chain via isolated adapters. |
| Tasks | 1. Define canonical `Transaction` / `TransactionEdge` schemas (Pydantic). 2. Implement chain adapters (Bitcoin + Ethereum for MVP) with pagination, retries, rate-limit handling. 3. Provenance tracking (`source`, `fetched_at`, `request_params`). 4. Idempotent persistence to PostgreSQL. 5. Address format validation per chain. 6. Local Docker Compose for PostgreSQL. |
| Deliverables | `backend/app/services/ingestion/` adapters, schemas, Alembic migrations for `addresses`/`transactions`/`transaction_edges`, `docker-compose.yml`, synthetic fixtures in `data/fixtures/`. |
| Exit criteria | Given a valid seed address, the system fetches, normalizes, and persists transactions idempotently; malformed input is rejected with a clear error; no secrets in code. |

---

## Phase 2 — Database & Graph Construction

| Item | Detail |
|---|---|
| Goal | Solidify the storage model and build the in-memory transaction graph. |
| Tasks | 1. Finalize tables: `investigations`, `addresses`, `transactions`, `transaction_edges`, `entities`, `address_entity_map`, `trace_runs`. 2. Indexes on `(chain_id, address)`, `tx_hash`, `block_time`. 3. Graph builder that materializes a directed graph from `transaction_edges` for a given investigation/trace run. |
| Deliverables | Updated migrations, graph construction service (`backend/app/services/graph/`), unit tests with fixtures. |
| Exit criteria | A persisted set of transactions can be materialized as a correct directed graph (nodes/edges) with hop metadata; tests cover UTXO multi-output and account-based cases. |

---

## Phase 3 — Traversal Engine

| Item | Detail |
|---|---|
| Goal | Bounded, explainable fund-flow traversal from a seed address. |
| Tasks | 1. BFS forward traversal with constraints: `max_hops`, `time_window`, `min_value`/`value_tolerance`, `max_edges_per_hop`, `max_total_edges`. 2. Cycle detection and pruning-reason logging. 3. UTXO change-heuristic handling (opt-in, labeled `heuristic`). 4. Deterministic output ordering. |
| Deliverables | `backend/app/services/traversal/` with configurable parameters, path + graph outputs, pruning diagnostics. |
| Exit criteria | Traversal respects all constraints, handles cycles without infinite expansion, records pruning reasons, and produces reproducible paths for the same snapshot/params. |

---

## Phase 4 — Entity Attribution

| Item | Detail |
|---|---|
| Goal | Map traversed addresses to entity categories with evidence bundles. |
| Tasks | 1. Entity catalog and `address_entity_map` with versioned tag sources. 2. Matching layers: exact address → cluster heuristic → contract/behavioral → unknown. 3. Evidence bundle per attribution (tag source/version, evidence tx hashes). 4. Investigator manual overrides with audit log. |
| Deliverables | `backend/app/services/attribution/`, tag import tooling, evidence bundle model. |
| Exit criteria | Known VASP/mixer/bridge addresses are correctly categorized with evidence; unknown addresses default to `unknown`/`unhosted`; overrides are audit-logged; every attribution carries its evidence bundle. |

---

## Phase 5 — Risk & Confidence Scoring

| Item | Detail |
|---|---|
| Goal | Explainable confidence and risk scores per attribution and per path. |
| Tasks | 1. Implement scoring model v0 per ATTRIBUTION.md (base scores + adjustments, path aggregation). 2. Persist scoring version and factor breakdowns. 3. Tier mapping and calibration against synthetic fixtures. |
| Deliverables | `backend/app/services/scoring/`, versioned scoring config, breakdown output for API/UI/report. |
| Exit criteria | Scores are deterministic, bounded `[0,1]`, explainable (factor breakdown), and match the methodology in ATTRIBUTION.md; changing weights bumps the model version. |

---

## Phase 6 — FastAPI Backend

| Item | Detail |
|---|---|
| Goal | Expose investigations, traces, entities, and reports via a typed REST API. |
| Tasks | 1. FastAPI app factory, Pydantic schemas, route groups (`/api/v1/investigations`, `/traces`, `/entities`, `/reports`, `/health`). 2. Config via `core/config.py` (env-based). 3. Async job handling for ingestion/trace runs (create → poll → result). 4. Auth scaffolding (JWT/session, roles: investigator/reviewer). 5. Validation, error mapping, rate limiting, audit logging. |
| Deliverables | `backend/app/api/`, `backend/app/core/`, OpenAPI docs at `/docs`, integration tests. |
| Exit criteria | An investigator can drive the full flow via API (create case → run trace → fetch graph/scores → request report); OpenAPI spec is accurate; no private key handling. |

---

## Phase 7 — React Dashboard

| Item | Detail |
|---|---|
| Goal | Investigator-facing UI with interactive graph and evidence review. |
| Tasks | 1. Vite + React + TypeScript setup. 2. Case list/detail, trace config form. 3. Cytoscape.js graph (pan/zoom, selection, category coloring, hop layering). 4. Evidence drawer + score breakdowns. 5. Filter/highlight (category, risk, hop, time). 6. Report/export panel. |
| Deliverables | `frontend/src/` pages/components/services/hooks, API client, component tests. |
| Exit criteria | An investigator can complete a trace and review the graph/evidence without reading code; graph interactions and filters work on thesis-scale data; no fake data in the UI. |

---

## Phase 8 — Reporting & SAHYOG Integration

| Item | Detail |
|---|---|
| Goal | Reproducible, auditable exports and SAHYOG-compatible payload. |
| Tasks | 1. PDF + JSON report generation (case metadata, params, graph summary, per-path attribution with confidence/evidence, risk summary, limitations, snapshot/scoring versions). 2. SAHYOG-compatible JSON mapper + validator (schema aligned to the published/shared spec available at build time). 3. Field mapping documented in `docs/sahyog-mapping.md`. |
| Deliverables | `backend/app/services/reporting/`, report templates, SAHYOG mapper/validator, mapping doc. |
| Exit criteria | PDF and JSON reports have identical semantic content and include limitations/disclaimers; SAHYOG payload validates against the documented schema; every export records its snapshot/scoring versions. Live portal submission is out of scope unless a test endpoint is provided. |

---

## Phase 9 — Testing, Hardening & Thesis Polish

| Item | Detail |
|---|---|
| Goal | Make the system defensible for thesis evaluation. |
| Tasks | 1. Unit tests for traversal/attribution/scoring with synthetic fixtures. 2. API integration tests (test DB). 3. Frontend component tests. 4. End-to-end demo script (seed → trace → graph → report). 5. Dependency audits (`pip audit`, `npm audit`), error handling, logging polish. 6. README/docs final pass, limitations clearly stated. |
| Deliverables | Test suites, CI config (optional), demo script, final documentation pass. |
| Exit criteria | Core logic has meaningful test coverage; demo runs end-to-end on synthetic + small real-world-derived (non-PII) examples; all docs reflect the as-built system; no fake integrations or unsupported claims. |

---

## Phase Sequencing & Dependencies

```
Phase 0 (done) → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9
                  ingestion   DB/graph  traversal  attribution  scoring   API    dashboard  reporting  hardening

Phases 2–5 are backend-logic heavy and can overlap lightly once Phase 1 schemas are stable.
Phase 7 (dashboard) starts once Phase 6 exposes the API contract (even if mocked).
Phase 8 depends on Phases 3–6 being stable.
```

---

## Milestones for Thesis Demos

| Milestone | Phases | Demo Capability |
|---|---|---|
| M1 — Data Foundation | 0–2 | Fetch and persist transactions; show normalized data. |
| M2 — Tracing | 0–3 | Trace from a seed with hop/time/value constraints; show paths. |
| M3 — Intelligence | 0–5 | Attributed paths with confidence + risk scores and evidence. |
| M4 — Investigator Workflow | 0–7 | Full UI flow: case → trace → graph → evidence review. |
| M5 — Reporting | 0–9 | Downloadable report + SAHYOG payload; reproducible, auditable. |

---

## General Rules (All Phases)

- One phase at a time unless explicitly requested to parallelize.
- No fake API keys, integrations, or datasets. Synthetic data is labeled as synthetic.
- Every attribution and score carries evidence and limitations — never present probable attribution as definitive ownership.
- Secrets via environment variables only; `.env` stays gitignored.
- Architectural changes get an ADR in `docs/`.

---

*This roadmap is the execution order. Do not start Phase 1 until explicitly requested.*
