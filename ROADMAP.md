# Roadmap — Crypto Attribution Engine

> Phased plan from bootstrap to thesis demo. Each phase has clear entry criteria, deliverables, and exit criteria. No phase should introduce fake keys, datasets, or unsupported claims.

---

## Phase 0 — Documentation & Repository Bootstrap

**Status: Completed**

| Item | Detail |
|---|---|
| Goal | Clean repo structure, scaffolding, and design contracts before any application code. |
| Deliverables | `README.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `ATTRIBUTION.md`, `ROADMAP.md`, directory scaffolding (`backend/`, `frontend/`, `data/`, `docs/`, `scripts/`). |
| Exit criteria | All five Markdown files reviewed; directories created; `.gitignore` covers secrets and local data. |

---

## Phase 1 — Data Ingestion

**Status: Completed — backend foundation + Ethereum (Etherscan) ingestion live.**

**Delivered**

- Canonical chain-agnostic `Transaction` schema (Pydantic; `value` as base-unit string) + `TokenTransfer` / `AddressAmount` schemas.
- Chain adapter interface (`ChainAdapter` protocol) + `IngestionRegistry`; **Ethereum** adapter with Etherscan **V2** client (pagination, rate-limit handling, typed provider errors).
- Normalization layer (`ethereum_normalizer`) mapping raw `txlist` records → canonical transactions.
- Idempotent persistence to PostgreSQL via `TransactionRepository.upsert_many`; unique `(chain_id, network, tx_hash)`; `ingestion_runs` audit rows with inserted/skipped counts.
- Address validation per chain (`utils/addresses`).
- Alembic migration `0001_initial` (tables: `transactions`, `token_transfers`, `ingestion_runs`).
- FastAPI app factory (`create_app`) + routes: `/health`, `POST|GET /api/v1/ingest/{chain}/{address}`, `GET /api/v1/ingestion-runs/{id}`, `GET /api/v1/transactions/{tx_hash}`.
- Environment-driven config (`core/config.py`, `.env.example`), structured logging, CORS, `compose.yaml` + PG init script, `Makefile`.
- Test suite: 59 tests (normalizer, client-stubbed, validation, schema, repository/idempotency, config, API) — green on PostgreSQL and SQLite; ruff clean.

**Known follow-ons (deferred, explicitly scoped)**

- ERC-20 token transfers (`tokentx`): schema + `token_transfers` table exist; fetch not yet wired.
- EIP-55 checksum validation for Ethereum addresses.
- Bitcoin/UTXO adapter (required for FR-CHAIN-01 full compliance).

| Item | Detail |
|---|---|
| Prior exit criteria | Given a valid seed address, the system fetches, normalizes, and persists transactions idempotently; malformed input is rejected with a clear error; no secrets in code. — **Met** (verified live via Etherscan unauthenticated 502 path + stub-driven tests; a real key ends the flow end-to-end). |

---

## Phase 2 — Database & Graph Construction

**Status: Mostly complete.** `GraphBuilder` + `DatabaseGraphExpander` derive a directed account-based transaction graph (native edges + token-transfer evidence) directly from the persisted `transactions` table. UTXO multi-output construction is a follow-on.

| Item | Detail |
|---|---|
| Goal | Solidify the storage model and build the in-memory transaction graph. |
| Tasks | 1. Finalize tables: `investigations`, `addresses`, `transactions`, `transaction_edges`, `entities`, `address_entity_map`, `trace_runs`. 2. Indexes on `(chain_id, address)`, `tx_hash`, `block_time`. 3. Graph builder that materializes a directed graph from `transaction_edges` for a given investigation/trace run. |
| Deliverables | Updated migrations, graph construction service (`backend/app/services/graph/`), unit tests with fixtures. |
| Done | `transactions`/`token_transfers` graphs derived on demand (`app/services/graph/`); unit tests (`tests/unit/test_graph_expansion.py`). |
| Exit criteria | A persisted set of transactions can be materialized as a correct directed graph (nodes/edges) with hop metadata; tests cover UTXO multi-output and account-based cases. |

---

## Phase 3 — Traversal Engine

**Status: Complete.** Deterministic, bounded forward BFS with hop/time/min-value/per-hop/global caps, cycle & revisit handling, pruning diagnostics, and reproducible output — covered by `tests/unit/test_traversal_engine.py`. UTXO change-heuristic handling remains a documented opt-in follow-on.

| Item | Detail |
|---|---|
| Goal | Bounded, explainable fund-flow traversal from a seed address. |
| Tasks | 1. BFS forward traversal with constraints: `max_hops`, `time_window`, `min_value`/`value_tolerance`, `max_edges_per_hop`, `max_total_edges`. 2. Cycle detection and pruning-reason logging. 3. UTXO change-heuristic handling (opt-in, labeled `heuristic`). 4. Deterministic output ordering. |
| Deliverables | `backend/app/services/traversal/` with configurable parameters, path + graph outputs, pruning diagnostics. |
| Exit criteria | Traversal respects all constraints, handles cycles without infinite expansion, records pruning reasons, and produces reproducible paths for the same snapshot/params. |

---

## Phase 4 — Entity Attribution

**Status: Partial.** Registry (`entities` / `entity_addresses`, versioned tag sources) with exact-address matching and evidence bundles is live, plus the `ConfidenceScorer` (model v0). Cluster/contract-match layers and investigator override audit-logging are follow-ons.

| Item | Detail |
|---|---|
| Goal | Map traversed addresses to entity categories with evidence bundles. |
| Tasks | 1. Entity catalog and `address_entity_map` with versioned tag sources. 2. Matching layers: exact address → cluster heuristic → contract/behavioral → unknown. 3. Evidence bundle per attribution (tag source/version, evidence tx hashes). 4. Investigator manual overrides with audit log. |
| Deliverables | `backend/app/services/attribution/`, tag import tooling, evidence bundle model. |
| Done | `app/services/attribution/` (registry, scoring, service); migration `0002_entities`; tests (`tests/unit/test_entity_registry.py`, `test_confidence_scoring.py`, `test_attribution_service.py`). |
| Exit criteria | Known VASP/mixer/bridge addresses are correctly categorized with evidence; unknown addresses default to `unknown`/`unhosted`; overrides are audit-logged; every attribution carries its evidence bundle. |

---

## Phase 5 — Risk & Confidence Scoring

**Status: Partial.** Confidence scoring model v0 (base scores + factor adjustments + tier mapping) is implemented inside the attribution service and surfaced via the API. Path-aggregation/weighted scoring and separate behavior-based risk scores are follow-ons.

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
Phase 0 (done) → Phase 1 (done) → Phase 2 (done) → Phase 3 (done) → Phase 4 (partial) → Phase 5 (partial) → Phase 6 → Phase 7 → Phase 8 → Phase 9
                  ingestion   DB/graph  traversal  attribution  scoring   API    dashboard  reporting  hardening

Phases 2–5 are backend-logic heavy and can overlap lightly once Phase 1 schemas are stable.
Phase 7 (dashboard) starts once Phase 6 exposes the API contract (even if mocked).
Phase 8 depends on Phases 3–6 being stable.
```

---

## Milestones for Thesis Demos

| Milestone | Phases | Demo Capability |
|---|---|---|
| M1 — Data Foundation | 0–2 | **Live:** fetch and persist Ethereum transactions (native ETH) idempotently; visualize normalized data via `/docs` and API JSON. UTXO chain and token-transfer ingestion remain follow-ons. |
| M2 — Tracing | 0–3 | **Live (API):** trace from a seed with hop/time/value constraints via `POST /api/v1/attribution/investigate`; paths and traversal stats returned. |
| M3 — Intelligence | 0–5 | **Live (API):** attributed candidates ranked by confidence with evidence bundles. Cluster/contract matching, weighted path confidence, and behavior-based risk scores are follow-ons. |
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

*This roadmap is the execution order. Phases 0–3 are done; Phases 4–5 are partially done (see status notes above). Do not begin a later phase until the earlier one is explicitly requested.*
