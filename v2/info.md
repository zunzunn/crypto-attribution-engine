# Crypto Attribution Engine v2 — Complete AI Context & Development Guide

## 0. Purpose of this document

This document is the **authoritative context file for the Crypto Attribution Engine v2 project**.

It is intended to be pasted into another AI coding/reasoning model so that the model can understand:

- what the project is
- why it exists
- what has already been implemented
- the current architecture
- what the current code can and cannot do
- the current testing state
- known limitations
- what should be built next
- what must NOT be changed prematurely

An AI model receiving this document should **continue from the current v2 implementation rather than rebuilding the project from scratch**.

---

# 1. Project Identity

## Project Name

**Crypto Attribution Engine v2**

## Domain

Blockchain forensics / cryptocurrency cybercrime investigation support.

## Primary blockchain currently supported

**Ethereum**

## Primary purpose

The engine helps investigators trace cryptocurrency flows from a suspicious address through transaction relationships, identify known service/entity addresses, preserve attribution evidence, and calculate an evidence-based risk score.

The project is intended as an **investigation-support system**, not as an autonomous criminal-identification or asset-freezing system.

---

# 2. Thesis Context

## Thesis statement

> **To combat cryptocurrency-related cybercrimes, an automated attribution engine integrated with the SAHYOG portal is necessary to swiftly identify service providers and streamline asset freezing.**

The larger thesis problem is that cryptocurrency transactions are public but can be difficult to investigate at scale.

A scammer can move funds through:

- multiple wallets
- wallet hopping
- split/fan-out patterns
- consolidation/fan-in patterns
- ERC-20 tokens
- internal contract transactions
- exchanges/VASPs
- mixers
- bridges
- multiple blockchains
- unknown addresses

Manual investigation becomes slow when the transaction trail contains many addresses and many possible paths.

The project's goal is to automate the repetitive parts of this investigation.

---

# 3. Simple Problem Statement

A simple explanation of the problem:

> Cryptocurrency scammers can make stolen funds difficult to follow by moving them through multiple wallets, splitting and consolidating funds, changing tokens, using exchanges, mixers and bridges, or moving assets across blockchains. Although confirmed blockchain transactions are normally still visible, the relationship between the original suspicious funds and later destinations can become difficult to establish manually. The Crypto Attribution Engine automates transaction collection, graph construction, fund-flow tracing, address attribution, evidence collection and risk scoring so investigators can understand where funds moved and which known services are involved.

---

# 4. Core System Idea

The current engine follows this pipeline:

```text
Suspicious Ethereum Address
            ↓
Fetch blockchain transactions
            ↓
Normalize ETH / ERC-20 / internal ETH
            ↓
Build unified transaction graph
            ↓
BFS trace through connected addresses
            ↓
Address attribution
   ┌────────┴─────────┐
   ↓                  ↓
Local Registry    Etherscan Metadata
   └────────┬─────────┘
            ↓
Combined Attribution
            ↓
Evidence
            ↓
Evidence-based Risk Score
            ↓
Investigation Result
```

---

# 5. Important Conceptual Distinctions

## Address vs Person

An Ethereum address is a public blockchain identifier.

Attributing:

```text
0xABC...
→ VASP
```

does NOT mean:

```text
0xABC...
→ specific criminal person
```

The engine currently performs **address/entity attribution**, not personal identity attribution.

## Risk vs Proof

A high risk score does NOT prove criminal activity.

The correct interpretation is:

> "The available blockchain evidence produces a higher investigative risk."

The frontend and future reports must never say:

> "This person is a criminal."

unless an external lawful process independently establishes that fact.

---

# 6. Current Technology Stack

Current implementation:

- Python 3.12.x
- `requests`
- `python-dotenv`
- Etherscan API V2
- JSON
- Python standard library
- `argparse`
- `collections.defaultdict`
- `io.StringIO`

Testing:

- pytest is installed and has also been used during development
- The project also contains an embedded test runner inside `eth_txs.py`

The current canonical manual test command used during development is:

```bash
python3 eth_txs.py test
```

The project should eventually move toward a cleaner dedicated pytest test structure, but this should be done deliberately rather than during unrelated feature work.

---

# 7. Current File Structure

Current conceptual structure:

```text
v2/
├── .env
├── .env.example
├── .gitignore
├── address_registry.json
├── eth_txs.py
├── README.md
├── requirements.txt
├── transaction.json
├── token_transfers.json
└── internal_transactions.json
```

Generated transaction files and `.env` are intended to be gitignored.

## Security

`.env` contains the Etherscan API key.

**Never expose, print, commit, or reproduce the API key.**

If a key appears in a screenshot, log, code, or shared document, it should be considered exposed and rotated/revoked.

---

# 8. Main Code File

The main implementation is:

```text
eth_txs.py
```

It currently contains the core functionality for:

- Etherscan data fetching
- transaction parsing
- normalization
- graph construction
- BFS traversal
- address registry
- attribution
- Etherscan metadata
- combined attribution
- risk scoring
- trace analysis
- tests

The file has become large because development has intentionally been incremental in one file.

Do not perform a large rewrite unless explicitly requested.

---

# 9. Etherscan Integration

The project uses the **Etherscan V2 API**.

Base endpoint:

```text
https://api.etherscan.io/v2/api
```

Ethereum Mainnet:

```text
chainid=1
```

The API key is loaded from `.env` using `python-dotenv`.

---

## 9.1 Normal Ethereum transactions

Uses the Etherscan V2 account transaction endpoint:

```text
module=account
action=txlist
```

This provides normal Ethereum transaction history.

The engine extracts information such as:

- transaction hash
- sender
- receiver
- value
- timestamp
- transaction status

---

## 9.2 ERC-20 transfers

Uses:

```text
module=account
action=tokentx
```

The engine supports ERC-20 transfers.

Important:

**ERC-20 tokens do not necessarily use 18 decimals.**

The implementation uses `tokenDecimal`.

Example:

```text
USDT
tokenDecimal = 6
```

Therefore:

```text
1000000 raw units = 1 USDT
```

Do not assume every token has 18 decimals.

---

## 9.3 Internal Ethereum transactions

Uses:

```text
module=account
action=txlistinternal
```

Internal transaction data is normalized and included in the unified model.

Failed/error internal transactions are excluded from the unified graph.

---

## 9.4 Address metadata

The project initially attempted:

```text
module=account
action=profile
```

This failed against the real API with:

```text
Missing Or invalid Action name
```

This was corrected after a real API test.

The current Etherscan V2 metadata request uses:

```text
module=nametag
action=getaddresstag
```

This is important historical context: **do not reintroduce `account.profile`.**

The metadata integration can provide:

- address
- nametag
- labels
- other metadata fields depending on the response

The engine conservatively maps clear labels to:

```text
VASP
Bridge
Mixer
Scam/Fraud
Unknown
```

Unknown or ambiguous labels remain Unknown.

---

# 10. Data Normalization

The project converts different blockchain transfer types into a common structure.

Conceptually:

```text
{
    "hash": "...",
    "from_address": "...",
    "to_address": "...",
    "asset_type": "...",
    "asset_contract": "...",
    "symbol": "...",
    "amount": ...,
    "timestamp": ...
}
```

Supported asset types include:

```text
ETH
ERC20
INTERNAL_ETH
```

Internal transactions can additionally contain an error/status field.

---

# 11. Graph Model

The graph is directed.

```text
Address = Node
Transaction = Directed Edge
```

Example:

```text
A → B
B → C
C → D
```

Multiple transfers between the same addresses must not cause important transaction metadata to be lost.

The unified graph therefore preserves multiple transfers on the same relationship.

---

# 12. BFS Tracing

The project uses Breadth-First Search to follow funds through connected addresses.

Example:

```text
Hop 0:
Suspicious Wallet

Hop 1:
Wallet A
Wallet B

Hop 2:
Wallet C
Wallet D

Hop 3:
Known VASP
```

BFS is limited by a configurable maximum hop count.

The engine also handles:

- branching
- cycles
- repeated addresses
- multiple transfers
- hop limits
- no outgoing edges
- invalid starting addresses

The graph can represent fan-out and fan-in patterns naturally.

---

# 13. Scammer Obfuscation Techniques and Current Handling

The engine should be understood as handling **observable transaction patterns**, not "breaking" every anti-tracing technique.

| Technique              | Explanation                                             | Current capability                                                                 |
| ---------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Wallet hopping         | Funds move through many wallets                         | 🟢 Handles                                                                         |
| Multiple transfers     | Funds move through many transaction edges               | 🟢 Handles                                                                         |
| Splitting / fan-out    | One source sends to many wallets                        | 🟢 Graph can represent; dedicated detector not yet complete                        |
| Consolidation / fan-in | Many wallets send to one wallet                         | 🟢 Graph can represent; dedicated detector not yet complete                        |
| ETH transfers          | Native ETH movement                                     | 🟢 Handles                                                                         |
| ERC-20 transfers       | Funds move as USDT/USDC/etc.                            | 🟢 Handles                                                                         |
| Internal transactions  | ETH moves through contracts/internal calls              | 🟢 Handles                                                                         |
| Known VASP/exchange    | Funds reach known service                               | 🟢 Attribution supported                                                           |
| Known mixer            | Funds reach a known mixer address                       | 🟢 Can attribute if reliable metadata/registry exists                              |
| Bridge                 | Funds reach/use a bridge                                | 🟡 Can identify known bridge addresses, but cross-chain continuation is incomplete |
| Cross-chain movement   | Ethereum → another blockchain                           | 🔴 Not fully supported yet                                                         |
| Unknown wallet         | No reliable label exists                                | 🟡 Traces address but may remain Unknown                                           |
| Rapid wallet hopping   | Many transfers over short periods                       | 🟡 Timestamps are available; dedicated behavioral detector is not yet complete     |
| Mixer obfuscation      | Mixer can break direct deposit/withdrawal relationships | 🔴 Cannot reliably prove ownership of later withdrawals                            |
| Privacy-focused chains | Reduced transparency                                    | 🔴 Not currently supported                                                         |
| Off-chain movement     | Funds leave observable blockchain flow                  | 🔴 Cannot trace from blockchain data alone                                         |

---

# 14. Consolidation / Fan-In

Consolidating funds means bringing funds from multiple wallets into one wallet.

Example:

```text
Wallet A ──┐
Wallet B ──┤
Wallet C ──┼──→ Wallet D
Wallet E ──┘
```

Wallet D is the consolidation point.

The current graph can represent this because several edges point to the same node.

However:

> The current engine can represent and trace consolidation, but it does not yet have a dedicated "consolidation detected" classifier.

That can be a future behavioral-analysis feature.

---

# 15. Address Registry

File:

```text
address_registry.json
```

The registry currently contains **synthetic test intelligence**.

Example conceptual entities:

```text
KnownVASP
KnownBridge
KnownMixer
```

Fields include:

```text
address
entity_name
entity_type
source
confidence
```

The synthetic registry must NOT be presented as real-world law-enforcement intelligence.

Functions include:

```text
load_address_registry()
lookup_address()
classify_entity()
attribute_address()
```

Address lookup is case-insensitive.

Unknown addresses remain Unknown.

---

# 16. Etherscan Attribution

Function:

```text
fetch_address_metadata_from_etherscan()
```

It returns structured metadata including:

```text
address
entity_name
entity_type
source
confidence
evidence
raw_metadata
```

Conservative mapping:

```text
clear VASP/exchange label → VASP
clear bridge label → Bridge
clear mixer label → Mixer
clear scam/fraud/phishing label → Scam/Fraud
otherwise → Unknown
```

Confidence convention currently used:

```text
Clear mapped label → 1.0
Name tag only → 0.5
No usable attribution → 0.0
```

These are **application-level confidence conventions**, not claims that Etherscan itself provides a universally calibrated probability.

---

# 17. Combined Attribution

Function:

```text
combine_attribution_sources(
    address,
    registry,
    etherscan_metadata
)
```

It combines:

```text
Local Registry
+
Etherscan Metadata
```

Rules currently implemented:

### Registry known + Etherscan unknown

Preserve registry attribution.

### Registry unknown + Etherscan mapped

Use Etherscan attribution.

### Both agree

Combine evidence and sources.

### Conflict

Preserve the registry attribution as primary and explicitly record the disagreement.

### Both unknown

Return Unknown with zero confidence.

The output includes:

```text
address
entity_name
entity_type
source
confidence
evidence
sources
combined_evidence
```

Important:

**Conflicting sources must never be silently hidden.**

---

# 18. Evidence Collection

Evidence comes from observable data already available to the engine.

Main evidence sources:

## A. Blockchain transaction evidence

Includes:

- transaction hash
- sender
- receiver
- amount
- asset/token
- timestamp
- transaction type
- path through the graph

## B. Address registry evidence

The local registry can provide:

- entity name
- entity type
- source
- confidence

## C. Etherscan metadata evidence

Can provide:

- nametag
- labels
- address metadata

## D. Combined evidence

When multiple sources agree, the engine preserves multiple sources.

When they conflict, the conflict is preserved.

Evidence should answer:

> "Why did the engine make this attribution?"

It should not merely output an unexplained entity name.

---

# 19. Risk Scoring

There are currently TWO risk-scoring concepts.

## 19.1 Original prototype

Function:

```text
calculate_risk_score(entity_type, hops)
```

Base points:

```text
VASP       = 10
Bridge     = 20
Mixer      = 40
Scam/Fraud = 50
Unknown    = 0
```

Hop penalty:

```text
5 × hops
```

Risk levels:

```text
Low       < 25
Medium    25–49
High      50–74
Critical  >= 75
```

Score is capped between 0 and 100.

This function is preserved for compatibility with existing tests.

---

# 20. Evidence-Based Risk Scoring

Newer function:

```text
calculate_evidence_risk(attribution, hops=0)
```

Purpose:

Make risk depend on actual attribution evidence rather than only entity type.

Current design:

```text
Scam/Fraud = 50
Mixer      = 40
Bridge     = 20
VASP       = 10
Unknown    = 0
```

Confidence scaling:

```text
score × confidence
```

Hop penalty:

```text
3 × hops
```

This is deliberately less aggressive than the original 5-point hop penalty.

Risk levels remain:

```text
Low       < 25
Medium    25–49
High      50–74
Critical  >= 75
```

Output:

```text
{
    "score": ...,
    "risk_level": "...",
    "reasons": [...]
}
```

Reasons should explain meaningful contributions.

Example:

```text
Known Mixer attribution
High-confidence attribution
Supported by Etherscan metadata
Reached within 2 hops
```

The risk model is currently **deterministic and rule-based**.

There is no ML model.

---

# 21. Risk Interpretation

Risk is an investigative prioritization signal.

It does NOT mean:

```text
Risk = criminality
```

Correct:

```text
High risk
→ deserves greater investigative attention
```

Incorrect:

```text
High risk
→ confirmed criminal
```

The frontend and reports must preserve this distinction.

---

# 22. Trace-Level Risk Integration

The evidence-based risk scoring has been integrated into trace analysis.

The intended pipeline is now:

```text
analyze_trace()
      ↓
Unified BFS
      ↓
Discovered addresses
      ↓
Attribution
      ↓
Evidence
      ↓
Evidence-based risk
      ↓
Trace result
```

Each discovered address can therefore have:

```text
address
entity
entity_type
confidence
source/sources
evidence
risk score
risk level
risk reasons
hop distance
```

The existing attribution fields should be preserved.

---

# 23. Current Testing Status

The project has accumulated many embedded tests.

A recent verified run reported:

```text
41 test functions executed
all passed
```

The latest test run explicitly showed the Step 16A risk tests and Step 16B trace-risk tests passing.

Step 16A tests include:

```text
test_calculate_evidence_risk_unknown
test_calculate_evidence_risk_vasp_low_confidence
test_calculate_evidence_risk_vasp_full_confidence
test_calculate_evidence_risk_bridge
test_calculate_evidence_risk_mixer
test_calculate_evidence_risk_scam_fraud
test_calculate_evidence_risk_hop_distance_penalty
test_calculate_evidence_risk_evidence_based_scoring
```

Step 16B tests include:

```text
test_analyze_trace_risk_unknown
test_analyze_trace_risk_vasp
test_analyze_trace_risk_bridge
test_analyze_trace_risk_mixer
test_analyze_trace_risk_scam
test_analyze_trace_risk_hop_penalty
test_analyze_trace_risk_preserves_attribution
```

Earlier project documentation may claim "70+ tests", but the latest verified development run counted **41 executed test functions**. Treat the **latest actual test output** as authoritative rather than older README counts.

---

# 24. Important Test-Runner Note

The embedded test runner has historically accumulated duplicate registrations.

At one point, running:

```bash
python3 eth_txs.py test
```

printed some test groups twice.

The functionality still passed, but this should eventually be cleaned up so every test function executes exactly once.

This cleanup should be done carefully and separately from feature development.

Do NOT rewrite the whole test runner.

---

# 25. Current Git / Development State

The project uses Git with a `main` branch and remote repository.

Completed milestones have generally been committed and pushed after tests pass.

The development process intentionally uses commits as checkpoints.

Before changing major code:

```bash
git status
git diff
```

After completing a feature:

```bash
python3 eth_txs.py test
git status
git diff --stat
git add ...
git commit ...
git push
git status
```

Do not discard changes blindly with `git restore` or `git reset`.

---

# 26. Current Project Status

## Completed

### Foundation

- Ethereum transaction fetching
- Etherscan V2 integration
- raw transaction saving
- Ethereum graph
- BFS traversal
- real address integration

### Asset coverage

- ETH
- ERC-20
- internal ETH

### Graph

- unified transaction model
- unified graph
- token-aware traversal
- multiple transfers preserved
- failed internal transfers excluded
- cycles handled
- hop limits

### Attribution

- synthetic address registry
- registry lookup
- evidence-based address attribution
- Etherscan metadata
- combined registry + Etherscan attribution
- conflict preservation

### Risk

- original deterministic risk score
- evidence-based risk score
- risk reasons
- trace-level risk integration

### Testing

- broad embedded test coverage
- latest verified run: 41 test functions passing

---

# 27. Current Limitations

These limitations should be clearly acknowledged in the thesis.

## 27.1 Unknown addresses

If an address has no reliable registry or metadata attribution, the engine cannot determine the owner merely from the address.

It remains:

```text
Unknown
```

The engine should never invent an identity.

---

## 27.2 Incomplete attribution data

Not every blockchain address has a label.

Therefore:

```text
Traceable address
≠
Identifiable entity
```

---

## 27.3 Mixers

A known mixer address can potentially be identified.

However, the engine cannot automatically prove:

```text
Deposit X
→
Withdrawal Y
```

belongs to the same underlying funds.

A mixer can intentionally break or obscure that relationship.

---

## 27.4 Bridges

A known bridge can be attributed, but current Ethereum-only tracing does not fully continue the trace onto another blockchain.

Example:

```text
Ethereum
   ↓
Bridge
   ↓
TRON
   ↓
Wallet
```

The current system cannot yet completely trace the TRON side.

---

## 27.5 Cross-chain transactions

The current engine is primarily Ethereum-focused.

Full cross-chain tracing is a future feature.

---

## 27.6 Privacy-focused systems

Some privacy-oriented networks or mechanisms provide less transparent transaction relationships.

The current engine does not solve those cases.

---

## 27.7 Off-chain movement

If funds leave the observable blockchain environment, the engine cannot continue tracing them using blockchain transaction data alone.

---

## 27.8 API dependency

The engine relies on Etherscan for some data.

Potential problems:

- API limits
- unavailable data
- provider downtime
- indexing differences
- incorrect or outdated labels

The system should preserve the source of metadata.

---

## 27.9 Risk score limitations

The risk model is deterministic and currently uses simple rules.

It is not a statistically calibrated probability of criminality.

It should be described as:

> an evidence-based investigative risk/prioritization score.

---

## 27.10 Synthetic registry limitation

The current `address_registry.json` contains synthetic test entries.

It must not be presented as a real-world intelligence database.

A production system would need verified sources and proper provenance.

---

# 28. What the Project Can Currently Handle

A simplified capability statement:

> The engine can collect Ethereum ETH, ERC-20 and internal transaction data, normalize those transfers, construct a unified transaction graph, trace connected addresses using BFS, attribute known addresses using a local registry and Etherscan metadata, preserve supporting evidence, combine multiple attribution sources, and calculate evidence-based risk scores.

---

# 29. What It Cannot Yet Fully Handle

```text
❌ Full cross-chain tracing
❌ Reliable mixer deposit-to-withdrawal attribution
❌ Privacy-chain analysis
❌ Off-chain fund movement
❌ Guaranteed identity of unknown wallets
❌ Production-grade behavioral pattern detection
❌ Fully calibrated ML/statistical risk model
❌ Real-world intelligence registry at production scale
```

---

# 30. Future Roadmap

The project should continue incrementally.

## Step 17 — Multichain support

Add another blockchain adapter.

A likely first additional chain is **TRON**, because of the importance of USDT activity.

Do not rewrite the Ethereum engine.

Instead move toward:

```text
Ethereum Adapter
      ↓
TRON Adapter
      ↓
Unified Transfer Model
      ↓
Unified Graph
      ↓
Trace
```

The exact TRON data provider/API should be researched before implementation.

---

## Step 18 — Behavioral pattern detection

Potential patterns:

### Fan-out

```text
A
├→ B
├→ C
├→ D
└→ E
```

### Fan-in / consolidation

```text
A ─┐
B ─┤
C ─┼→ D
E ─┘
```

### Rapid wallet hopping

Multiple transfers across addresses within short time intervals.

### Layering

Multiple sequential hops intended to make the flow harder to follow.

### Service interaction

Known:

- VASP
- bridge
- mixer
- scam/fraud
- other service categories

These should become **evidence signals**, not automatic proof of criminality.

---

# 31. Step 19 — Investigation Report

Build a structured investigation report containing:

```text
Case ID
Starting address
Network
Investigation timestamp

Trace summary
Addresses discovered
Maximum hops
Transactions analyzed

Important addresses
Entity attribution
Confidence
Sources

Evidence
Transaction hashes
Attribution evidence
Source disagreements

Risk
Score
Risk level
Reasons
```

Potential output:

```text
JSON
PDF
```

---

# 32. Step 20 — Backend/API Layer

Only after the core engine is stable should the system expose APIs.

Possible architecture:

```text
Python Attribution Engine
        ↓
FastAPI
        ↓
Frontend
```

Potential API endpoints:

```text
POST /investigations
GET /investigations/{id}
GET /addresses/{address}
GET /transactions/{hash}
GET /traces/{address}
```

Exact API design should be decided later.

---

# 33. Database

A database such as PostgreSQL/Supabase may eventually be added for:

- cases
- investigations
- users
- transaction cache
- attribution records
- evidence
- reports
- audit logs

Do not introduce the database prematurely if the current core engine can remain file-based during development.

---

# 34. Frontend

A separate frontend is being developed in parallel by teammates.

The frontend should be an **investigator-facing dashboard**, not a crypto trading interface.

Recommended conceptual UI:

```text
Dashboard
   ↓
Investigation
   ↓
Enter wallet address
   ↓
Trace
   ↓
Transaction Graph
   +
Trace Path
   +
Attribution
   +
Evidence
   +
Risk
```

Frontend should use mock JSON until the API layer is ready.

It should never contain:

- private keys
- seed phrases
- Etherscan API keys
- blockchain tracing logic
- risk calculation logic

---

# 35. Frontend Requirements

Important frontend components:

## Dashboard

Show:

- investigations
- suspicious addresses
- high-risk addresses
- known services
- recent investigations

## Investigation page

Input:

```text
Ethereum address
Maximum hops
Asset/network filters
```

## Graph

Show:

```text
wallet nodes
transaction edges
hop distance
entity type
```

Support:

- zoom
- pan
- node selection
- edge selection
- filters
- path highlighting

## Address panel

Show:

```text
Address
Entity
Entity type
Confidence
Sources
Evidence
Risk
Risk reasons
Hop distance
```

## Transaction panel

Show:

```text
Hash
Sender
Receiver
Amount
Token
Asset type
Timestamp
Status
```

## Trace/path view

Example:

```text
Hop 0
Suspicious Wallet
      ↓
Hop 1
Wallet B
      ↓
Hop 2
Known Mixer
      ↓
Hop 3
Known VASP
```

## Evidence panel

Show the exact sources/evidence used.

Conflicts should be visible.

## Report preview

Show:

- case information
- trace
- entities
- evidence
- risk
- sources

---

# 36. SAHYOG Integration

The thesis eventually aims to integrate the attribution engine with the **SAHYOG portal/workflow**.

Conceptually:

```text
Investigator
      ↓
Suspicious wallet
      ↓
Crypto Attribution Engine
      ↓
Trace
      ↓
Attribution
      ↓
Evidence
      ↓
Identify relevant service/provider
      ↓
SAHYOG
      ↓
Lawful disclosure / freezing workflow
```

The engine should assist investigators.

It should NOT autonomously freeze assets.

Legal action should remain under authorized investigative procedures.

The exact SAHYOG API/interface must be researched before implementation.

---

# 37. Important Research Areas Still Needed

Before implementing later stages, research should cover:

- TRON data access/API
- cross-chain bridge identification
- VASP/address intelligence sources
- mixer identification
- OFAC/sanctions data where legally appropriate
- verified public blockchain labels
- evidence provenance
- attribution confidence methodology
- SAHYOG integration/API availability
- data retention/security
- audit logging
- investigator workflow
- evaluation metrics

Do not claim an external source is integrated until it has actually been implemented and tested.

---

# 38. Evaluation Strategy for Thesis

The final thesis should evaluate the system using measurable criteria.

Potential metrics:

## Tracing

- number of addresses discovered
- maximum trace depth
- trace completion time
- graph size

## Attribution

- known addresses correctly identified
- unknown-address handling
- source agreement/conflict handling

## Risk

- consistency of deterministic scoring
- explainability of reasons
- false-positive considerations

## Performance

- API latency
- graph traversal time
- processing time as graph size increases

## Comparison

Compare:

```text
Manual tracing
vs
Automated engine
```

Potential measurements:

```text
time required
number of addresses manually checked
number of hops successfully traced
number of known entities found
```

The thesis should avoid claiming perfect attribution.

---

# 39. Security Requirements

Never store or request:

```text
Private keys
Seed phrases
Wallet passwords
```

API keys must remain server-side/environment variables.

The eventual frontend must never contain:

```text
ETHERSCAN_API_KEY
```

in client-side code.

The system should eventually include:

- authentication
- authorization
- audit logging
- secure case storage
- evidence provenance
- input validation

when moved to a production-style backend.

---

# 40. Coding-Agent Rules

Any AI coding agent working on this project must follow these rules.

## Rule 1 — Do not rebuild

Continue from the existing v2 implementation.

## Rule 2 — Small steps

Use:

```text
Understand
→ Build
→ Run
→ Test
→ Explain
→ Commit
→ Next
```

## Rule 3 — Inspect before editing

Before modifying `eth_txs.py`, inspect the surrounding structure.

## Rule 4 — Avoid broad replacements

Do not use giant string replacements.

Do not rewrite large parts of `eth_txs.py` for a small feature.

## Rule 5 — Preserve existing functionality

Existing tests must continue to pass.

## Rule 6 — Test new functionality

Every new feature should have automated tests.

## Rule 7 — Real API verification

When adding an external API integration:

```text
Mocked tests
+
Real API verification
```

should both be used where practical.

## Rule 8 — No invented evidence

Never invent:

- entity identities
- blockchain labels
- confidence values
- criminal attribution
- API responses

## Rule 9 — No premature architecture

Do not add:

```text
FastAPI
PostgreSQL
ML
frontend integration
Docker
microservices
```

unless the current roadmap step specifically requires it.

## Rule 10 — Commit checkpoints

After a stable milestone:

```text
git status
git diff
tests
git add
git commit
git push
```

---

# 41. Current Immediate Development State

The latest major completed milestones are:

```text
Steps 1–10   ✅ Foundation
Step 11      ✅ Unified graph + token-aware BFS
Step 12      ✅ Address registry
Step 13      ✅ Evidence attribution
Step 14      ✅ Unified trace + attribution
Step 15A     ✅ Etherscan metadata
Step 15B     ✅ Combined attribution
Step 16A     ✅ Evidence-based risk scoring
Step 16B     ✅ Trace-level risk integration
```

The latest verified test run reported:

```text
41 test functions executed
all passed
```

The test output included:

```text
test_calculate_evidence_risk_unknown
test_calculate_evidence_risk_vasp_low_confidence
test_calculate_evidence_risk_vasp_full_confidence
test_calculate_evidence_risk_bridge
test_calculate_evidence_risk_mixer
test_calculate_evidence_risk_scam_fraud
test_calculate_evidence_risk_hop_distance_penalty
test_calculate_evidence_risk_evidence_based_scoring

test_analyze_trace_risk_unknown
test_analyze_trace_risk_vasp
test_analyze_trace_risk_bridge
test_analyze_trace_risk_mixer
test_analyze_trace_risk_scam
test_analyze_trace_risk_hop_penalty
test_analyze_trace_risk_preserves_attribution
```

All passed.

---

# 42. Immediate Next Work

Before starting a new major feature:

1. Verify Git is clean.
2. Confirm Step 16B is committed/pushed.
3. Clean duplicate test-runner registrations carefully if they still exist.
4. Do not modify production behavior during test-runner cleanup.
5. Re-run the complete suite.
6. Then begin the next roadmap item.

The likely next major feature is:

> **Step 17 — Multichain support, beginning with one additional blockchain.**

However, the first step of Step 17 should be **Understand**, not coding.

The AI should first explain:

- why Ethereum-only tracing is insufficient
- what changes when a bridge is involved
- how cross-chain transaction data differs
- what a chain adapter should do
- which chain should be implemented first
- how to preserve the existing unified transfer model

Only then should implementation begin.

---

# 43. Final Mental Model

The entire project should be understood as:

```text
                 CRYPTO ATTRIBUTION ENGINE

                       Input
                         │
                         ▼
                Suspicious Address
                         │
                         ▼
               Blockchain Data
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             ETH       ERC-20    Internal ETH
              └──────────┼──────────┘
                         ▼
                Unified Transfers
                         │
                         ▼
                Transaction Graph
                         │
                         ▼
                    BFS Trace
                         │
                         ▼
                 Discovered Addresses
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Local Registry         Etherscan Metadata
              └──────────┬──────────┘
                         ▼
                Combined Attribution
                         │
                         ▼
                      Evidence
                         │
                         ▼
                 Evidence Risk Score
                         │
                         ▼
             Investigation Intelligence
                         │
                         ▼
                  Future API Layer
                         │
                         ▼
                    Frontend
                         │
                         ▼
                 Future SAHYOG Flow
```

## One-sentence project explanation

> **The Crypto Attribution Engine automatically follows cryptocurrency funds through blockchain transaction graphs, uses multiple evidence sources to identify known services and entities, and produces explainable risk information so investigators can investigate suspicious fund flows faster than manual tracing.**
