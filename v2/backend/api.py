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
    
    try:
        # Load registry (local synthetic registry always available)
        registry = eth_txs.load_address_registry('address_registry.json')
        
        if use_live:
            # --- BOUNDED MULTI-HOP LIVE FETCH PHASE ---
            # Track fetched normalized addresses to avoid duplicate API calls
            fetched_norm = {eth_txs.normalize_eth_address(address)}
            # Queue of addresses whose transactions still need to be fetched, ordered by hop
            fetch_queue = [address]
            # Accumulate normalized transfers per address
            all_normalized = {}  # address -> normalized dict
            # Build graph incrementally; keys are "FROM->TO"
            graph = {}
            # Remaining hops to process
            remaining_hops = req.max_hops
            # Process up to max_hops batches
            while fetch_queue and remaining_hops > 0:
                current = fetch_queue.pop(0)
                cur_norm = eth_txs.normalize_eth_address(current)
                # Skip if already fetched (including the target initially)
                if cur_norm in fetched_norm and current != address:
                    continue
                fetched_norm.add(cur_norm)
                # Fetch native ETH transactions for current address
                try:
                    eth_txs_data = eth_txs.fetch_transactions_from_etherscan(current, "transaction.json")
                except Exception:
                    eth_txs_data = []
                # Fetch ERC-20 token transfers
                try:
                    erc20_txs = eth_txs.fetch_erc20_token_transfers(current, "token_transfers.json")
                except Exception:
                    erc20_txs = []
                # Fetch internal transactions if Etherscan key available
                if etherscan_key:
                    try:
                        internal_txs = eth_txs.fetch_internal_transactions(current, "internal_transactions.json")
                    except Exception:
                        internal_txs = []
                else:
                    internal_txs = []
                # Normalize into consistent format
                normalized = eth_txs.normalize_all_transfers(eth_txs_data, erc20_txs, internal_txs)
                all_normalized[current] = normalized
                # Add edges to graph (key format "FROM->TO")
                for tx in normalized.get('eth', []):
                    # normalized may contain a dict with 'eth' key listing eth tx dicts
                    f = tx.get('from') or tx.get('from_address') or ''
                    t = tx.get('to') or tx.get('to_address') or ''
                    if f and t:
                        edge_key = f"{eth_txs.normalize_eth_address(f)}->{eth_txs.normalize_eth_address(t)}"
                        graph.setdefault(edge_key, []).append({
                            "hash": tx.get("hash", ""),
                            "value_eth": tx.get("value_eth", 0),
                            "timestamp": tx.get("timestamp", 0),
                        })
                for tx in normalized.get('erc20', []):
                    f = tx.get('from') or tx.get('from_address') or ''
                    t = tx.get('to') or tx.get('to_address') or ''
                    if f and t:
                        edge_key = f"{eth_txs.normalize_eth_address(f)}->{eth_txs.normalize_eth_address(t)}"
                        graph.setdefault(edge_key, []).append({
                            "hash": tx.get("hash", ""),
                            "value_eth": tx.get("value_eth", 0),
                            "timestamp": tx.get("timestamp", 0),
                        })
                for tx in normalized.get('internal', []):
                    f = tx.get('from') or tx.get('from_address') or ''
                    t = tx.get('to') or tx.get('to_address') or ''
                    if f and t:
                        edge_key = f"{eth_txs.normalize_eth_address(f)}->{eth_txs.normalize_eth_address(t)}"
                        graph.setdefault(edge_key, []).append({
                            "hash": tx.get("hash", ""),
                            "value_eth": tx.get("value_eth", 0),
                            "timestamp": tx.get("timestamp", 0),
                        })
                # Discover new receivers to fetch in the next hop
                # Collect all unique receiver normalized addresses from added edges
                new_addrs = set()
                for edge_key, txs in graph.items():
                    parts = edge_key.split("->")
                    if len(parts) == 2:
                        receiver_norm = parts[1]
                        if receiver_norm not in fetched_norm:
                            new_addrs.add(receiver_norm)
                # Add newly discovered normalized addresses to queue for next iteration
                for a in new_addrs:
                    # map back to original case; we store the first seen original address
                    # use a simple dict later if needed; for queue we can use normalized form
                    fetch_queue.append(a)
                remaining_hops -= 1
            
            # After building the augmented graph, run BFS trace and risk analysis
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