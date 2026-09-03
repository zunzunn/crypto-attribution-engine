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

    registry = eth_txs.load_address_registry()
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
    """
    address = req.target_address.strip()
    if not address:
        raise HTTPException(status_code=400, detail="Target address cannot be empty.")

    try:
        # Load registry
        registry = eth_txs.load_address_registry()
        
        # Load or fetch graph transactions
        # If transaction files exist in directory, build unified graph
        tx_data = eth_txs.load_transactions("transaction.json") if os.path.exists("transaction.json") else []
        erc20_data = eth_txs.load_transactions("token_transfers.json") if os.path.exists("token_transfers.json") else []
        internal_data = eth_txs.load_transactions("internal_transactions.json") if os.path.exists("internal_transactions.json") else []

        normalized = eth_txs.normalize_all_transactions(tx_data, erc20_data, internal_data)
        graph = eth_txs.build_unified_graph(normalized)

        # Run BFS Trace & Trace-level risk analysis
        trace_results = eth_txs.analyze_trace_risk(address, graph, registry, max_hops=req.max_hops)

        # Run behavioral pattern analysis
        patterns = pattern_detector.detect_all_patterns(graph, trace_results)

        # Generate report preview
        json_report = report_generator.generate_json_report(address, trace_results, patterns)

        return {
            "target_address": address,
            "max_hops": req.max_hops,
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
