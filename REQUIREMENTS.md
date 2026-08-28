# Requirements — Crypto Attribution Engine

> Thesis-scope specification. No blockchain engine is implemented in Phase 0; this document defines what the system must do when built.

---

## 1. Overview

The system helps an investigator start from a suspect/unhosted wallet address, trace fund flows across a bounded number of hops, attribute intermediate addresses to entity categories, score risk and attribution confidence, visualize the graph, and export an auditable report plus a SAHYOG-compatible payload.

---

## 2. Definitions

- **Seed address**: The investigator-supplied starting address (suspect/unhosted wallet).
- **Hop**: One transaction edge from a source address to a destination address.
- **Entity**: A real-world actor or service category associated with one or more addresses (e.g., VASP/exchange, mixer, bridge, swap service, unknown/unhosted).
- **VASP**: Virtual Asset Service Provider (FATF terminology; includes exchanges and custodial wallet providers).
- **Attribution**: Evidence-based probable linkage of an address to an entity category, with a confidence score — not a claim of legal ownership.
- **Investigation / Case**: A container tying a seed, chain, parameters, traces, notes, and exports together.

---

## 3. Functional Requirements

### 3.1 Inputs

| ID | Requirement |
|---|---|
| FR-IN-01 | Accept a seed address, blockchain selector, and optional case metadata (case ID, investigator notes, date range). |
| FR-IN-02 | Validate address format per chain before any network call; reject malformed input with a clear error. |
| FR-IN-03 | Allow configurable traversal parameters per investigation: max hops, time window, minimum value threshold, direction (forward; backward as optional extension). |
| FR-IN-04 | Support manual entity-tag overrides by the investigator (with audit log of who/when). |

### 3.2 Supported Blockchains (Thesis Scope)

| ID | Requirement |
|---|---|
| FR-CHAIN-01 | MVP must support at least **one UTXO chain** (e.g., Bitcoin) **and one account-based chain** (e.g., Ethereum) to demonstrate both models. Additional EVM-compatible chains may be added as adapters without changing the core pipeline. |
| FR-CHAIN-02 | Chain support is adapter-based: each chain has an isolated ingestion/normalization module. Adding a chain does not require changes to traversal, attribution, or scoring logic. |
| FR-CHAIN-03 | Token transfers (e.g., ERC-20) on account-based chains are in scope as a follow-on after native-asset tracing is stable. |

> No specific third-party API is mandated here. Adapters will target publicly documented blockchain data APIs; the exact provider is selected in Phase 1 and documented in `backend/app/services/ingestion/`.

### 3.3 Data Requirements

| ID | Requirement |
|---|---|
| FR-DATA-01 | Normalize all chain data into a common transaction model (tx hash, block height/time, inputs/outputs or from/to, value, fee, chain ID). |
| FR-DATA-02 | Persist raw and normalized data with provenance: source API, fetch timestamp, and request parameters. |
| FR-DATA-03 | Maintain entity/tag data separately from chain data; tags are versioned and source-attributed (e.g., public VASP address lists, investigator-curated). No tag is treated as authoritative ownership proof. |
| FR-DATA-04 | Synthetic fixtures used for testing must be labeled as synthetic and contain no real PII or private keys. |

### 3.4 Traversal & Graph

| ID | Requirement |
|---|---|
| FR-TRAV-01 | Perform bounded graph traversal from the seed address respecting hop limit, time window, and value threshold. |
| FR-TRAV-02 | Support both BFS (breadth-first) and configurable traversal strategies; default is BFS forward. |
| FR-TRAV-03 | Handle UTXO change-address heuristics transparently and document their limitations (they are probabilistic, not deterministic). |
| FR-TRAV-04 | Detect and flag potential loop/cycle paths to avoid infinite expansion. |
| FR-TRAV-05 | Produce a directed transaction graph consumable by the API and frontend (nodes = addresses/entities, edges = transactions). |

### 3.5 Entity Attribution

| ID | Requirement |
|---|---|
| FR-ATTR-01 | Map addresses to entity categories: `unhosted/unknown`, `VASP/exchange`, `mixer`, `bridge`, `swap service`, and extensible others. |
| FR-ATTR-02 | Match against a curated set of known VASP addresses/clusters where available; every match must record source and match type (exact address vs. cluster heuristic). |
| FR-ATTR-03 | Attribution outputs must include evidence references (tx hashes, block times, matched tag source) — see ATTRIBUTION.md. |
| FR-ATTR-04 | Attribution is probabilistic; the system must not present attribution as definitive ownership. |

### 3.6 Risk & Confidence Scoring

| ID | Requirement |
|---|---|
| FR-SCORE-01 | Compute an **attribution confidence score** per entity linkage and per path (methodology in ATTRIBUTION.md). |
| FR-SCORE-02 | Compute a **risk score** per path/address reflecting exposure to high-risk categories (e.g., mixer, sanctioned/high-risk VASP). |
| FR-SCORE-03 | Scores are explainable: the contributing factors are stored and surfaced in the UI and report. |

### 3.7 Investigator Features (Dashboard)

| ID | Requirement |
|---|---|
| FR-INV-01 | Create, list, and manage investigations/cases. |
| FR-INV-02 | Configure and re-run a trace with different parameters; results are versioned per run. |
| FR-INV-03 | Interactive graph visualization (pan/zoom, select node/edge, view evidence drawer). |
| FR-INV-04 | Filter and highlight by entity category, risk level, hop depth, and time range. |
| FR-INV-05 | Add investigator notes/annotations per node, edge, or investigation. |
| FR-INV-06 | Role-aware access (at minimum: investigator and reviewer roles planned; enforcement deferred to API phase). |

### 3.8 Outputs & Reporting

| ID | Requirement |
|---|---|
| FR-REP-01 | Generate an investigation report containing: case metadata, seed and parameters, graph summary, per-path attribution with confidence and evidence, risk summary, limitations/disclaimers, and generation timestamp. |
| FR-REP-02 | Report available as **PDF** (human-readable) and **JSON** (machine-readable) with identical semantic content. |
| FR-REP-03 | Generate a **SAHYOG-compatible JSON payload** aligned to the portal's expected schema (field mapping documented in Phase 8; no live portal call in thesis scope unless a test endpoint is provided). |
| FR-REP-04 | Every export is reproducible: the report records the data snapshot identifiers and scoring version used. |

---

## 4. Non-Functional Requirements

| ID | Requirement | Target / Note |
|---|---|---|
| NFR-PERF-01 | Trace latency | Bounded traces (e.g., 3 hops, 100 edges) should complete within seconds on thesis-scale data, excluding external API wait time. Bulk expansion is rate-limited and paginated. |
| NFR-PERF-02 | API responsiveness | P95 < 500 ms for cached reads; ingestion-bound endpoints may be async (job + polling). |
| NFR-SCALE-01 | Data volume | Thesis scope targets thousands of transactions per investigation, not full-chain indexing. |
| NFR-REL-01 | Idempotent ingestion | Re-fetching the same tx hash does not duplicate records. |
| NFR-REL-02 | Provenance | Every derived fact (attribution, score) links back to source tx hashes and tag versions. |
| NFR-USE-01 | Usability | An investigator can run a first trace and view the graph without reading code. |
| NFR-MAIN-01 | Modularity | Chain adapters, attribution rules, and scoring weights are isolated and replaceable. |
| NFR-SEC-01 | Secrets | No API keys or credentials in code or docs. Use environment variables. |
| NFR-SEC-02 | PII | No real personal data in fixtures or committed data. Case data is treated as sensitive. |
| NFR-COMPAT-01 | Browser | Latest Chrome/Firefox/Edge for the dashboard. |
| NFR-TEST-01 | Testability | Core logic (traversal, attribution, scoring) has unit tests with synthetic fixtures. |

---

## 5. Inputs & Outputs Summary

### Inputs

- Seed address + chain selector (required).
- Case metadata: case ID, investigator name/ID, notes (optional, stored per investigation).
- Traversal parameters: max hops, time window, min value, direction.
- Entity/tag sources: curated address lists, investigator overrides.

### Outputs

- Transaction graph (JSON for API/frontend; internal model for scoring).
- Per-address and per-path attribution with confidence + evidence bundle.
- Per-path and per-entity risk score with factor breakdown.
- Investigation report (PDF + JSON).
- SAHYOG-compatible payload (JSON).

---

## 6. Security Considerations

1. **Secrets management** — Blockchain API keys and DB credentials via environment variables; `.env` is gitignored. No keys in documentation or fixtures.
2. **Input validation** — Address format, chain, and numeric parameters validated server-side via Pydantic schemas; no raw query interpolation.
3. **Access control** — Planned role-based access (investigator, reviewer, admin). Even at thesis scale, investigations are not world-readable.
4. **Audit trail** — Record who created/modified investigations, overrides, and exports (user, timestamp).
5. **Data retention** — Thesis deployment is local/ephemeral; production retention and encryption-at-rest are noted as future work.
6. **Dependency hygiene** — Pin backend/frontend dependencies; run `pip audit` / `npm audit` before releases.
7. **Rate limiting & abuse** — Ingestion layer respects upstream rate limits with backoff; API layer applies per-user rate limiting in later phases.
8. **No private key handling** — The system never handles, stores, or requests private keys or seed phrases.

---

## 7. Constraints & Assumptions

- Blockchain data depends on third-party APIs; availability and rate limits are outside system control. The design uses caching and idempotent writes to mitigate this.
- Entity tags are incomplete by nature; absence of a tag does not imply an address is unhosted/safe.
- SAHYOG schema alignment will be based on the published/shared specification available during Phase 8; live portal integration requires credentials and access that are out of scope for this bootstrap.
- PostgreSQL is the initial store; a graph extension or dedicated graph DB may be introduced if traversal benchmarks justify it — such a change will be recorded as an ADR in `docs/`.

---

## 8. Acceptance Criteria (Thesis Demo)

- An investigator can create a case, submit a seed address and parameters, view a traversal graph with entity labels and confidence/risk scores, read the evidence for any attribution, and download a PDF report and SAHYOG-compatible JSON that match the on-screen results.
- All attribution statements in the UI and report carry a visible confidence level and disclaimer that attribution is probable, not definitive.
- No fake integrations, keys, or datasets are present; all external calls and tag sources are documented.

---

*This document is the contract for implementation phases. Changes require updating this file and, where architectural, ARCHITECTURE.md.*
