"""
Crypto Attribution Engine v2 — FastAPI REST API Layer (Step 20)

Exposes HTTP endpoints connecting the Python attribution & tracing engine
to the investigator dashboard frontend.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import os
import sys

# Import core modules
import eth_txs
from pattern_detector import PatternDetector
from report_generator import ReportGenerator

app = FastAPI(
    title="Crypto Attribution Engine API v2",
    description="Forensic transaction tracing, entity attribution, evidence-based risk scoring & behavioral pattern analysis.",
    version="2.0.0"
)

# Enable CORS for frontend dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pattern_detector = PatternDetector()
report_generator = ReportGenerator()


class TraceRequest(BaseModel):
    target_address: str = Field(..., json_schema_extra={"example": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"})
    max_hops: int = Field(default=2, ge=1, le=5)
    use_etherscan: bool = Field(default=False, description="Fetch live Etherscan metadata if API key available")


class ReportRequest(BaseModel):
    target_address: str = Field(...)
    trace_results: Dict[str, Any] = Field(...)
    patterns: Optional[Dict[str, Any]] = None
    case_id: Optional[str] = None
    network: str = Field(default="Ethereum Mainnet")


@app.get("/")
def read_root():
    return {
        "status": "online",
        "engine": "Crypto Attribution Engine v2",
        "version": "2.0.0",
        "supported_chain": "Ethereum",
        "docs_url": "/docs"
    }


@app.get("/api/v2/address/{address}")
def lookup_address(address: str):
    """
    Look up attribution intelligence for a single address using local registry & Etherscan metadata.
    """
    if not address or len(address) < 10:
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")

    registry = eth_txs.load_address_registry('address_registry.json')
    registry_attr = eth_txs.attribute_address(address, registry)
    
    # Etherscan metadata lookup
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    etherscan_meta = eth_txs.fetch_address_metadata_from_etherscan(address, api_key) if api_key else {"entity_type": "Unknown"}

    combined = eth_txs.combine_attribution_sources(address, registry, etherscan_meta)
    risk_data = eth_txs.calculate_evidence_risk(combined, hops=0)

    return {
        "address": address,
        "attribution": combined,
        "risk": risk_data
    }


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
        "is_error": "0"
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
        "is_error": "0"
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
        "is_error": "0"
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
        "is_error": "0"
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
        "is_error": "0"
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
        "is_error": "0"
    }
]


@app.post("/api/v2/trace")
def trace_address(req: TraceRequest):
    """
    Execute full multi-hop BFS trace, entity attribution, evidence-based risk scoring,
    and behavioral pattern detection on a target address.
    
    When use_etherscan=true and ETHERSCAN_API_KEY is present, fetches live Ethereum data.
    When use_etherscan=false, uses local dataset / demo network traces.
    """
    address = req.target_address.strip().lower()
    if not address:
        raise HTTPException(status_code=400, detail="Target address cannot be empty.")
    
    # Validate Ethereum address format
    if not eth_txs.is_valid_eth_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")
    
    registry = eth_txs.load_address_registry('address_registry.json')
    
    # Check for Etherscan API key if live fetching requested
    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")
    use_live = req.use_etherscan and bool(etherscan_key)
    
    addresses_fetched = 0
    transactions_fetched = 0
    hops_processed = 0
    MAX_ADDRESS_FETCH = 50

    try:
        if use_live:
            # --- RECURSIVE MULTI-HOP LIVE FETCH PHASE ---
            fetched_norm = set()
            fetch_queue = [(address, 0)]
            all_transfers = []

            while fetch_queue and hops_processed < req.max_hops:
                hop_size = len(fetch_queue)
                if hop_size == 0:
                    break
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

                    # 1. Fetch native ETH transactions
                    try:
                        eth_txs_data = eth_txs.fetch_transactions_from_etherscan(current, "transaction.json")
                    except Exception:
                        eth_txs_data = []

                    # 2. Fetch ERC-20 token transfers
                    try:
                        erc20_txs = eth_txs.fetch_erc20_token_transfers(current, "token_transfers.json")
                    except Exception:
                        erc20_txs = []

                    # 3. Fetch internal transactions
                    try:
                        internal_txs = eth_txs.fetch_internal_transactions(current, "internal_transactions.json")
                    except Exception:
                        internal_txs = []

                    # 4. Normalize transfers
                    normalized = eth_txs.normalize_all_transfers(eth_txs_data, erc20_txs, internal_txs)
                    all_transfers.extend(normalized)
                    transactions_fetched += len(normalized)

                    # 5. Enqueue outbound recipient addresses for the next hop level
                    for tx in normalized:
                        to_addr = tx.get("to_address") or ""
                        if eth_txs.is_valid_eth_address(to_addr):
                            to_norm = eth_txs.normalize_eth_address(to_addr)
                            if to_norm not in fetched_norm and to_norm != cur_norm:
                                next_hop_receivers.add(to_addr)

                for r in next_hop_receivers:
                    fetch_queue.append((r, hops_processed + 1))

                hops_processed += 1

            graph = eth_txs.build_unified_graph(all_transfers)
            trace_results = eth_txs.analyze_trace(address, graph, registry, max_hops=req.max_hops)

        else:
            # --- LOCAL / SYNTHETIC MODE ---
            # If target address matches canonical demo address, load demo multi-hop trace
            if address == "0x71c7656ec7ab88b098defb751b7401b5f6d8976f":
                transfers = DEMO_TRANSFERS
            else:
                tx_data = eth_txs.load_transactions("transaction.json") if os.path.exists("transaction.json") else []
                erc20_data = eth_txs.load_transactions("token_transfers.json") if os.path.exists("token_transfers.json") else []
                internal_data = eth_txs.load_transactions("internal_transactions.json") if os.path.exists("internal_transactions.json") else []
                transfers = eth_txs.normalize_all_transfers(tx_data, erc20_data, internal_data)

            graph = eth_txs.build_unified_graph(transfers)
            trace_results = eth_txs.analyze_trace(address, graph, registry, max_hops=req.max_hops)

        # Build structured discovered_addresses array
        discovered_addresses = []
        for addr in trace_results.get("discovered", []):
            info = trace_results.get("attribution", {}).get(addr, {})
            hop = info.get("hop_distance")
            if hop is None and addr in trace_results.get("paths", {}):
                hop = trace_results["paths"][addr][2]
            sources = [info.get("source")] if info.get("source") else []
            reasons = [info.get("risk_evidence")] if info.get("risk_evidence") else []
            discovered_addresses.append({
                "address": addr,
                "entity": info.get("entity_name", "Unknown"),
                "entity_type": info.get("entity_type", "Unknown"),
                "confidence": float(info.get("confidence", 0.0) or 0.0),
                "sources": sources,
                "hop_distance": hop if hop is not None else 0,
                "evidence": info.get("evidence", ""),
                "risk": {
                    "score": float(info.get("risk_score", 0.0) or 0.0),
                    "risk_level": info.get("risk_level", "Low"),
                    "reasons": reasons
                }
            })
        trace_results["discovered_addresses"] = discovered_addresses

        # Scope returned graph to only include edges connecting discovered trace nodes
        discovered_norm_set = {eth_txs.normalize_eth_address(a) for a in trace_results.get("discovered", [])}
        filtered_graph = {}
        for edge_key, tx_list in graph.items():
            parts = edge_key.split("->")
            if len(parts) == 2:
                s_norm = eth_txs.normalize_eth_address(parts[0])
                d_norm = eth_txs.normalize_eth_address(parts[1])
                if s_norm in discovered_norm_set and d_norm in discovered_norm_set:
                    filtered_graph[edge_key] = tx_list

        # Run behavioral pattern analysis on filtered graph
        patterns = pattern_detector.detect_all_patterns(filtered_graph, trace_results)

        # Generate report preview
        json_report = report_generator.generate_json_report(address, trace_results, patterns)

        return {
            "target_address": address,
            "max_hops": req.max_hops,
            "live_data": use_live,
            "live_data_stats": {
                "addresses_fetched": addresses_fetched,
                "transactions_fetched": transactions_fetched,
                "hops_processed": hops_processed,
                "address_limit_reached": addresses_fetched >= MAX_ADDRESS_FETCH if use_live else False
            },
            "graph": filtered_graph,
            "trace_results": trace_results,
            "patterns": patterns,
            "report_summary": json_report["investigation_summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trace execution failed: {str(e)}")


@app.post("/api/v2/report")
def generate_report(req: ReportRequest):
    """
    Generate structured JSON and Markdown forensic reports.
    """
    json_rep = report_generator.generate_json_report(
        req.target_address, req.trace_results, req.patterns, req.case_id, req.network
    )
    md_rep = report_generator.generate_markdown_report(
        req.target_address, req.trace_results, req.patterns, req.case_id, req.network
    )

    return {
        "json_report": json_rep,
        "markdown_report": md_rep
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)