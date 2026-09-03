"""
Crypto Attribution Engine v2 — Behavioral Pattern Detector (Step 18)

Analyzes unified transaction graphs and trace paths to identify observable
crypto asset obfuscation and flow patterns:
- Fan-Out (Splitting): Single address disbursing funds to multiple recipients
- Fan-In (Consolidation): Multiple sender addresses aggregating funds into one address
- Rapid Wallet Hopping: Sequential transfers occurring within short time intervals
- Multi-Hop Layering: Extended linear transfer chains across multiple hops
"""

import time
from collections import defaultdict
from typing import Dict, List, Any, Optional

DEFAULT_TIME_THRESHOLD_SECONDS = 900  # 15 minutes
DEFAULT_MIN_FAN_DEGREE = 3            # minimum recipients/senders to classify as fan event


class PatternDetector:
    def __init__(self, time_threshold_seconds: int = DEFAULT_TIME_THRESHOLD_SECONDS, min_fan_degree: int = DEFAULT_MIN_FAN_DEGREE):
        self.time_threshold_seconds = time_threshold_seconds
        self.min_fan_degree = min_fan_degree

    def detect_fan_out(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects addresses sending funds to multiple distinct recipients (Splitting).
        """
        fan_out_events = []
        for source_addr, outgoing_txs in graph.items():
            if not outgoing_txs:
                continue

            recipients = defaultdict(list)
            for tx in outgoing_txs:
                to_addr = tx.get("to")
                if to_addr and to_addr.lower() != source_addr.lower():
                    recipients[to_addr.lower()].append(tx)

            if len(recipients) >= self.min_fan_degree:
                total_outbound_val = sum(
                    float(tx.get("amount", 0) or 0) 
                    for tx_list in recipients.values() 
                    for tx in tx_list
                )
                fan_out_events.append({
                    "address": source_addr,
                    "recipient_count": len(recipients),
                    "recipients": list(recipients.keys()),
                    "total_outbound_amount": total_outbound_val,
                    "transaction_count": sum(len(v) for v in recipients.values()),
                    "pattern_type": "FAN_OUT_SPLITTING",
                    "risk_signal": "HIGH_FAN_OUT",
                    "description": f"Address split funds out to {len(recipients)} distinct recipients."
                })
        return fan_out_events

    def detect_fan_in(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects addresses receiving funds from multiple distinct senders (Consolidation).
        """
        incoming_map = defaultdict(list)
        for source_addr, outgoing_txs in graph.items():
            for tx in outgoing_txs:
                to_addr = tx.get("to")
                if to_addr:
                    incoming_map[to_addr.lower()].append({
                        "from": source_addr.lower(),
                        "amount": tx.get("amount", 0),
                        "hash": tx.get("hash"),
                        "timestamp": tx.get("timestamp")
                    })

        fan_in_events = []
        for target_addr, incoming_txs in incoming_map.items():
            senders = defaultdict(list)
            for tx in incoming_txs:
                senders[tx["from"]].append(tx)

            if len(senders) >= self.min_fan_degree:
                total_inbound_val = sum(
                    float(tx.get("amount", 0) or 0) 
                    for tx_list in senders.values() 
                    for tx in tx_list
                )
                fan_in_events.append({
                    "address": target_addr,
                    "sender_count": len(senders),
                    "senders": list(senders.keys()),
                    "total_inbound_amount": total_inbound_val,
                    "transaction_count": sum(len(v) for v in senders.values()),
                    "pattern_type": "FAN_IN_CONSOLIDATION",
                    "risk_signal": "HIGH_FAN_IN",
                    "description": f"Address consolidated funds from {len(senders)} distinct senders."
                })
        return fan_in_events

    def detect_rapid_hopping(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects sequential transactions along connected paths where timestamp difference
        between hops is under the threshold.
        """
        rapid_hops = []
        for source_addr, outgoing_txs in graph.items():
            for tx in outgoing_txs:
                next_addr = tx.get("to")
                tx1_time = tx.get("timestamp")
                if not next_addr or tx1_time is None:
                    continue

                next_outgoing = graph.get(next_addr.lower(), [])
                for next_tx in next_outgoing:
                    tx2_time = next_tx.get("timestamp")
                    if tx2_time is None:
                        continue

                    try:
                        t1 = float(tx1_time)
                        t2 = float(tx2_time)
                        delta = t2 - t1
                        if 0 <= delta <= self.time_threshold_seconds:
                            rapid_hops.append({
                                "hop_1_from": source_addr,
                                "intermediate_address": next_addr,
                                "hop_2_to": next_tx.get("to"),
                                "time_delta_seconds": delta,
                                "tx1_hash": tx.get("hash"),
                                "tx2_hash": next_tx.get("hash"),
                                "pattern_type": "RAPID_WALLET_HOPPING",
                                "description": f"Funds moved through {next_addr} to {next_tx.get('to')} in {int(delta)}s (< {self.time_threshold_seconds}s)."
                            })
                    except (ValueError, TypeError):
                        continue
        return rapid_hops

    def detect_layering(self, trace_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Detects multi-hop layering paths from trace results.
        """
        layering_events = []
        if not trace_results:
            return layering_events

        discovered_nodes = trace_results.get("discovered_addresses", [])
        max_hop = 0
        deep_addresses = []

        for node in discovered_nodes:
            hop = node.get("hop_distance", 0)
            if hop >= 3:
                deep_addresses.append(node)
                if hop > max_hop:
                    max_hop = hop

        if deep_addresses:
            layering_events.append({
                "max_hop_depth": max_hop,
                "deep_address_count": len(deep_addresses),
                "addresses": [n.get("address") for n in deep_addresses],
                "pattern_type": "MULTI_HOP_LAYERING",
                "description": f"Trace extends through {max_hop} sequential hops across {len(deep_addresses)} addresses, indicating complex layering."
            })
        return layering_events

    def detect_all_patterns(self, graph: Dict[str, Any], trace_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs all pattern detectors and aggregates findings into a unified pattern summary.
        """
        fan_out = self.detect_fan_out(graph)
        fan_in = self.detect_fan_in(graph)
        rapid_hopping = self.detect_rapid_hopping(graph)
        layering = self.detect_layering(trace_results)

        total_patterns = len(fan_out) + len(fan_in) + len(rapid_hopping) + len(layering)

        summary = {
            "total_patterns_detected": total_patterns,
            "has_fan_out": len(fan_out) > 0,
            "has_fan_in": len(fan_in) > 0,
            "has_rapid_hopping": len(rapid_hopping) > 0,
            "has_layering": len(layering) > 0,
        }

        return {
            "summary": summary,
            "fan_out_events": fan_out,
            "fan_in_events": fan_in,
            "rapid_hopping_events": rapid_hopping,
            "layering_events": layering
        }


# --- Unit Tests ---
def test_detect_fan_out():
    graph = {
        "0xsource": [
            {"to": "0xrec1", "amount": "1.0", "hash": "0xh1"},
            {"to": "0xrec2", "amount": "2.0", "hash": "0xh2"},
            {"to": "0xrec3", "amount": "3.0", "hash": "0xh3"},
        ]
    }
    detector = PatternDetector(min_fan_degree=3)
    res = detector.detect_fan_out(graph)
    assert len(res) == 1
    assert res[0]["pattern_type"] == "FAN_OUT_SPLITTING"
    assert res[0]["recipient_count"] == 3
    print("test_detect_fan_out passed!")


def test_detect_fan_in():
    graph = {
        "0xsender1": [{"to": "0xtarget", "amount": "1.0", "hash": "0xh1"}],
        "0xsender2": [{"to": "0xtarget", "amount": "2.0", "hash": "0xh2"}],
        "0xsender3": [{"to": "0xtarget", "amount": "3.0", "hash": "0xh3"}],
    }
    detector = PatternDetector(min_fan_degree=3)
    res = detector.detect_fan_in(graph)
    assert len(res) == 1
    assert res[0]["pattern_type"] == "FAN_IN_CONSOLIDATION"
    assert res[0]["sender_count"] == 3
    print("test_detect_fan_in passed!")


def test_detect_rapid_hopping():
    graph = {
        "0xa": [{"to": "0xb", "amount": "1.0", "timestamp": 1000, "hash": "0xh1"}],
        "0xb": [{"to": "0xc", "amount": "1.0", "timestamp": 1300, "hash": "0xh2"}]  # 300 sec delta
    }
    detector = PatternDetector(time_threshold_seconds=900)
    res = detector.detect_rapid_hopping(graph)
    assert len(res) == 1
    assert res[0]["time_delta_seconds"] == 300
    print("test_detect_rapid_hopping passed!")


def run_tests():
    test_detect_fan_out()
    test_detect_fan_in()
    test_detect_rapid_hopping()
    print("All pattern_detector tests passed cleanly!")


if __name__ == "__main__":
    run_tests()
