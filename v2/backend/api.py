"""
Crypto Attribution Engine v2 — FastAPI REST API Layer

Provides:
- Ethereum address lookup
- Live Etherscan transaction fetching
- ETH transaction tracing
- ERC-20 token transfer tracing
- Internal transaction tracing
- Multi-hop BFS graph construction
- Local registry attribution
- Etherscan metadata attribution
- Evidence-based risk scoring
- Behavioral pattern detection
- Forensic report generation
"""

import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================
# PATH CONFIGURATION
# ============================================================

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import eth_txs
from pattern_detector import PatternDetector
from report_generator import ReportGenerator

# ============================================================
# DATA FILES
# ============================================================

REGISTRY_FILE = os.path.join(PROJECT_ROOT, "address_registry.json")

TRANSACTION_FILE = os.path.join(PROJECT_ROOT, "transaction.json")

TOKEN_TRANSFER_FILE = os.path.join(PROJECT_ROOT, "token_transfers.json")

INTERNAL_TRANSACTION_FILE = os.path.join(PROJECT_ROOT, "internal_transactions.json")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Crypto Attribution Engine API v2",
    description=(
        "Forensic transaction tracing, entity attribution, "
        "evidence-based risk scoring and behavioral pattern analysis."
    ),
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SERVICES
# ============================================================

pattern_detector = PatternDetector()
report_generator = ReportGenerator()


# ============================================================
# REQUEST MODELS
# ============================================================


class TraceRequest(BaseModel):
    target_address: str = Field(
        ..., json_schema_extra={"example": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
    )

    max_hops: int = Field(default=2, ge=1, le=5)

    # IMPORTANT:
    # Live Etherscan is now the default.
    use_etherscan: bool = Field(
        default=True,
        description="Use live Etherscan blockchain data when API key is available.",
    )


class ReportRequest(BaseModel):
    target_address: str = Field(...)

    trace_results: Dict[str, Any] = Field(...)

    patterns: Optional[Dict[str, Any]] = None

    case_id: Optional[str] = None

    network: str = Field(default="Ethereum Mainnet")


# ============================================================
# ROOT
# ============================================================


@app.get("/")
def read_root():
    return {
        "status": "online",
        "engine": "Crypto Attribution Engine v2",
        "version": "2.0.0",
        "supported_chain": "Ethereum",
        "live_etherscan_available": bool(os.getenv("ETHERSCAN_API_KEY", "")),
        "docs_url": "/docs",
    }


# ============================================================
# ADDRESS LOOKUP
# ============================================================


@app.get("/api/v2/address/{address}")
def lookup_address(address: str):
    """
    Look up attribution intelligence for a single Ethereum address.

    Sources:
    1. Local address registry
    2. Etherscan metadata
    """

    address = address.strip().lower()

    if not eth_txs.is_valid_eth_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")

    # --------------------------------------------------------
    # Load local registry
    # --------------------------------------------------------

    registry = eth_txs.load_address_registry(REGISTRY_FILE)

    registry_attr = eth_txs.attribute_address(address, registry)

    # --------------------------------------------------------
    # Etherscan metadata
    # --------------------------------------------------------

    api_key = os.getenv("ETHERSCAN_API_KEY", "")

    if api_key:
        try:
            etherscan_meta = eth_txs.fetch_address_metadata_from_etherscan(
                address, api_key
            )
        except Exception as exc:
            etherscan_meta = {
                "entity_type": "Unknown",
                "entity_name": "Unknown",
                "source": "etherscan_error",
                "confidence": 0.0,
                "evidence": str(exc),
            }
    else:
        etherscan_meta = {
            "entity_type": "Unknown",
            "entity_name": "Unknown",
            "source": "no_api_key",
            "confidence": 0.0,
        }

    # --------------------------------------------------------
    # Combine attribution sources
    # --------------------------------------------------------

    combined = eth_txs.combine_attribution_sources(address, registry, etherscan_meta)

    risk_data = eth_txs.calculate_evidence_risk(combined, hops=0)

    return {"address": address, "attribution": combined, "risk": risk_data}


# ============================================================
# DEMO DATA
# ============================================================

DEMO_TRANSFERS = [
    {
        "hash": "0xa1b2c3d4e5f67890",
        "from_address": "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
        "to_address": "0x1111111111111111111111111111111111111111",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 45.50,
        "timestamp": 1725380000,
        "is_error": "0",
    },
    {
        "hash": "0xb2c3d4e5f67890a1",
        "from_address": "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
        "to_address": "0x2222222222222222222222222222222222222222",
        "asset_type": "ERC20",
        "asset_contract": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "symbol": "USDT",
        "amount": 10000.00,
        "timestamp": 1725380500,
        "is_error": "0",
    },
    {
        "hash": "0xc3d4e5f67890a1b2",
        "from_address": "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
        "to_address": "0x3333333333333333333333333333333333333333",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 12.00,
        "timestamp": 1725381000,
        "is_error": "0",
    },
    {
        "hash": "0xd4e5f67890a1b2c3",
        "from_address": "0x1111111111111111111111111111111111111111",
        "to_address": "0x4444444444444444444444444444444444444444",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 45.00,
        "timestamp": 1725381200,
        "is_error": "0",
    },
    {
        "hash": "0xe5f67890a1b2c3d4",
        "from_address": "0x2222222222222222222222222222222222222222",
        "to_address": "0x5555555555555555555555555555555555555555",
        "asset_type": "ERC20",
        "asset_contract": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "symbol": "USDT",
        "amount": 9950.00,
        "timestamp": 1725381800,
        "is_error": "0",
    },
    {
        "hash": "0xf67890a1b2c3d4e5",
        "from_address": "0x4444444444444444444444444444444444444444",
        "to_address": "0x6666666666666666666666666666666666666666",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 44.20,
        "timestamp": 1725382500,
        "is_error": "0",
    },
]


# ============================================================
# TRACE ENDPOINT
# ============================================================


@app.post("/api/v2/trace")
def trace_address(req: TraceRequest):
    """
    Execute a multi-hop blockchain trace.

    Live mode:
        - Etherscan ETH transactions
        - ERC-20 transfers
        - Internal transactions
        - Multi-hop BFS
        - Etherscan address attribution
        - Local registry attribution

    Local mode:
        - Local transaction datasets
        - Synthetic demo network
    """

    address = req.target_address.strip().lower()

    # --------------------------------------------------------
    # Validate address
    # --------------------------------------------------------

    if not eth_txs.is_valid_eth_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")

    # --------------------------------------------------------
    # Load registry
    # --------------------------------------------------------

    registry = eth_txs.load_address_registry(REGISTRY_FILE)

    # --------------------------------------------------------
    # Determine live mode
    # --------------------------------------------------------

    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")

    use_live = req.use_etherscan and bool(etherscan_key)

    print("TRACE ADDRESS:", address)
    print("USE ETHERSCAN:", req.use_etherscan)
    print("API KEY CONFIGURED:", bool(etherscan_key))
    print("USE LIVE:", use_live)

    addresses_fetched = 0
    transactions_fetched = 0
    hops_processed = 0

    MAX_ADDRESS_FETCH = 50

    # ========================================================
    # LIVE MODE
    # ========================================================

    try:
        if use_live:
            fetched_norm = set()

            fetch_queue = [(address, 0)]

            all_transfers = []

            while fetch_queue and hops_processed < req.max_hops:
                hop_size = len(fetch_queue)

                next_hop_receivers = set()

                for _ in range(hop_size):
                    current, hop_level = fetch_queue.pop(0)

                    cur_norm = eth_txs.normalize_eth_address(current)

                    if cur_norm in fetched_norm:
                        continue

                    if addresses_fetched >= MAX_ADDRESS_FETCH:
                        break

                    fetched_norm.add(cur_norm)

                    addresses_fetched += 1

                    # ------------------------------------------------
                    # 1. Native ETH transactions
                    # ------------------------------------------------

                    try:
                        eth_data = eth_txs.fetch_transactions_from_etherscan(
                            current, TRANSACTION_FILE
                        )

                    except Exception as exc:
                        print(
                            f"[trace] ETH txlist failed for {current}: {exc}",
                            file=sys.stderr,
                        )
                        eth_data = []

                    # ------------------------------------------------
                    # 2. ERC-20 transfers
                    # ------------------------------------------------

                    try:
                        erc20_data = eth_txs.fetch_erc20_token_transfers(
                            current, TOKEN_TRANSFER_FILE
                        )

                    except Exception as exc:
                        print(
                            f"[trace] ERC-20 tokentx failed for {current}: {exc}",
                            file=sys.stderr,
                        )
                        erc20_data = []

                    # ------------------------------------------------
                    # 3. Internal transactions
                    # ------------------------------------------------

                    try:
                        internal_data = eth_txs.fetch_internal_transactions(
                            current, INTERNAL_TRANSACTION_FILE
                        )

                    except Exception as exc:
                        print(
                            f"[trace] internal txlistinternal failed for {current}: {exc}",
                            file=sys.stderr,
                        )
                        internal_data = []

                    # ------------------------------------------------
                    # 4. Normalize all transaction types
                    # ------------------------------------------------

                    normalized = eth_txs.normalize_all_transfers(
                        eth_data, erc20_data, internal_data
                    )

                    all_transfers.extend(normalized)

                    transactions_fetched += len(normalized)

                    # ------------------------------------------------
                    # 5. Discover outbound addresses
                    # ------------------------------------------------

                    for tx in normalized:
                        to_addr = tx.get("to_address") or ""

                        if not eth_txs.is_valid_eth_address(to_addr):
                            continue

                        to_norm = eth_txs.normalize_eth_address(to_addr)

                        if to_norm not in fetched_norm and to_norm != cur_norm:
                            next_hop_receivers.add(to_addr)

                # Add next hop addresses

                for receiver in next_hop_receivers:
                    fetch_queue.append((receiver, hops_processed + 1))

                hops_processed += 1

            # --------------------------------------------------------
            # Build graph
            # --------------------------------------------------------

            graph = eth_txs.build_unified_graph(all_transfers)

            # --------------------------------------------------------
            # BFS trace
            # --------------------------------------------------------

            trace_results = eth_txs.analyze_trace(
                address, graph, registry, max_hops=req.max_hops
            )

        # ========================================================
        # LOCAL MODE
        # ========================================================

        else:
            if address == "0x71c7656ec7ab88b098defb751b7401b5f6d8976f":
                transfers = DEMO_TRANSFERS

            else:
                tx_data = (
                    eth_txs.load_transactions(TRANSACTION_FILE)
                    if os.path.exists(TRANSACTION_FILE)
                    else []
                )

                erc20_data = (
                    eth_txs.load_transactions(TOKEN_TRANSFER_FILE)
                    if os.path.exists(TOKEN_TRANSFER_FILE)
                    else []
                )

                internal_data = (
                    eth_txs.load_transactions(INTERNAL_TRANSACTION_FILE)
                    if os.path.exists(INTERNAL_TRANSACTION_FILE)
                    else []
                )

                transfers = eth_txs.normalize_all_transfers(
                    tx_data, erc20_data, internal_data
                )

            graph = eth_txs.build_unified_graph(transfers)

            trace_results = eth_txs.analyze_trace(
                address, graph, registry, max_hops=req.max_hops
            )

        # ========================================================
        # LIVE ADDRESS ATTRIBUTION
        # ========================================================

        discovered = trace_results.get("discovered", [])

        # For live mode, ask Etherscan about every discovered
        # address so real service labels can be incorporated.

        if use_live and etherscan_key:
            for discovered_addr in discovered:
                try:
                    etherscan_meta = eth_txs.fetch_address_metadata_from_etherscan(
                        discovered_addr
                    )

                    combined = eth_txs.combine_attribution_sources(
                        discovered_addr, registry, etherscan_meta
                    )

                    # Replace attribution for this address

                    if "attribution" not in trace_results:
                        trace_results["attribution"] = {}

                    existing = trace_results["attribution"].get(discovered_addr, {})

                    # Preserve hop distance from original trace

                    hop_distance = existing.get("hop_distance")

                    combined["hop_distance"] = (
                        hop_distance if hop_distance is not None else 0
                    )

                    trace_results["attribution"][discovered_addr] = combined

                except Exception:
                    # Never allow one metadata failure to
                    # destroy the entire investigation.
                    continue

        # ========================================================
        # BUILD DISCOVERED ADDRESS STRUCTURE
        # ========================================================

        discovered_addresses = []

        for addr in discovered:
            info = trace_results.get("attribution", {}).get(addr, {})

            hop = info.get("hop_distance")

            if hop is None and addr in trace_results.get("paths", {}):
                hop = trace_results["paths"][addr][2]

            sources = []

            if info.get("source"):
                sources.append(info["source"])

            reasons = []

            if info.get("risk_evidence"):
                reasons.append(info["risk_evidence"])

            discovered_addresses.append(
                {
                    "address": addr,
                    "entity": info.get("entity_name", "Unknown"),
                    "entity_type": info.get("entity_type", "Unknown"),
                    "confidence": float(info.get("confidence", 0.0) or 0.0),
                    "sources": sources,
                    "hop_distance": (hop if hop is not None else 0),
                    "evidence": info.get("evidence", ""),
                    "risk": {
                        "score": float(info.get("risk_score", 0.0) or 0.0),
                        "risk_level": info.get("risk_level", "Low"),
                        "reasons": reasons,
                    },
                }
            )

        trace_results["discovered_addresses"] = discovered_addresses

        # ========================================================
        # FILTER GRAPH TO DISCOVERED TRACE NODES
        # ========================================================

        discovered_norm_set = {
            eth_txs.normalize_eth_address(addr) for addr in discovered
        }

        filtered_graph = {}

        for edge_key, tx_list in graph.items():
            parts = edge_key.split("->")

            if len(parts) != 2:
                continue

            source_norm = eth_txs.normalize_eth_address(parts[0])

            destination_norm = eth_txs.normalize_eth_address(parts[1])

            if (
                source_norm in discovered_norm_set
                and destination_norm in discovered_norm_set
            ):
                filtered_graph[edge_key] = tx_list

        # ========================================================
        # BEHAVIORAL PATTERNS
        # ========================================================

        patterns = pattern_detector.detect_all_patterns(filtered_graph, trace_results)

        # ========================================================
        # REPORT
        # ========================================================

        json_report = report_generator.generate_json_report(
            address, trace_results, patterns
        )

        # ========================================================
        # RESPONSE
        # ========================================================

        return {
            "target_address": address,
            "max_hops": req.max_hops,
            "live_data": use_live,
            "data_mode": ("Etherscan Live" if use_live else "Offline / Local"),
            "live_data_stats": {
                "addresses_fetched": addresses_fetched,
                "transactions_fetched": transactions_fetched,
                "hops_processed": hops_processed,
                "address_limit_reached": (
                    addresses_fetched >= MAX_ADDRESS_FETCH if use_live else False
                ),
            },
            "graph": filtered_graph,
            "trace_results": trace_results,
            "patterns": patterns,
            "report_summary": json_report["investigation_summary"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=(f"Trace execution failed: {str(exc)}")
        )


# ============================================================
# REPORT ENDPOINT
# ============================================================


@app.post("/api/v2/report")
def generate_report(req: ReportRequest):
    """
    Generate structured JSON and Markdown
    forensic investigation reports.
    """

    json_rep = report_generator.generate_json_report(
        req.target_address, req.trace_results, req.patterns, req.case_id, req.network
    )

    md_rep = report_generator.generate_markdown_report(
        req.target_address, req.trace_results, req.patterns, req.case_id, req.network
    )

    return {"json_report": json_rep, "markdown_report": md_rep}


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
