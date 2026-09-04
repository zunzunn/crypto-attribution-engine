"""
Crypto Attribution Engine v2 — Investigation Report Generator (Step 19)

Generates structured JSON and Markdown investigation reports summarizing:
- Case details & target address
- Trace graph analysis & hop metrics
- Address attribution & entity evidence
- Evidence-based risk scoring
- Behavioral pattern analysis (Fan-Out, Fan-In, Rapid Hopping, Layering)
- Formal investigative disclaimers
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional


class ReportGenerator:
    def __init__(self, tool_version: str = "v2.0.0"):
        self.tool_version = tool_version

    def generate_json_report(
        self,
        target_address: str,
        trace_results: Dict[str, Any],
        patterns: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None,
        network: str = "Ethereum Mainnet"
    ) -> Dict[str, Any]:
        """
        Builds a canonical structured JSON investigation report object.
        """
        if not case_id:
            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        discovered_nodes = trace_results.get("discovered_addresses", [])
        if not discovered_nodes and "attribution" in trace_results:
            attribution = trace_results.get("attribution", {})
            paths = trace_results.get("paths", {})
            discovered_nodes = []
            for addr in trace_results.get("discovered", list(attribution.keys())):
                info = attribution.get(addr, {})
                hop = info.get("hop_distance")
                if hop is None and addr in paths:
                    hop = paths[addr][2]
                discovered_nodes.append({
                    "address": addr,
                    "entity": info.get("entity_name", "Unknown"),
                    "entity_type": info.get("entity_type", "Unknown"),
                    "confidence": info.get("confidence", 0.0),
                    "sources": [info.get("source")] if info.get("source") else [],
                    "hop_distance": hop if hop is not None else 0,
                    "evidence": info.get("evidence", ""),
                    "risk": {
                        "score": info.get("risk_score", 0),
                        "risk_level": info.get("risk_level", "Low"),
                        "reasons": [info.get("risk_evidence")] if info.get("risk_evidence") else []
                    }
                })
        max_hop = 0
        highest_risk = 0.0
        highest_risk_level = "Low"
        attributed_count = 0

        entities = []
        evidence_chain = []

        risk_rank = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

        for node in discovered_nodes:
            hop = node.get("hop_distance", 0)
            if hop > max_hop:
                max_hop = hop

            risk_obj = node.get("risk", {})
            score = float(risk_obj.get("score", 0))
            level = risk_obj.get("risk_level", "Low")

            if score > highest_risk:
                highest_risk = score
            if risk_rank.get(level, 0) > risk_rank.get(highest_risk_level, 0):
                highest_risk_level = level

            entity_name = node.get("entity", "Unknown")
            if entity_name != "Unknown":
                attributed_count += 1
                entities.append({
                    "address": node.get("address"),
                    "entity": entity_name,
                    "entity_type": node.get("entity_type"),
                    "confidence": node.get("confidence"),
                    "sources": node.get("sources"),
                    "hop_distance": hop,
                    "risk_score": score,
                    "risk_level": level,
                    "risk_reasons": risk_obj.get("reasons", [])
                })

            node_ev = node.get("evidence")
            if node_ev:
                evidence_chain.append({
                    "address": node.get("address"),
                    "evidence": node_ev
                })

        pattern_summary = patterns.get("summary", {}) if patterns else {}

        report = {
            "case_metadata": {
                "case_id": case_id,
                "target_address": target_address,
                "network": network,
                "generated_at": timestamp_iso,
                "engine_version": self.tool_version
            },
            "investigation_summary": {
                "total_addresses_traced": len(discovered_nodes),
                "maximum_hop_distance": max_hop,
                "attributed_entities_count": attributed_count,
                "highest_risk_score": highest_risk,
                "highest_risk_level": highest_risk_level,
                "patterns_detected_count": pattern_summary.get("total_patterns_detected", 0)
            },
            "attributed_entities": entities,
            "detected_behavioral_patterns": patterns or {},
            "evidence_chain": evidence_chain,
            "disclaimer": (
                "This document is an investigative risk and evidence summary produced by the Crypto Attribution Engine. "
                "Attribution scores reflect probabilistic and evidence-backed indicators. "
                "Risk levels represent investigative priority and do NOT constitute autonomous legal proof of criminal liability."
            )
        }
        return report

    def generate_markdown_report(
        self,
        target_address: str,
        trace_results: Dict[str, Any],
        patterns: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None,
        network: str = "Ethereum Mainnet"
    ) -> str:
        """
        Renders the investigation report as a clean Markdown document.
        """
        json_report = self.generate_json_report(
            target_address, trace_results, patterns, case_id, network
        )
        meta = json_report["case_metadata"]
        summary = json_report["investigation_summary"]
        entities = json_report["attributed_entities"]
        pat_data = json_report["detected_behavioral_patterns"]

        md_lines = [
            f"# Crypto Attribution & Forensic Investigation Report",
            f"",
            f"**Case ID:** `{meta['case_id']}`  ",
            f"**Target Address:** `{meta['target_address']}`  ",
            f"**Blockchain Network:** {meta['network']}  ",
            f"**Report Generated:** {meta['generated_at']}  ",
            f"**Engine Version:** {meta['engine_version']}  ",
            f"",
            f"---",
            f"",
            f"## 1. Executive Summary",
            f"",
            f"- **Addresses Traced:** {summary['total_addresses_traced']}",
            f"- **Max Hop Depth:** {summary['maximum_hop_distance']}",
            f"- **Attributed Entities Identified:** {summary['attributed_entities_count']}",
            f"- **Peak Risk Level:** **{summary['highest_risk_level']}** (Score: `{summary['highest_risk_score']:.1f}/100`)",
            f"- **Behavioral Patterns Detected:** {summary['patterns_detected_count']}",
            f"",
            f"---",
            f"",
            f"## 2. Attributed Entities & Risk Breakdown",
            f""
        ]

        if not entities:
            md_lines.append("_No known services or entities attributed along the traced paths._\n")
        else:
            md_lines.append("| Address | Entity Name | Type | Confidence | Hop | Risk Score | Risk Level |")
            md_lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for e in entities:
                md_lines.append(
                    f"| `{e['address'][:10]}...{e['address'][-6:]}` | {e['entity']} | {e['entity_type']} | {e['confidence']} | {e['hop_distance']} | {e['risk_score']:.1f} | **{e['risk_level']}** |"
                )
            md_lines.append("\n")

        md_lines.extend([
            f"## 3. Detected Obfuscation & Behavioral Patterns",
            f""
        ])

        if not pat_data or pat_data.get("summary", {}).get("total_patterns_detected", 0) == 0:
            md_lines.append("_No specific obfuscation patterns (Splitting, Consolidation, Rapid Hopping) detected._\n")
        else:
            if pat_data.get("fan_out_events"):
                md_lines.append("### 3.1 Fan-Out (Splitting) Events")
                for ev in pat_data["fan_out_events"]:
                    md_lines.append(f"- **Address:** `{ev['address']}` split funds across **{ev['recipient_count']}** distinct recipients.")
                md_lines.append("")

            if pat_data.get("fan_in_events"):
                md_lines.append("### 3.2 Fan-In (Consolidation) Events")
                for ev in pat_data["fan_in_events"]:
                    md_lines.append(f"- **Address:** `{ev['address']}` consolidated funds from **{ev['sender_count']}** senders.")
                md_lines.append("")

            if pat_data.get("rapid_hopping_events"):
                md_lines.append("### 3.3 Rapid Wallet Hopping Events")
                for ev in pat_data["rapid_hopping_events"]:
                    md_lines.append(f"- **Intermediate Wallet:** `{ev['intermediate_address']}` transferred funds to `{ev['hop_2_to']}` within **{int(ev['time_delta_seconds'])} seconds**.")
                md_lines.append("")

            if pat_data.get("layering_events"):
                md_lines.append("### 3.4 Multi-Hop Layering Events")
                for ev in pat_data["layering_events"]:
                    md_lines.append(f"- **Layering Depth:** Maximum trace depth reached **{ev['max_hop_depth']} hops**.")
                md_lines.append("")

        md_lines.extend([
            f"---",
            f"",
            f"## 4. Legal & Investigative Disclaimer",
            f"",
            f"> {json_report['disclaimer']}",
            f""
        ])

        return "\n".join(md_lines)


# --- Unit Tests ---
def test_report_generator():
    generator = ReportGenerator()
    mock_trace = {
        "discovered_addresses": [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "entity": "KnownMixer",
                "entity_type": "Mixer",
                "confidence": 1.0,
                "sources": ["Local Registry"],
                "hop_distance": 2,
                "evidence": "Known Mixer in local registry",
                "risk": {
                    "score": 40.0,
                    "risk_level": "Medium",
                    "reasons": ["Known Mixer attribution"]
                }
            }
        ]
    }
    mock_patterns = {
        "summary": {"total_patterns_detected": 1, "has_rapid_hopping": True},
        "rapid_hopping_events": [
            {
                "intermediate_address": "0x2222222222222222222222222222222222222222",
                "hop_2_to": "0x3333333333333333333333333333333333333333",
                "time_delta_seconds": 120
            }
        ]
    }

    json_rep = generator.generate_json_report("0x1111111111111111111111111111111111111111", mock_trace, mock_patterns)
    assert json_rep["investigation_summary"]["total_addresses_traced"] == 1
    assert json_rep["investigation_summary"]["attributed_entities_count"] == 1
    assert json_rep["investigation_summary"]["highest_risk_score"] == 40.0

    md_rep = generator.generate_markdown_report("0x1111111111111111111111111111111111111111", mock_trace, mock_patterns)
    assert "# Crypto Attribution & Forensic Investigation Report" in md_rep
    assert "KnownMixer" in md_rep
    print("test_report_generator passed cleanly!")


if __name__ == "__main__":
    test_report_generator()
