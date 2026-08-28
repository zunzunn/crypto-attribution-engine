# Crypto Attribution Engine

> A thesis project for evidence-based cryptocurrency transaction tracing and entity attribution to support investigators.

**Status:** `Phase 0 — Documentation & Repository Bootstrap` — No blockchain engine implemented yet. See [ROADMAP.md](ROADMAP.md).

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
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # config, security, logging
│   │   ├── services/     # ingestion, traversal, attribution, scoring, reporting
│   │   ├── models/       # SQLAlchemy / ORM models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── utils/        # helpers
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/     # API clients
│   │   ├── hooks/
│   │   └── utils/
│   └── public/
├── docs/                 # supplementary docs, diagrams, ADRs
├── data/
│   ├── raw/              # ignored; local chain exports
│   ├── processed/        # ignored; derived datasets
│   └── fixtures/         # small, synthetic examples (no real PII)
└── scripts/              # one-off maintenance scripts
```

---

## 7. Current Development Status

| Phase | Status |
|---|---|
| 0 — Documentation & repo bootstrap | **In progress (this commit)** |
| 1 — Data ingestion | Not started |
| 2 — Database / graph construction | Not started |
| 3 — Traversal engine | Not started |
| 4 — Entity attribution | Not started |
| 5 — Risk scoring | Not started |
| 6 — API | Not started |
| 7 — Dashboard | Not started |
| 8 — Reporting & SAHYOG export | Not started |
| 9 — Testing & hardening | Not started |

No blockchain API keys, datasets, or integrations are included in this bootstrap. Phase 1 will not begin until explicitly requested.

---

## 8. Getting Started (Bootstrap Only)

This repository currently contains **documentation and scaffolding only**.

```bash
# Clone
git clone <remote-url>
cd crypto_attribution_engine

# Backend (placeholder — no implementation yet)
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt  # to be added in Phase 1

# Frontend (placeholder)
cd frontend && npm install && npm run dev
```

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
