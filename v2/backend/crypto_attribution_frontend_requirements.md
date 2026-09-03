# Crypto Attribution Engine — Frontend Requirements

## 1. Purpose

This document defines the frontend that should be developed alongside the **Crypto Attribution Engine** thesis project.

The backend/engine is being developed separately. The frontend should be built as an **investigator-facing dashboard** that can consume the engine's results later.

The frontend should therefore focus on:

- displaying investigation data clearly
- visualizing transaction flows
- showing attribution and evidence
- showing risk scores and reasons
- making suspicious-wallet investigation easy
- keeping the UI ready for future API integration

The frontend should **not implement blockchain tracing, attribution logic, risk calculations, or ML itself**. Those belong to the backend/engine.

---

# 2. Main User

The primary user is an investigator or authorized law-enforcement user.

The UI should answer these questions quickly:

1. What wallet am I investigating?
2. Where did the funds move?
3. How many hops did the money travel?
4. Which addresses are known?
5. Is an address a VASP, bridge, mixer, scam/fraud address, or unknown?
6. What evidence supports the attribution?
7. What is the risk score?
8. Why did the system assign that risk?
9. Which transactions connect the addresses?
10. Can I generate/export an investigation report?

---

# 3. Recommended Frontend Stack

The frontend can use:

- React
- Vite
- JavaScript or TypeScript
- Tailwind CSS
- a graph visualization library such as React Flow, Cytoscape.js, or D3
- a chart library if required

The exact library can be chosen by the frontend developer.

Keep the architecture simple and modular.

Do NOT build a separate backend for the frontend.

The frontend should initially work with **mock JSON data**, because the attribution engine/API is still being developed.

Later, the mock data can be replaced with API calls.

---

# 4. Main Pages / Views

The frontend should contain the following major views.

## 4.1 Dashboard

Purpose: give an investigator an overview.

Display:

- total investigations
- active investigations
- suspicious addresses
- high-risk addresses
- recent investigations
- recently detected entities
- basic transaction statistics

Example cards:

```text
Investigations       24
High Risk             7
Suspicious Wallets   31
Known Services       14
```

Also include a list of recent investigations.

---

# 5. Investigation / Trace Page

This is the most important page.

The investigator should be able to enter:

```text
Ethereum Wallet Address
```

Example:

```text
0xFBD7Afc49821A1250A299428f3aE7723415f1c44
```

Controls:

- wallet address input
- blockchain/network selector
- maximum hops
- asset filter
- start investigation button

For the current version, Ethereum should be the primary supported network.

Future networks can be added later.

---

# 6. Investigation Summary

After a trace is performed, show a summary at the top.

Example:

```text
Investigated Address
0xFBD7...

Network
Ethereum

Addresses Discovered
37

Maximum Hops
5

High-Risk Addresses
4

Known Services
6

Unknown Addresses
21
```

Also show an overall investigation status.

---

# 7. Transaction Graph

This is the most important visualization.

Display addresses as nodes:

```text
Suspicious Wallet
       |
       v
    Wallet A
     /    \
    v      v
 Wallet B  Wallet C
     |
     v
 Known VASP
```

Transactions should be represented as directed edges.

The graph should support:

- zoom
- pan
- node selection
- edge selection
- fit-to-screen
- reset view
- filtering
- highlighting paths
- showing hop levels

Use different visual indicators for entity types:

```text
VASP
Bridge
Mixer
Scam/Fraud
Unknown
Suspicious wallet
```

Do not hard-code a specific color scheme if the design system changes; use a consistent visual legend.

---

# 8. Node Information Panel

When the investigator clicks a node, open a side panel.

Show:

### Address

```text
0xABC...
```

### Entity

```text
Known VASP
```

### Entity Type

```text
VASP
```

### Confidence

```text
0.90
```

### Risk

```text
High
Score: 67/100
```

### Hop Distance

```text
2 hops
```

### Sources

```text
Address Registry
Etherscan Metadata
```

### Evidence

Display the evidence that caused the attribution.

Example:

```text
Etherscan metadata identifies this address
with an exchange-related label.

Local registry also identifies this address
as a known VASP.
```

---

# 9. Risk Display

The frontend must make risk understandable.

Show:

```text
Risk Score: 67 / 100
Risk Level: HIGH
```

Also display the reasons.

Example:

```text
Why this address is high risk:

• Known mixer attribution
• High-confidence attribution
• Supported by multiple sources
• Address reached within 2 hops
```

Do NOT display a high risk score as proof that an entity is criminal.

Use wording such as:

> "Risk based on available blockchain evidence"

rather than:

> "Confirmed criminal"

---

# 10. Evidence Panel

Evidence is extremely important to the thesis.

Create a dedicated evidence section.

For each attribution show:

```text
Source
Etherscan Metadata

Evidence
Address has a recognized exchange label.

Confidence
1.0

Entity Type
VASP
```

If multiple sources exist:

```text
Sources:
• Address Registry
• Etherscan Metadata
```

If sources disagree, clearly display the conflict.

Example:

```text
Attribution Conflict

Registry: VASP
Etherscan: Mixer

Primary attribution:
Registry

Note:
Sources disagree and should be reviewed by an investigator.
```

Never hide attribution conflicts.

---

# 11. Transaction Details

When an edge/transaction is selected, display:

- transaction hash
- sender
- receiver
- amount
- token
- asset type
- timestamp
- transaction type
- status

Examples of asset types:

```text
ETH
ERC20
INTERNAL_ETH
```

For ERC-20:

```text
Token: USDT
Amount: 250.00
Contract: 0x...
```

For internal ETH:

```text
Type: INTERNAL_ETH
Amount: 0.25 ETH
```

---

# 12. Trace Path View

Provide a readable alternative to the graph.

Example:

```text
Hop 0
Suspicious Wallet
0xAAA...

       ↓ 100 USDT

Hop 1
Wallet B
0xBBB...

       ↓ 100 USDT

Hop 2
Known Mixer
0xCCC...

       ↓

Hop 3
Known VASP
0xDDD...
```

This is useful when the graph becomes large.

The investigator should be able to switch between:

```text
Graph View
```

and:

```text
Path / Timeline View
```

---

# 13. Filters

The graph and transaction list should support filters.

Useful filters:

### Entity type

```text
All
VASP
Bridge
Mixer
Scam/Fraud
Unknown
```

### Asset

```text
All
ETH
USDT
Other ERC-20
```

### Risk

```text
All
Low
Medium
High
Critical
```

### Hop

```text
0
1
2
3
4+
```

### Source

```text
Registry
Etherscan
Multiple Sources
```

---

# 14. Search

Provide address search.

The investigator should be able to enter a wallet address and quickly see:

- whether it exists in the current investigation
- its attribution
- its risk
- its hop distance

Address search should support case-insensitive Ethereum addresses.

---

# 15. Investigation History

Create a page showing previous investigations.

Each investigation can contain:

```text
Investigation ID
Date
Starting Address
Network
Addresses Discovered
Highest Risk
Status
```

Example:

```text
CASE-001
0xFBD7...
Ethereum
37 addresses
High
Completed
```

For the initial frontend, this can use mock/local data.

Persistent database integration can be added later.

---

# 16. Report Page

Create a report preview.

The report should contain:

## Investigation Information

- case ID
- investigated address
- date
- network

## Trace Summary

- number of addresses
- maximum hops
- transactions analyzed

## Important Addresses

- address
- entity
- entity type
- confidence
- risk
- sources

## Evidence

List attribution evidence.

## Transaction Path

Show important fund-flow paths.

## Risk Summary

Show scores and reasons.

The report should eventually be exportable as:

```text
PDF
```

or:

```text
JSON
```

if practical.

---

# 17. API Integration Design

The frontend should be written so that mock data can later be replaced with the real engine API.

Do NOT hard-code data throughout React components.

Instead use a service layer.

Example:

```text
src/
├── components/
├── pages/
├── services/
│   └── api.js
├── data/
│   └── mockData.js
├── hooks/
├── utils/
└── App.jsx
```

Example future API abstraction:

```javascript
getInvestigation(address, options)
getTrace(address, maxHops)
getAddressAttribution(address)
getTransactionDetails(hash)
getInvestigationHistory()
```

Initially these functions can return mock JSON.

Later they can call the actual backend.

---

# 18. Mock Data

The frontend developer should create realistic mock investigation data.

Example:

```json
{
  "start": "0xAAA...",
  "discovered": 6,
  "hop_count": 3,
  "addresses": [
    {
      "address": "0xAAA...",
      "entity_type": "Unknown",
      "confidence": 0.0,
      "risk": {
        "score": 0,
        "risk_level": "Low"
      }
    },
    {
      "address": "0xBBB...",
      "entity_name": "Known VASP",
      "entity_type": "VASP",
      "confidence": 1.0,
      "risk": {
        "score": 10,
        "risk_level": "Low"
      }
    }
  ]
}
```

The mock structure should be designed around the current engine output.

Do not invent features that require backend functionality we don't currently have.

---

# 19. Important Future Compatibility

The frontend should be prepared for:

### Multiple blockchains

Current:

```text
Ethereum
```

Future:

```text
TRON
Bitcoin
Other chains
```

Do not build chain-specific UI logic everywhere.

Use:

```text
network
chain
asset_type
```

as data fields.

---

# 20. Important UX Principles

This is an investigation tool, not a consumer crypto app.

The UI should prioritize:

- clarity
- evidence
- traceability
- readable data
- professional appearance
- low visual clutter
- investigator workflow

Avoid:

- excessive animations
- crypto trading-style UI
- unnecessary gradients
- flashy Web3 visuals
- fake "AI detected criminal" messages
- unexplained risk scores

The investigator should understand the result within seconds.

---

# 21. Dashboard Layout Recommendation

A possible layout:

```text
┌─────────────────────────────────────────────────────┐
│ Crypto Attribution Engine                           │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│ Dashboard    │ Investigation                         │
│              │                                      │
│ Investigate │  [ Enter wallet address ] [Trace]     │
│              │                                      │
│ History      │ ┌────────┐ ┌────────┐ ┌────────┐    │
│              │ │37 Addr │ │4 High  │ │6 Known │    │
│ Reports      │ └────────┘ └────────┘ └────────┘    │
│              │                                      │
│ Settings     │          Transaction Graph           │
│              │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

---

# 22. What the Frontend DOES NOT Do

Do not implement these in the frontend:

- blockchain API fetching
- BFS
- transaction normalization
- attribution logic
- risk calculations
- mixer detection
- bridge detection
- entity classification
- ML
- private-key handling
- automatic asset freezing

The frontend only displays and interacts with the results produced by the engine/backend.

---

# 23. Security Requirements

The frontend must NEVER ask for or store:

```text
private keys
seed phrases
wallet passwords
Etherscan API keys
```

The user should only enter public blockchain addresses.

Do not expose backend API keys in frontend JavaScript.

---

# 24. Current Backend Capabilities the UI Should Reflect

The engine currently supports:

- Ethereum normal transactions
- ERC-20 token transfers
- Ethereum internal transactions
- unified transfer representation
- unified transaction graph
- BFS tracing
- address registry attribution
- Etherscan metadata attribution
- combined attribution from multiple sources
- evidence collection
- deterministic evidence-based risk scoring
- trace-level risk integration

Current limitations:

- primarily Ethereum
- unknown addresses may remain Unknown
- cross-chain tracing is not complete
- mixer deposit/withdrawal ownership cannot automatically be proven
- risk score is an investigative signal, not proof of criminality
- synthetic registry is currently test data

The frontend should visibly handle these limitations rather than hiding them.

---

# 25. Error States

Design clear error states for:

### Invalid address

```text
Invalid Ethereum address.
Please enter a valid 0x... address.
```

### No transactions

```text
No indexed transactions were found for this address.
```

### API failure

```text
Unable to retrieve blockchain data.
Please try again later.
```

### Unknown attribution

```text
No reliable entity attribution available.
```

### Large graph

```text
Large investigation detected.
Use filters or increase/decrease hop depth.
```

---

# 26. Loading States

Tracing can take time.

Show:

```text
Fetching transactions...
Building transaction graph...
Tracing fund flow...
Checking address attribution...
Calculating risk...
Preparing investigation...
```

Do not show fake progress percentages unless the backend actually provides progress information.

---

# 27. Visual Language

Use a professional cybersecurity/investigation dashboard style.

Suggested characteristics:

- dark or neutral professional interface
- strong information hierarchy
- readable tables
- clear graph
- compact cards
- restrained animations
- consistent typography
- accessible contrast

The UI should feel closer to an **investigation/intelligence platform** than a cryptocurrency trading website.

---

# 28. Definition of Done

The frontend is considered complete for the current phase when:

- [ ] Dashboard exists
- [ ] Wallet investigation input exists
- [ ] Investigation result page exists
- [ ] Transaction graph exists
- [ ] Graph nodes can be selected
- [ ] Address information panel exists
- [ ] Attribution/evidence is visible
- [ ] Risk score and reasons are visible
- [ ] Transaction details are visible
- [ ] Trace/path view exists
- [ ] Filters work
- [ ] Investigation history exists
- [ ] Report preview exists
- [ ] Mock API/data layer exists
- [ ] UI handles loading/error/unknown states
- [ ] No API keys/private keys are exposed
- [ ] Frontend is ready to replace mock data with the real backend API
- [ ] README explains how to run the frontend

---

# 29. Most Important Rule for the Frontend Developer

**Do not wait for the backend to be finished.**

Build the UI using mock JSON that resembles the current Crypto Attribution Engine output.

When the backend APIs become available, replace the mock service functions with real API calls.

The frontend and backend should remain loosely coupled.

The final intended system is:

```text
                 CRYPTO ATTRIBUTION ENGINE

                         Backend
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
       Blockchain       Attribution       Risk
          Data             + Evidence       │
             └──────────────┼──────────────┘
                            ↓
                       API Layer
                            ↓
                    ┌───────────────┐
                    │   Frontend    │
                    │ Investigator  │
                    │   Dashboard   │
                    └───────────────┘
```

The frontend should make the investigation understandable, visual, and evidence-driven without duplicating the backend's intelligence logic.
