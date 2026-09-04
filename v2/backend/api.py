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


@app.post("/api/v2/trace")
def trace_address(req: TraceRequest):
    """
    Execute full multi-hop BFS trace, entity attribution, evidence-based risk scoring,
    and behavioral pattern detection on a target address.
    
    When use_etherscan=true, fetches live Ethereum transaction data from Etherscan API.
    When use_etherscan=false, falls back to local transaction files if present.
    """
    address = req.target_address.strip().lower()
    if not address:
        raise HTTPException(status_code=400, detail="Target address cannot be empty.")
    
    # Validate Ethereum address format
    if not eth_txs.is_valid_eth_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")
    
    # Check for Etherscan API key if live fetching requested
    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")
    use_live = req.use_etherscan and bool(etherscan_key)
    
    if use_live:
            # --- RECRUITIVE MULTI-HOP LIVE FETCH PHASE ---
            # Safety limit: cap total distinct addresses fetched to avoid runaway API calls
            MAX_ADDRESS_FETCH = 50
            # Track fetched normalised addresses to avoid duplicate calls
            fetched_norm = {eth_txs.normalize_eth_address(address)}
            # Queue of (address, hop_level) tuples; start with target at hop 0
            fetch_queue = [(address, 0)]
            # Graph built from all fetched transactions; keys are "FROM->TO" with normalised addresses
            graph = {}
            # Statistics for the response
            addresses_fetched = 0
            transactions_fetched = 0
            hops_processed = 0

            while fetch_queue and hops_processed < req.max_hops:
                # Process all addresses queued at the current hop level
                hop_size = len(fetch_queue)
                if hop_size == 0:
                    break
                for _ in range(hop_size):
                    current, hop_level = fetch_queue.pop(0)
                    cur_norm = eth_txs.normalize_eth_address(current)
                    # Skip if already fetched (including the target at hop 0)
                    if cur_norm in fetched_norm:
                        continue
                    # Enforce total address limit
                    if addresses_fetched >= MAX_ADDRESS_FETCH:
                        break
                    fetched_norm.add(cur_norm)
                    addresses_fetched += 1

                    # Fetch native ETH transactions for current address
                    try:
                        eth_txs_data = eth_txs.fetch_transactions_from_etherscan(current, "transaction.json")
                        transactions_fetched += len(eth_txs_data) if eth_txs_data else 0
                    except Exception:
                        eth_txs_data = []
                    # Fetch ERC-20 token transfers
                    try:
                        erc20_txs = eth_txs.fetch_erc20_token_transfers(current, "token_transfers.json")
                        transactions_fetched += len(erc20_txs) if erc20_txs else 0
                    except Exception:
                        erc20_txs = []
                    # Fetch internal transactions if Etherscan key available
                    if etherscan_key:
                        try:
                            internal_txs = eth_txs.fetch_internal_transactions(current, "internal_transactions.json")
                            transactions_fetched += len(internal_txs) if internal_txs else 0
                        except Exception:
                            internal_txs = []
                    else:
                        internal_txs = []

                    # Normalize into consistent format
                    normalized = eth_txs.normalize_all_transfers(eth_txs_data, erc20_txs, internal_txs)
                    # Add edges to graph (key format "FROM->TO" using normalised addresses)
                    for tx_cat in normalized.values():
                        for tx in tx_cat:
                            f = tx.get('from') or tx.get('from_address') or ''
                            t = tx.get('to') or tx.get('to_address') or ''
                            if f and t:
                                edge_key = f"{eth_txs.normalize_eth_address(f)}->{eth_txs.normalize_eth_address(t)}"
                                graph.setdefault(edge_key, []).append({
                                    "hash": tx.get("hash", ""),
                                    "value_eth": tx.get("value_eth", 0),
                                    "timestamp": tx.get("timestamp", 0),
                                })
                    # Discover new receivers to fetch in the next hop level
                    # Collect unique normalised receiver addresses from newly added edges
                    new_receivers = set()
                    for edge_key, _ in graph.items():
                        parts = edge_key.split("->")
                        if len(parts) == 2:
                            # only consider edges where the sender normalised address matches current
                            # (simple heuristic: if receiver not yet fetched, add)
                            r_norm = parts[1]
                            if r_norm not in fetched_norm:
                                new_receivers.add(r_norm)
                    # Queue each new receiver for the next hop level (hop_level + 1)
                    for r_norm in new_receivers:
                        # Store the normalised form; original case can be recovered later if needed
                        fetch_queue.append((r_norm, hop_level + 1))
                hops_processed += 1

            # After the recursive fetch loop, run BFS trace and risk analysis on the full graph
            trace_results = eth_txs.analyze_trace(address, graph, registry, max_hops=req.max_hops)
            
        else:
            # --- LOCAL/SYNTHETIC MODE ---
            # Load existing transaction files from disk if present
            tx_data = eth_txs.load_transactions("transaction.json") if os.path.exists("transaction.json") else []
            erc20_data = eth_txs.load_transactions("token_transfers.json") if os.path.exists("token_transfers.json") else []
            internal_data = eth_txs.load_transactions("internal_transactions.json") if os.path.exists("internal_transactions.json") else []
            
            normalized = eth_txs.normalize_all_transfers(tx_data, erc20_data, internal_data)
            graph = eth_txs.build_unified_graph(normalized)
            trace_results = eth_txs.analyze_trace(address, graph, registry, max_hops=req.max_hops)
        
        # Run behavioral pattern analysis (works on any graph)
        patterns = pattern_detector.detect_all_patterns(graph, trace_results)
        
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
            "graph": graph,
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