# Attribution Methodology — Crypto Attribution Engine

> Formal description of the planned attribution approach. This is a **probable, evidence-based** methodology — it does not claim definitive wallet ownership.

---

## 1. Purpose & Disclaimer

Blockchain addresses are pseudonymous. Linking an address to a real-world entity (e.g., an exchange/VASP, mixer, bridge, or swap service) is inherently probabilistic and depends on the quality, freshness, and provenance of the available evidence.

**This system provides evidence-based probable attribution**: every attribution carries a confidence score, an evidence bundle, and a clear statement of limitations. Investigators must corroborate findings through lawful process (e.g., information requests to VASPs) before drawing legal conclusions. No output of this system should be presented as proof of ownership without independent corroboration.

---

## 2. Entity Taxonomy

| Category | Description | Examples (category-level, not exhaustive) |
|---|---|---|
| `unhosted` / `unknown` | No reliable tag; treated as self-custodied or unattributed by default | Fresh wallet, personal cold storage |
| `VASP` / `exchange` | Virtual Asset Service Provider holding custodial wallets | Centralized exchanges (tag source determines specific names) |
| `mixer` | Privacy-enhancing service that pools and redistributes funds | CoinJoin-style or custodial mixers |
| `bridge` | Cross-chain transfer service/contract | Lock-and-mint / burn-and-release bridges |
| `swap_service` | Instant swap / DEX aggregator | Non-custodial swap services, DEX routers |
| `other` | Extensible bucket for future categories | Gambling, merchant, etc. (added only with a defined tag source) |

Categories are extensible, but a new category is only introduced when it has a documented tag source and matching rule.

---

## 3. Wallet Traversal Model

### 3.1 Graph Model

- **Nodes**: addresses (plus derived entity labels when attributed).
- **Edges**: directed transfers — one edge per address→address movement within a transaction. For UTXO chains, a single transaction may produce multiple edges (one per input→output mapping under the chosen expansion strategy).
- **Paths**: ordered edge sequences originating from the seed address.

### 3.2 Traversal Strategy

- **Default**: breadth-first search (BFS) forward from the seed.
- **Direction**: forward only in MVP; backward (funding source) as an optional extension.
- **Bounded expansion**: traversal stops when all active frontiers exceed the configured limits (§3.3). This keeps results explainable and computationally tractable for thesis scale.

### 3.3 Constraints (Per Trace Run)

All constraints are explicit, stored with the trace run, and surfaced in the report.

| Constraint | Purpose | Typical Thesis Value |
|---|---|---|
| `max_hops` | Hard depth limit; prevents unbounded expansion | 3–6 |
| `time_window` | Only edges within `[t0, t0 + window]` or an explicit `[from, to]` range are followed | Case-dependent; e.g., 7–90 days |
| `min_value` | Ignore dust / irrelevant micro-transfers | Chain-specific dust threshold or investigator-set |
| `value_tolerance` | For UTXO chains, follow outputs whose value is within tolerance of the tracked amount (to handle fees/change) | e.g., ±5% or fixed fee allowance |
| `max_edges_per_hop` | Cap fan-out per hop to avoid explosion on high-degree nodes (e.g., exchange hot wallets) | e.g., 50–200 |
| `max_total_edges` | Global cap per trace run | e.g., 500–1000 |

When a constraint prunes a path, the pruning reason is recorded (e.g., `hop_limit`, `time_window_exceeded`, `value_below_threshold`, `fan_out_cap`).

### 3.4 UTXO-Specific Handling

- **No silent address clustering**: co-spend or change-address heuristics are not applied automatically. If used, they are opt-in, labeled as `heuristic`, and carry a confidence penalty.
- **Change detection**: if enabled, the system flags the likely change output per transaction but does not merge addresses without an explicit heuristic attribution.
- **All heuristics are documented** with their false-positive risks in the report's limitations section.

### 3.5 Cycle & Loop Handling

- A global `visited` set prevents re-expansion of already-traversed addresses at the same or shallower depth.
- Cycles are flagged in the output (`cycle_detected`) rather than expanded infinitely.

---

## 4. Entity Tagging & Matching

### 4.1 Tag Sources

- **Curated address lists**: versioned datasets of known VASP/mixer/bridge addresses with source attribution (e.g., public research datasets, investigator-curated lists). Each import records `source`, `version`, `imported_at`.
- **Contract addresses**: known bridge/swap router contracts per chain.
- **Investigator overrides**: manual tags applied per investigation, audit-logged with `user`, `timestamp`, `reason`.

Tag freshness matters: stale tags produce lower-confidence attributions.

### 4.2 Matching Layers

Matching is attempted in priority order. The first matching layer determines the primary attribution, but lower layers are still evaluated for corroboration.

| Priority | Match Type | Signal Strength | Confidence Effect |
|---|---|---|---|
| 1 | **Exact address match** | Strong — address appears verbatim in a curated list | Highest base confidence |
| 2 | **Cluster match (UTXO)** | Moderate — address belongs to a co-spend cluster containing a tagged address | Reduced; marked `heuristic` |
| 3 | **Contract / behavioral match** | Moderate — interaction with a known mixer/bridge/swap contract | Category-level; moderate |
| 4 | **No match** | None — defaults to `unknown` / `unhosted` | No attribution; context only |

A single address may match multiple tags (e.g., an exchange hot wallet that also routes through a bridge). All matches are preserved; the primary match is the highest-priority exact match.

### 4.3 Evidence Collection (Per Attribution)

Every address→entity attribution stores an **evidence bundle**:

```
EvidenceBundle {
  address: string,
  chain_id: string,
  entity: { category, name?, risk_tier? },
  match_type: "exact" | "cluster_heuristic" | "contract" | "manual_override",
  tag_source: string,            // e.g., "curated_vasp_list_v3"
  tag_version: string,
  evidence_tx_hashes: string[],  // txs that triggered or corroborate the match
  first_seen_at: datetime?,      // block time of earliest evidence tx
  attributed_at: datetime,
  attributed_by: "system" | user_id,
  notes?: string
}
```

The bundle is persisted, returned by the API, shown in the evidence drawer, and included in the report.

---

## 5. Confidence Scoring

### 5.1 Principles

- Confidence is a **probabilistic estimate of attribution correctness**, not a risk or suspicion score.
- Scores are **explainable**: the numeric score is always accompanied by its factor breakdown.
- Scores are **bounded** to `[0, 1]` and mapped to qualitative tiers for display.

### 5.2 Qualitative Tiers

| Tier | Range | Meaning |
|---|---|---|
| `high` | 0.75 – 1.00 | Strong corroboration (e.g., exact match + recent tag + corroborating txs) |
| `medium` | 0.45 – 0.74 | Moderate signal (e.g., exact match with older tag, or single-tx contract match) |
| `low` | 0.15 – 0.44 | Weak/heuristic signal (e.g., cluster heuristic alone) |
| `very_low` | 0.00 – 0.14 | No meaningful attribution signal; effectively `unknown` |

Thresholds are configurable and versioned with the scoring model.

### 5.3 Planned Scoring Model (v0)

A transparent, weighted-factor model is planned for the thesis. No machine-learning classifier is assumed for MVP; ML is an optional future extension.

**Base confidence by match type**

| Match Type | Base Score |
|---|---|
| `exact` (curated address) | 0.80 |
| `manual_override` | 0.85 (investigator-vouched, but still not ownership proof) |
| `contract` (known mixer/bridge router) | 0.60 |
| `cluster_heuristic` | 0.35 |
| `no_match` | 0.00 |

**Adjustments** (additive, clamped to `[0, 1]`):

| Factor | Adjustment | Rationale |
|---|---|---|
| Tag freshness | +0.05 if tag version < 30 days old; −0.10 if > 180 days | Stale tags are less reliable |
| Corroboration | +0.05 per additional distinct evidence tx (cap +0.10) | Multiple txs strengthen the signal |
| Hop distance | −0.03 per hop beyond the attributed hop (cap −0.15) | Attribution further from the seed is less directly tied to the case |
| Heuristic penalty | −0.15 if `cluster_heuristic` is the sole signal | Heuristics have known false positives |
| Investigator flag | ±0.10 for explicit investigator confirm/dispute | Human review modulates but does not override evidence |

**Example**

> An address matches a curated VASP address (`exact`, base 0.80), tag is 10 days old (+0.05), with 2 corroborating txs (+0.10), at hop 2 (−0.03) → `0.92` → tier `high`. Evidence bundle lists the 3 tx hashes and tag source `curated_vasp_list_v3`.

### 5.4 Path-Level Confidence

Path confidence is the **minimum** (weakest link) of hop-level attribution confidences along the path, optionally weighted by hop proximity to the seed. This conservative aggregation avoids overstating confidence when one hop is weakly attributed, even if others are strong.

---

## 6. Risk Scoring (Complementary to Confidence)

Risk scoring is separate from attribution confidence. It reflects **exposure to high-risk categories**, not the likelihood of correct attribution.

**Planned risk signals**

| Signal | Risk Contribution |
|---|---|
| Direct mixer interaction | High |
| Bridge/swap hop that breaks value continuity | Medium–High |
| Interaction with high-risk VASP (per tag metadata) | Medium–High |
| Rapid peel chain / structuring-like pattern | Medium |
| Interaction with low-risk / regulated VASP | Low |

Path risk is an aggregate (e.g., max or weighted sum) of per-hop risk contributions. Exact weights are configurable and documented per scoring version. Risk scores are also explainable with a factor breakdown.

---

## 7. Limitations & Disclaimers (Surfaced in Every Report)

The report and UI must surface these limitations verbatim or in clearly equivalent language:

1. Attribution is **probable, not definitive**; it does not prove wallet ownership or control.
2. Tag datasets are **incomplete and time-sensitive**; absence of a tag does not imply safety or non-involvement.
3. Heuristic methods (e.g., clustering, change detection) carry **known false-positive rates**.
4. Mixers and cross-chain bridges can **break deterministic tracing**; paths through such services are flagged with reduced confidence.
5. Findings require **independent corroboration** and lawful process before enforcement action.

---

## 8. Versioning & Reproducibility

- Scoring weights, tier thresholds, and tag dataset versions are **versioned** (e.g., `scoring_model_v0`, `curated_vasp_list_v3`).
- Every trace run and report records the scoring version and tag versions used.
- Re-running a trace with the same inputs and versions must produce the same scores (deterministic given the same data snapshot).

---

## 9. Future Extensions (Out of Scope for MVP)

- ML-based attribution classifiers (requires labeled training data and evaluation framework).
- Cross-chain value correlation after bridge hops.
- Real-time alerting on new transactions from watched addresses.

---

*This methodology will be refined as ingestion and traversal are implemented. Changes to scoring weights or match rules require updating this file and bumping the scoring model version.*
