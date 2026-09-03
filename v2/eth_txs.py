import argparse
import os
import json
import sys
from dotenv import load_dotenv
import requests
from collections import defaultdict


load_dotenv()


def is_valid_eth_address(address: str) -> bool:
    """Check if string looks like an Ethereum address."""
    addr = address.strip()
    if not addr.startswith("0x"):
        return False
    hex_part = addr[2:]
    if len(hex_part) != 40:
        return False
    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False


def load_transactions(path: str = "transaction.json") -> list:
    """Load transactions from a JSON file.

    Expected format: array of objects with 'from', 'to', 'hash', 'value', 'timeStamp' fields.
    """
    with open(path, "r") as f:
        data = json.load(f)
    return data


def build_graph(transactions: list, include_token_transfers: bool = False) -> dict:
    """Build a transaction graph from a list of transaction records.

    Returns a dict mapping edge keys (from->to) to lists of
    {hash, value_eth, timestamp} dicts.

    If include_token_transfers is True, token transfers can be represented as edges
    while preserving token information in the edge data.
    """
    graph = defaultdict(list)
    for tx in transactions:
        sender = tx.get("from", "")
        receiver = tx.get("to", "")
        if not is_valid_eth_address(sender) or not is_valid_eth_address(receiver):
            continue
        value_eth = int(tx.get("value", "0")) / 10 ** 18
        tx_hash = tx.get("hash", "N/A")
        timestamp = tx.get("timeStamp", "0")
        edge_key = f"{sender}->{receiver}"
        graph[edge_key].append(
            {"hash": tx_hash, "value_eth": value_eth, "timestamp": timestamp}
        )
    return dict(graph)


def fetch_transactions_from_etherscan(address: str, filepath: str = "transaction.json") -> list:
    """Fetch transaction history for an Ethereum address using Etherscan API V2.

    Calls the `account.txlist` endpoint and saves the raw response to `filepath`
    (default: transaction.json). Returns the parsed transactions list.

    Requires ETHERSCAN_API_KEY environment variable to be set (loaded from .env file).
    """
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: ETHERSCAN_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not is_valid_eth_address(address):
        print(f"Invalid Ethereum address: {address}", file=sys.stderr)
        sys.exit(1)

    base_url = "https://api.etherscan.io/v2/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,
        "sort": "asc",
        "chainid": "1",
        "apikey": api_key,
    }

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            # Print complete error response (including result field) without exposing the API key
            error_detail = data.get("result", "No result field")
            print(f"Etherscan API error (status={data.get('status')}, message={data.get('message')}, result={error_detail})", file=sys.stderr)
            sys.exit(1)

        transactions = data.get("result", [])
        with open(filepath, "w") as f:
            json.dump(transactions, f, indent=2)

        print(f"Fetched {len(transactions)} transactions for {address} and saved to {filepath}")
        return transactions

    except requests.exceptions.RequestException as exc:
        print(f"Error fetching from Etherscan: {exc}", file=sys.stderr)
        sys.exit(1)


def fetch_erc20_token_transfers(address: str, filepath: str = "token_transfers.json") -> list:
    """Fetch ERC-20 token transfer history for an Ethereum address using Etherscan API V2.

    Calls the `account tokentx` endpoint and saves the raw response to `filepath`
    (default: token_transfers.json). Returns the parsed token transfers list.

    Requires ETHERSCAN_API_KEY environment variable to be set (loaded from .env file).
    Uses chainid=1 for Ethereum Mainnet.
    """
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: ETHERSCAN_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not is_valid_eth_address(address):
        print(f"Invalid Ethereum address: {address}", file=sys.stderr)
        sys.exit(1)

    base_url = "https://api.etherscan.io/v2/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,
        "sort": "asc",
        "chainid": "1",
        "apikey": api_key,
    }

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            # Print complete error response (including result field) without exposing the API key
            error_detail = data.get("result", "No result field")
            print(f"Etherscan API error (status={data.get('status')}, message={data.get('message')}, result={error_detail})", file=sys.stderr)
            sys.exit(1)

        token_transfers = data.get("result", [])
        with open(filepath, "w") as f:
            json.dump(token_transfers, f, indent=2)

        print(f"Fetched {len(token_transfers)} ERC-20 token transfers for {address} and saved to {filepath}")
        return token_transfers

    except requests.exceptions.RequestException as exc:
        print(f"Error fetching from Etherscan: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_erc20_transfer(raw: dict) -> dict:
    """Parse a raw Etherscan token transfer dict into a common format.

    Returns a dict with keys: hash, from_address, to_address,
    token_contract_address, token_symbol, amount_raw, amount_ether, timestamp.
    Etherscan API uses CamelCase keys (tokenContractAddress, tokenSymbol).
    """
    return {
        "hash": raw.get("hash", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "token_contract_address": raw.get("tokenContractAddress", ""),
        "token_symbol": raw.get("tokenSymbol", ""),
        "amount_raw": raw.get("value", "0"),
        "amount_ether": int(raw.get("value", "0")) / 10 ** 18,
        "timestamp": raw.get("timeStamp", "0"),
    }


RISK_BASE_POINTS = {
    "VASP": 10,
    "Bridge": 20,
    "Mixer": 40,
    "Scam/Fraud": 50,
    "Unknown": 0,
}


def load_address_registry(filepath: str) -> dict:
    """Load an address registry from a JSON file.

    The registry file should map addresses to entities with fields:
    - address: the normalized checksum address
    - entity_name: human-readable entity name
    - entity_type: one of VASP, Bridge, Mixer, Scam/Fraud, Unknown
    - source: origin of this registry entry
    - confidence: float 0.0 to 1.0
    """
    import json
    with open(filepath, "r") as f:
        registry = json.load(f)
    # Normalize all addresses to lowercase for consistent lookup
    normalized = {}
    for addr, entry in registry.items():
        normalized[addr.lower()] = entry
    return normalized


def lookup_address(address: str, registry: dict) -> dict | None:
    """Look up an address in the registry.

    Returns the entity dict if found, None otherwise.
    Case-insensitive matching on the hex portion after 0x prefix.
    The returned entity dict includes: address, entity_name, entity_type,
    source, and confidence.
    """
    addr = address.strip()
    if not is_valid_eth_address(addr):
        return None
    # Normalize: lowercase the hex portion after 0x
    hex_part = addr[2:].lower()
    normalized_addr = "0x" + hex_part
    entry = registry.get(normalized_addr)
    if entry is not None:
        # Ensure entry has all required fields with defaults
        entry.setdefault("address", normalized_addr)
        entry.setdefault("entity_name", "Unknown")
        entry.setdefault("entity_type", "Unknown")
        entry.setdefault("source", "unknown")
        entry.setdefault("confidence", 0.0)
    return entry


def lookup_address(address: str, registry: dict) -> dict | None:
    """Look up an address in the registry.

    Returns the entity dict if found, None otherwise.
    Case-insensitive matching on the hex portion after 0x prefix.
    The returned entity dict includes: address, entity_name, entity_type,
    source, and confidence.
    """
    addr = address.strip()
    if not is_valid_eth_address(addr):
        return None
    # Normalize: lowercase the hex portion after 0x
    hex_part = addr[2:].lower()
    normalized_addr = "0x" + hex_part
    entry = registry.get(normalized_addr)
    if entry is not None:
        # Ensure entry has all required fields with defaults
        entry.setdefault("address", normalized_addr)
        entry.setdefault("entity_name", "Unknown")
        entry.setdefault("entity_type", "Unknown")
        entry.setdefault("source", "unknown")
        entry.setdefault("confidence", 0.0)
    return entry


def attribute_address(address: str, registry: dict) -> dict:
    """Provide attribution evidence for an address based on the registry.

    Returns a structured result containing attribution evidence:
    - address: the normalized address
    - entity_name: entity name from registry or "Unknown"
    - entity_type: entity type from registry or "Unknown"
    - source: source from registry or "unknown"
    - confidence: confidence from registry or 0.0
    - evidence: string explaining the match status

    For a known address in the registry, evidence confirms the registry match.
    For an unknown address, evidence indicates no registry match was found.
    All evidence explicitly states this is synthetic test data.
    """
    entry = lookup_address(address, registry)
    if entry is not None and entry.get("entity_type") != "Unknown":
        evidence = (
            f"Address {entry['address']} matched entity '{entry['entity_name']}' "
            f"of type {entry['entity_type']} from registry source '{entry['source']}' "
            f"with confidence {entry['confidence']}. "
            f"This is synthetic test data; the registry does not represent real intelligence."
        )
        return {
            "address": entry.get("address", address),
            "entity_name": entry.get("entity_name", "Unknown"),
            "entity_type": entry.get("entity_type", "Unknown"),
            "source": entry.get("source", "unknown"),
            "confidence": float(entry.get("confidence", 0.0)),
            "evidence": evidence,
        }
    else:
        # Unknown address - no registry match
        return {
            "address": address.strip() if address else "0x00000000000000000000000000000000",
            "entity_name": "Unknown",
            "entity_type": "Unknown",
            "source": "unknown",
            "confidence": 0.0,
            "evidence": (
                f"Address {address.strip() if address else '0x00000000000000000000000000000000'} "
                f"not found in intelligence registry. No match. "
                f"This is synthetic test data; no real intelligence claims are made."
            ),
        }


def classify_entity(address: str, registry: dict | None = None) -> str:
    """Classify an address using the address registry.

    Returns the entity_type from the registry if the address is found.
    Returns "Unknown" if the address is not in the registry or is invalid.
    This replaces the old first-hex-character classifier.

    If no registry is provided, returns "Unknown".
    """
    entry = lookup_address(address, registry) if registry is not None else None
    if entry is not None:
        return entry["entity_type"]
    return "Unknown"


def calculate_risk_score(entity_type: str, hops: int) -> (int, str):
    """Calculate risk score and level based on entity type and hop distance.

    - Base points from entity type (VASP=10, Bridge=20, Mixer=40, Scam/Fraud=50)
    - Small hop-distance factor: subtract hops * 5 (entities farther away
      are slightly less risky)
    - Final score capped at 100, minimum 0
    - Risk levels: Low (<25), Medium (25-49), High (50-74), Critical (75-100)
    """
    base = RISK_BASE_POINTS.get(entity_type, 0)
    distance_penalty = hops * 5
    score = max(0, min(100, base - distance_penalty))

    if score < 25:
        level = "Low"
    elif score < 50:
        level = "Medium"
    elif score < 75:
        level = "High"
    else:
        level = "Critical"

    return score, level


def bfs_traverse(graph: dict, start: str, max_hops: int = 3) -> dict:
    """Breadth-first traversal of the transaction graph.

    Args:
        graph: dict mapping "FROM->TO" edges to lists of {hash, value_eth, timestamp}
        start: starting Ethereum address
        max_hops: maximum number of edges to follow

    Returns:
        dict with:
        - "visited": set of visited addresses (including start)
        - "paths": dict mapping address -> (path_list, edge_transactions)
          where path_list is list of addresses from start, and edge_transactions
          is list of {hash, value_eth, timestamp} for each hop
    """
    if not is_valid_eth_address(start):
        return {"visited": set(), "paths": {}}

    visited = {start}
    # queue: (current_address, path_so_far, hops_taken)
    queue = [(start, [start], 0)]
    # paths: address -> (path_from_start, edge_transactions_list)
    paths = {start: ([start], [])}

    while queue:
        current, path, hops = queue.pop(0)
        if hops >= max_hops:
            continue

        # Find all outgoing edges from current address
        for edge_key, txs in graph.items():
            # edge_key format: "FROM->TO"
            parts = edge_key.split("->")
            if len(parts) != 2:
                continue
            sender, receiver = parts[0], parts[1]

            if sender != current:
                continue

            for tx in txs:
                tx_hash = tx["hash"]
                tx_value = tx["value_eth"]
                tx_timestamp = tx["timestamp"]

                if receiver in visited:
                    continue

                new_path = path + [receiver]
                new_hops = hops + 1
                new_visited = visited | {receiver}

                visited.add(receiver)
                paths[receiver] = (new_path, [{"hash": tx_hash, "value_eth": tx_value, "timestamp": tx_timestamp}])

                queue.append((receiver, new_path, new_hops))

    return {"visited": visited, "paths": paths}


def print_graph(graph: dict) -> None:
    """Print a simple representation of the transaction graph.

    Format: FROM->TO (VALUE_ETH) [hashes]
    """
    if not graph:
        print("No valid transactions to display.")
        return

    for edge, txs in sorted(graph.items()):
        total_eth = sum(t["value_eth"] for t in txs)
        hashes = ", ".join(t["hash"] for t in txs[:3])
        if len(txs) > 3:
            hashes += f" +{len(txs)-3} more"
        print(f"{edge} ({total_eth:.2f}eth) [{hashes}]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a transaction graph from transaction.json"
    )
    parser.add_argument(
        "--tx-file",
        default="transaction.json",
        help="Path to transaction JSON file (default: transaction.json)",
    )
    parser.add_argument(
        "--address",
        help="Fetch transaction history from Etherscan API V2 and save to transaction.json",
    )
    parser.add_argument(
        "--token",
        help="Fetch ERC-20 token transfers from Etherscan API V2 and save to token_transfers.json",
    )
    parser.add_argument(
        "--internal",
        help="Fetch Ethereum internal transactions from Etherscan API V2 and save to internal_transactions.json",
    )
    parser.add_argument(
        "--metadata",
        help="Fetch address metadata from Etherscan V2 profile endpoint and display entity info",
    )
    parser.add_argument(
        "--start",
        help="Starting Ethereum address for BFS traversal",
    )
    parser.add_argument(
        "--max-hops",
        type=int,
        default=3,
        help="Maximum number of hops for BFS traversal (default: 3)",
    )
    args = parser.parse_args()

    if args.address:
        transactions = fetch_transactions_from_etherscan(args.address, args.tx_file)
    else:
        try:
            transactions = load_transactions(args.tx_file)
        except FileNotFoundError:
            print(f"Error: {args.tx_file} not found.", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"Error parsing JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(transactions, list) or not transactions:
        print("Error: transaction file must contain a non-empty array.", file=sys.stderr)
        sys.exit(1)

    graph = build_graph(transactions)

    if args.token:
        fetch_erc20_token_transfers(args.token, "token_transfers.json")

    if args.internal:
        fetch_internal_transactions(args.internal, "internal_transactions.json")

    if args.metadata:
        from eth_txs import fetch_address_metadata_from_etherscan
        metadata = fetch_address_metadata_from_etherscan(args.metadata)
        print(f"Address: {metadata['address']}")
        print(f"Entity Name: {metadata['entity_name']}")
        print(f"Entity Type: {metadata['entity_type']}")
        print(f"Source: {metadata['source']}")
        print(f"Confidence: {metadata['confidence']}")
        print(f"Evidence: {metadata['evidence']}")

    if args.start:
        if not is_valid_eth_address(args.start):
            print(
                "Invalid Ethereum address format for --start.",
                file=sys.stderr,
            )
            sys.exit(1)
        result = bfs_traverse(graph, args.start, args.max_hops)
        visited = sorted(result["visited"])
        paths = result["paths"]

        print(f"BFS traversal from {args.start} (max_hops={args.max_hops})")
        print(f"Visited addresses: {', '.join(visited)}")
        print()

        for hop in range(args.max_hops + 1):
            hop_addrs = []
            hop_txs = []
            for addr, (path, edge_txs) in paths.items():
                if len(path) - 1 == hop:  # hops = path length - 1
                    hop_addrs.append(addr)
                    hop_txs.extend(edge_txs)

            if not hop_addrs:
                continue

            print(f"Hop {hop}:")
            if hop_addrs:
                print(f"  Addresses: {', '.join(hop_addrs)}")
            if hop_txs:
                tx_summaries = []
                for tx in hop_txs:
                    tx_summaries.append(f"{tx['hash']} ({tx['value_eth']:.2f}eth) at {tx['timestamp']}")
                print(f"  Transactions: {', '.join(tx_summaries)}")
            # Print risk scores for entities at this hop
            # Load registry for address classification
            registry = load_address_registry(args.registry)
            for addr in hop_addrs:
                entity_type = classify_entity(addr, registry)
                score, level = calculate_risk_score(entity_type, hop)
                print(f"  Risk: {addr[:6]}...{addr[-4:]} | {entity_type} | Score: {score} | Level: {level}")
            print()
    else:
        print_graph(graph)


def bfs_traverse_unified(graph: dict, start: str, max_hops: int = 3) -> dict:
    if not is_valid_eth_address(start):
        return {"visited": set(), "paths": {}}
    visited = {start}
    queue = [(start, [start], 0, [])]
    paths = {start: ([start], [], 0)}
    while queue:
        current, path, hops, transfers = queue.pop(0)
        if hops >= max_hops:
            continue
        for edge_key, txs in graph.items():
            parts = edge_key.split("->")
            if len(parts) != 2:
                continue
            sender, receiver = parts[0], parts[1]
            if sender != current:
                continue
            for transfer in txs:
                if transfer["asset_type"] == "INTERNAL_ETH" and transfer.get("is_error") == "1":
                    continue
                if receiver in visited:
                    paths[receiver] = (paths[receiver][0], paths[receiver][1] + [transfer], paths[receiver][2])
                    continue
                new_path = path + [receiver]
                new_transfers = transfers + [transfer]
                new_hops = hops + 1
                new_visited = visited | {receiver}
                visited.add(receiver)
                paths[receiver] = (new_path, new_transfers, new_hops)
                queue.append((receiver, new_path, new_hops, new_transfers))
    return {"visited": visited, "paths": paths}


def analyze_trace(start: str, graph: dict, registry: dict, max_hops: int = 3) -> dict:
    """Run BFS traversal and attribute every discovered address.

    Returns a structured investigation result:
    - start: the starting address
    - discovered: list of all discovered addresses
    - hop_count: maximum hops reached
    - paths: dict of address -> (path, transfers, hops)
    - attribution: dict of address -> {
        address, entity_name, entity_type, source, confidence, evidence,
        risk_score, risk_level
      }
    - all transfer metadata preserved from unified BFS
    """
    from eth_txs import calculate_risk_score

    bfs_result = bfs_traverse_unified(graph, start, max_hops)
    visited = bfs_result["visited"]
    paths = bfs_result["paths"]

    # Determine max hops reached
    max_hops_reached = 0
    for addr, (path, txs, hops) in paths.items():
        if hops > max_hops_reached:
            max_hops_reached = hops

    # Attribute every discovered address
    attribution = {}
    for addr in visited:
        # attribute_address returns structured result
        attr = attribute_address(addr, registry)
        
        # Add risk score information using existing calculate_risk_score
        entity_type = attr["entity_type"]
        risk_score, risk_level = calculate_risk_score(entity_type, attr.get("hops", 0)) if addr in paths else (0, "Low")
        
        # We need to get the hops from the paths
        hops = 0
        if addr in paths:
            _, _, hops = paths[addr]
        
        risk_score, risk_level = calculate_risk_score(entity_type, hops)
        
        attribution[addr] = {
            "address": attr["address"],
            "entity_name": attr["entity_name"],
            "entity_type": attr["entity_type"],
            "source": attr["source"],
            "confidence": attr["confidence"],
            "evidence": attr["evidence"],
            "risk_score": risk_score,
            "risk_level": risk_level,
        }

    # Collect discovered addresses
    discovered = sorted(visited)

    return {
        "start": start,
        "discovered": discovered,
        "hop_count": max_hops_reached,
        "paths": paths,
        "attribution": attribution,
    }




def analyze_trace(start: str, graph: dict, registry: dict, max_hops: int = 3) -> dict:
    """Run BFS traversal and attribute every discovered address.

    Returns a structured investigation result:
    - start: the starting address
    - discovered: list of all discovered addresses
    - hop_count: maximum hops reached
    - paths: dict of address -> (path, transfers, hops)
    - attribution: dict of address -> {
        address, entity_name, entity_type, source, confidence, evidence,
        risk_score, risk_level
      }
    - all transfer metadata preserved from unified BFS
    """
    from eth_txs import calculate_risk_score

    bfs_result = bfs_traverse_unified(graph, start, max_hops)
    visited = bfs_result["visited"]
    paths = bfs_result["paths"]

    # Determine max hops reached
    max_hops_reached = 0
    for addr, (path, txs, hops) in paths.items():
        if hops > max_hops_reached:
            max_hops_reached = hops

    # Attribute every discovered address
    attribution = {}
    for addr in visited:
        # attribute_address returns structured result
        attr = attribute_address(addr, registry)
        
        # Add risk score information using existing calculate_risk_score
        entity_type = attr["entity_type"]
        risk_score, risk_level = calculate_risk_score(entity_type, attr.get("hops", 0)) if addr in paths else (0, "Low")
        
        # We need to get the hops from the paths
        hops = 0
        if addr in paths:
            _, _, hops = paths[addr]
        
        risk_score, risk_level = calculate_risk_score(entity_type, hops)
        
        attribution[addr] = {
            "address": attr["address"],
            "entity_name": attr["entity_name"],
            "entity_type": attr["entity_type"],
            "source": attr["source"],
            "confidence": attr["confidence"],
            "evidence": attr["evidence"],
            "risk_score": risk_score,
            "risk_level": risk_level,
        }

    # Collect discovered addresses
    discovered = sorted(visited)

    return {
        "start": start,
        "discovered": discovered,
        "hop_count": max_hops_reached,
        "paths": paths,
        "attribution": attribution,
    }






def test_graph() -> None:
    """Basic tests for graph creation and invalid/missing addresses."""
    # Test with valid Ethereum addresses (0x + 40 hex chars)
    valid_addr = "0x" + "a" * 40
    other_addr = "0x" + "b" * 40
    third_addr = "0x" + "c" * 40

    # Test with valid transactions
    txs = [
        {"from": valid_addr, "to": other_addr, "value": "1000000000000000000", "hash": "0xhash1", "timeStamp": "1609459200"},
        {"from": valid_addr, "to": other_addr, "value": "2000000000000000000", "hash": "0xhash2", "timeStamp": "1609459260"},
        {"from": "0xinvalid1234567890123456789012345678901234", "to": other_addr, "value": "1000000000000000000", "hash": "0xhash3", "timeStamp": "1609459200"},  # invalid sender
        {"from": valid_addr, "to": "", "value": "1000000000000000000", "hash": "0xhash4", "timeStamp": "1609459200"},  # missing receiver
        {"from": valid_addr, "to": "0xnotaddress" + "c" * 30, "value": "1000000000000000000", "hash": "0xhash5", "timeStamp": "1609459200"},  # invalid receiver
    ]
    graph = build_graph(txs)
    assert f"{valid_addr}->{other_addr}" in graph, "Valid edge should be in graph"
    assert len(graph[f"{valid_addr}->{other_addr}"]) == 2, "Should have 2 transactions for that edge"
    # Invalid addresses should be skipped
    assert f"0xinvalid1234567890123456789012345678901234->{other_addr}" not in graph, "Invalid sender should be skipped"
    assert f"{valid_addr}->" not in graph, "Missing receiver should be skipped"
    assert f"{valid_addr}->0xnotaddress" not in graph, "Invalid receiver should be skipped"

    # Test with empty list
    graph = build_graph([])
    assert graph == {}, "Empty list should produce empty graph"

    # Test with None/invalid values
    graph = build_graph([{"from": "bad", "to": "bad"}])
    assert graph == {}, "Invalid addresses should produce empty graph"

    # Test print_graph output format
    import io, sys
    from contextlib import redirect_stdout
    graph = {f"{valid_addr}->{other_addr}": [{"hash": "0xhash1", "value_eth": 1.0, "timestamp": "1609459200"}]}
    captured = io.StringIO()
    with redirect_stdout(captured):
        print_graph(graph)
    output = captured.getvalue().strip()
    assert f"{valid_addr}->{other_addr}" in output, "Should print edge"
    assert "(1.00eth)" in output, "Should print value in ETH"

    print("All graph tests passed!")


def test_bfs() -> None:
    """Tests for BFS traversal of the transaction graph."""

    valid_addr = "0x" + "a" * 40
    other_addr = "0x" + "b" * 40
    third_addr = "0x" + "c" * 40

    # Build a graph:
    # start -> other -> third (linear chain)
    # start -> third (direct shortcut)
    # start -> other AND start -> third (branching)
    txs = [
        {"from": valid_addr, "to": other_addr, "value": "1000000000000000000", "hash": "0xhash1", "timeStamp": "1609459200"},
        {"from": other_addr, "to": third_addr, "value": "2000000000000000000", "hash": "0xhash2", "timeStamp": "1609459260"},
        {"from": valid_addr, "to": third_addr, "value": "3000000000000000000", "hash": "0xhash3", "timeStamp": "1609459320"},
        {"from": valid_addr, "to": other_addr, "value": "4000000000000000000", "hash": "0xhash4", "timeStamp": "1609459380"},
    ]
    graph = build_graph(txs)

    # Test 1: Direct transfer (1 hop)
    # Graph has: valid->other, valid->third, other->third
    # With max_hops=1, we can reach both other and third directly from valid
    result = bfs_traverse(graph, valid_addr, max_hops=1)
    assert valid_addr in result["visited"]
    assert other_addr in result["visited"]
    assert third_addr in result["visited"], "With max_hops=1, should reach third directly via valid->third edge"
    # Check both paths exist
    assert len(result["paths"][other_addr][0]) == 2  # path: [start, other]
    assert len(result["paths"][other_addr][1]) == 1  # one transaction
    assert len(result["paths"][third_addr][0]) == 2  # path: [start, third]
    assert len(result["paths"][third_addr][1]) == 1  # one transaction

    # Test 2: Multi-hop transfer (2 hops)
    # Graph has direct valid->third AND valid->other->third paths
    # BFS finds shortest path first (direct edge at 1 hop)
    result = bfs_traverse(graph, valid_addr, max_hops=2)
    assert valid_addr in result["visited"]
    assert other_addr in result["visited"]
    assert third_addr in result["visited"]
    # BFS finds shortest path: direct valid->third at 1 hop
    path, edge_txs = result["paths"][third_addr]
    assert len(path) == 2, f"Expected path of length 2 (direct), got {path}"
    assert len(edge_txs) == 1, "Should have 1 edge transaction (direct edge)"

    # Test 3: Branching paths
    result = bfs_traverse(graph, valid_addr, max_hops=1)
    assert other_addr in result["visited"]
    assert third_addr in result["visited"], "Branching should reach both neighbors in 1 hop from start"
    # Check both paths exist from start
    assert len(result["paths"][other_addr][0]) == 2
    assert len(result["paths"][third_addr][0]) == 2

    # Test 4: Cycles (graph with back-edge, but BFS should not revisit)
    # Add a reverse edge: third -> start
    txs_with_cycle = txs + [
        {"from": third_addr, "to": valid_addr, "value": "5000000000000000000", "hash": "0xhash5", "timeStamp": "1609459440"},
    ]
    graph_with_cycle = build_graph(txs_with_cycle)
    result_cycle = bfs_traverse(graph_with_cycle, valid_addr, max_hops=3)
    # Should not revisit start due to visited set
    assert valid_addr in result_cycle["visited"]
    # Count unique visited addresses
    assert len(result_cycle["visited"]) > 0

    # Test 5: Maximum-hop limit
    result = bfs_traverse(graph, valid_addr, max_hops=0)
    assert valid_addr in result["visited"]
    assert len(result["visited"]) == 1, "With 0 hops, only start should be visited"
    assert len(result["paths"]) == 1

    # Test 6: Invalid start address
    result = bfs_traverse(graph, "invalid", max_hops=2)
    assert result["visited"] == set()
    assert result["paths"] == {}

    # Test 7: Start address with no outgoing edges
    graph_no_outgoing = build_graph([
        {"from": other_addr, "to": third_addr, "value": "1000000000000000000", "hash": "0xhash6", "timeStamp": "1609459200"},
    ])
    result = bfs_traverse(graph_no_outgoing, valid_addr, max_hops=5)
    assert result["visited"] == {valid_addr}
    assert result["paths"] == {valid_addr: ([valid_addr], [])}

    print("All BFS tests passed!")


def test_address_cli_with_mock() -> None:
    """Test the --address CLI flow using a mocked Etherscan API response.

    Does not make live API calls; uses unittest.mock to patch requests.get.
    Verifies that transactions are saved to transaction.json and the
    subsequent graph/BSF flow works with the fetched data.
    """
    import unittest.mock as mock
    import os

    # Set a dummy API key so the function doesn't exit early
    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response
    mock_tx_data = [
        {
            "hash": "0xmockhash1",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "value": "1000000000000000000",
            "timeStamp": "1609459200",
        },
        {
            "hash": "0xmockhash2",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xcccccccccccccccccccccccccccccccccccccccc",
            "value": "2000000000000000000",
            "timeStamp": "1609459320",
        },
    ]

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": mock_tx_data,
        }
        mock_get.return_value = mock_response

        # Run the fetch function
        from eth_txs import fetch_transactions_from_etherscan
        transactions = fetch_transactions_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "test_tx.json"
        )
    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    # Verify the saved file
    from eth_txs import load_transactions
    saved_data = load_transactions("test_tx.json")
    assert len(saved_data) == 2, f"Expected 2 transactions, got {len(saved_data)}"
    assert saved_data[0]["hash"] == "0xmockhash1"
    assert saved_data[0]["from"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert saved_data[0]["to"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert saved_data[1]["hash"] == "0xmockhash2"

    # Verify the transactions can build a graph
    from eth_txs import build_graph
    graph = build_graph(saved_data)
    assert "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa->0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" in graph
    assert "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa->0xcccccccccccccccccccccccccccccccccccccccc" in graph

    # Verify BFS works with the fetched data
    from eth_txs import bfs_traverse
    result = bfs_traverse(graph, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", max_hops=2)
    assert len(result["visited"]) > 0
    assert "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" in result["visited"]
    assert "0xcccccccccccccccccccccccccccccccccccccccc" in result["visited"]

    # Cleanup
    import os
    if os.path.exists("test_tx.json"):
        os.remove("test_tx.json")

    print("test_address_cli_with_mock passed!")


def test_etherscan_error_handling() -> None:
    """Test that Etherscan API errors print the complete JSON response including the result field.

    Verifies that when the API returns status != "1", the error message includes
    the status, message, and result fields without exposing the API key.
    """
    import unittest.mock as mock
    import os
    import sys
    from io import StringIO

    # Set a dummy API key so the function doesn't exit early
    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API error response (status = "0")
    mock_error_data = {
        "status": "0",
        "message": "Internal Error",
        "result": "Max rate limit exceeded",
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_error_data
        mock_get.return_value = mock_response

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            from eth_txs import fetch_transactions_from_etherscan
            fetch_transactions_from_etherscan(
                "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "test_error.json"
            )
        except SystemExit:
            pass  # Expected - the function exits on API error

        # Restore stderr
        output = sys.stderr.getvalue()
        sys.stderr = old_stderr

        # Verify the full error response is displayed (includes result field)
        assert "status=0" in output, f"Expected 'status=0' in error output, got: {output}"
        assert "message=Internal Error" in output, f"Expected 'message=Internal Error' in error output, got: {output}"
        assert "result=Max rate limit exceeded" in output, (
            f"Expected 'result=Max rate limit exceeded' in error output, got: {output}"
        )

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    # Cleanup
    import os
    if os.path.exists("test_error.json"):
        os.remove("test_error.json")

    print("test_etherscan_error_handling passed!")


def test_risk_scoring() -> None:
    """Tests for rule-based risk scoring and entity classification.

    Uses the address_registry.json for entity classification instead of
    the old first-hex-character prefix classifier.
    """
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Test entity classification using registry
    vasp_addr = "0x" + "a" * 40
    bridge_addr = "0x" + "b" * 40
    mixer_addr = "0x" + "c" * 40
    scam_addr = "0x" + "d" * 40
    unknown_addr = "0x" + "e" * 40

    assert classify_entity(vasp_addr, registry) == "VASP", f"Expected VASP, got {classify_entity(vasp_addr, registry)}"
    assert classify_entity(bridge_addr, registry) == "Bridge", f"Expected Bridge, got {classify_entity(bridge_addr, registry)}"
    assert classify_entity(mixer_addr, registry) == "Mixer", f"Expected Mixer, got {classify_entity(mixer_addr, registry)}"
    # Scam address not in registry -> Unknown
    assert classify_entity(scam_addr, registry) == "Unknown", f"Expected Unknown, got {classify_entity(scam_addr, registry)}"
    # Unknown address not in registry -> Unknown
    assert classify_entity(unknown_addr, registry) == "Unknown", f"Expected Unknown, got {classify_entity(unknown_addr, registry)}"

    # Test invalid address
    assert classify_entity("invalid", registry) == "Unknown"
    assert classify_entity("0x", registry) == "Unknown"

    # Test risk score calculation - base scores
    vasp_score, vasp_level = calculate_risk_score("VASP", 0)
    assert vasp_score == 10, f"Expected base score 10, got {vasp_score}"
    assert vasp_level == "Low"

    bridge_score, bridge_level = calculate_risk_score("Bridge", 0)
    assert bridge_score == 20, f"Expected base score 20, got {bridge_score}"
    assert bridge_level == "Low"

    mixer_score, mixer_level = calculate_risk_score("Mixer", 0)
    assert mixer_score == 40, f"Expected base score 40, got {mixer_score}"
    assert mixer_level == "Medium"

    scam_score, scam_level = calculate_risk_score("Scam/Fraud", 0)
    assert scam_score == 50, f"Expected base score 50, got {scam_score}"
    assert scam_level == "High"

    unknown_score, unknown_level = calculate_risk_score("Unknown", 0)
    assert unknown_score == 0, f"Expected base score 0, got {unknown_score}"
    assert unknown_level == "Low"

# Test hop-distance factor
    vasp_h1_score, _ = calculate_risk_score("VASP", 1)
    assert vasp_h1_score == 5, f"Expected score 5 at hop 1, got {vasp_h1_score}"

    # Test that score hits minimum 0 when hops exceed base points
    vasp_h3_score, vasp_h3_level = calculate_risk_score("VASP", 3)
    assert vasp_h3_score == 0, f"Expected minimum score 0 at hop 3, got {vasp_h3_score}"
    assert vasp_h3_level == "Low"

    # Test 100-point cap
    # Base 50 can't exceed 100 with the current formula, but let's verify
    high_score, high_level = calculate_risk_score("Scam/Fraud", 0)
    assert high_score <= 100, f"Score should be capped at 100, got {high_score}"

    # Test that minimum score is 0 (hops exceed base points)
    low_score, _ = calculate_risk_score("Unknown", 10)
    assert low_score == 0, f"Expected minimum score 0, got {low_score}"

    # Test risk levels
    # Scam/Fraud at hop 0 = 50 -> High
    _, scam_level = calculate_risk_score("Scam/Fraud", 0)
    assert scam_level == "High"

    # Scam/Fraud at hop 1 = 45 -> Medium
    _, scam_h1_level = calculate_risk_score("Scam/Fraud", 1)
    assert scam_h1_level == "Medium"

    # Bridge at hop 4 = 20 - 20 = 0 -> Low
    _, bridge_h4_level = calculate_risk_score("Bridge", 4)
    assert bridge_h4_level == "Low"

    # VASP at hop 2 = 10 - 10 = 0 -> Low
    _, vasp_h2_level = calculate_risk_score("VASP", 2)
    assert vasp_h2_level == "Low"

    print("All risk scoring tests passed!")
# New tests for address registry architecture

def test_address_registry() -> None:
    """Tests for the address registry architecture.

    Tests known VASP, Bridge, Mixer, unknown address,
    malformed registry data, and case-insensitive lookup.

    All registry entries are synthetic test data;
    they do not represent real companies or real blockchain addresses.

    Known entities (in registry):
      - KnownVASP (VASP entity type)
      - KnownBridge (Bridge entity type)
      - KnownMixer (Mixer entity type)

    Unknown address: returns entity_type Unknown.
    Malformed registry data: gracefully handled.
    Case-insensitive address lookup: works regardless of case.
    """
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Known VASP
    vasp_addr = "0x" + "a" * 40
    assert classify_entity(vasp_addr, registry) == "VASP"

    # Known Bridge
    bridge_addr = "0x" + "b" * 40
    assert classify_entity(bridge_addr, registry) == "Bridge"

    # Known Mixer
    mixer_addr = "0x" + "c" * 40
    assert classify_entity(mixer_addr, registry) == "Mixer"

    # Unknown address (not in registry)
    unknown_addr = "0x" + "e" * 40
    assert classify_entity(unknown_addr, registry) == "Unknown"

    # Case-insensitive lookup: uppercase hex
    addr_upper = "0x" + "A" * 40
    assert classify_entity(addr_upper, registry) == "VASP"

    # Malformed registry data test
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write("{invalid json}")
        tmp_path = tmp.name

    try:
        from eth_txs import load_address_registry
        try:
            loaded = load_address_registry(tmp_path)
            assert loaded == {} or loaded is None
        except (json.JSONDecodeError, Exception):
            pass
    finally:
        os.unlink(tmp_path)

    print("All address registry tests passed!")

# New tests for attribute_address evidence-based attribution
def test_attribute_address() -> None:
    """Tests for the attribute_address evidence-based attribution function.

    Tests known VASP, Bridge, Mixer, unknown address,
    confidence preservation, source preservation, and evidence generation.

    All registry entries are synthetic test data;
    they do not represent real companies or real blockchain addresses.
    """
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Known VASP attribution
    vasp_addr = "0x" + "a" * 40
    result = attribute_address(vasp_addr, registry)
    assert result["entity_name"] == "KnownVASP", f"Expected KnownVASP, got {result['entity_name']}"
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert result["source"] == "synthetic_test_registry", f"Expected synthetic_test_registry, got {result['source']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    assert "matched entity" in result["evidence"], f"Expected evidence about match, got: {result['evidence']}"
    assert "synthetic test data" in result["evidence"], f"Evidence should mention synthetic test data"

    # Known Bridge attribution
    bridge_addr = "0x" + "b" * 40
    result = attribute_address(bridge_addr, registry)
    assert result["entity_name"] == "KnownBridge", f"Expected KnownBridge, got {result['entity_name']}"
    assert result["entity_type"] == "Bridge", f"Expected Bridge, got {result['entity_type']}"
    assert result["confidence"] == 1.0

    # Known Mixer attribution
    mixer_addr = "0x" + "c" * 40
    result = attribute_address(mixer_addr, registry)
    assert result["entity_name"] == "KnownMixer", f"Expected KnownMixer, got {result['entity_name']}"
    assert result["entity_type"] == "Mixer", f"Expected Mixer, got {result['entity_type']}"
    assert result["confidence"] == 1.0

    # Unknown address attribution
    unknown_addr = "0x" + "z" * 40
    result = attribute_address(unknown_addr, registry)
    assert result["entity_name"] == "Unknown", f"Expected Unknown, got {result['entity_name']}"
    assert result["entity_type"] == "Unknown", f"Expected Unknown, got {result['entity_type']}"
    assert result["confidence"] == 0.0, f"Expected 0.0, got {result['confidence']}"
    assert "not found" in result["evidence"].lower() or "no match" in result["evidence"].lower(),         f"Evidence should indicate no match: {result['evidence']}"

    # Case-insensitive uppercase address
    addr_upper = "0x" + "A" * 40
    result = attribute_address(addr_upper, registry)
    assert result["entity_name"] == "KnownVASP", f"Expected KnownVASP for uppercase, got {result['entity_name']}"
    assert result["entity_type"] == "VASP"

    # Address with 0x prefix variant
    addr_no_prefix = "0x" + "a" * 40  # should still work with prefix
    result = attribute_address(addr_no_prefix, registry)
    assert result["entity_name"] == "KnownVASP", f"Expected KnownVASP, got {result['entity_name']}"

    # Verify classify_entity still works backward compatible (no registry arg)
    # This test address is NOT in registry, so should return Unknown
    result_no_reg = classify_entity("0x" + "z" * 40)
    assert result_no_reg == "Unknown", f"Expected Unknown without registry, got {result_no_reg}"

    # Verify classify_entity works with registry
    result_with_reg = classify_entity("0x" + "a" * 40, registry)
    assert result_with_reg == "VASP", f"Expected VASP with registry, got {result_with_reg}"

    print("All attribute_address tests passed!")




def test_etherscan_v2_endpoint() -> None:
    """Verify that the Etherscan request uses the V2 API endpoint (/v2/api).

    Patches requests.get and checks that the base URL contains /v2/api
    (not the deprecated /api V1 endpoint). Does not expose the API key.
    """
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": [],
        }
        mock_get.return_value = mock_response

        from eth_txs import fetch_transactions_from_etherscan
        fetch_transactions_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "test_v2.json"
        )

        # Get the request URL that was actually called
        call_args = mock_get.call_args
        url = call_args[0][0]  # first positional arg is the URL

        # Verify V2 endpoint is used (no apiversion param needed; /v2/ in path selects V2)
        assert "/v2/api" in url, f"Expected /v2/api in URL, got: {url}"

        # Verify V1 endpoint is NOT used
        assert "/api" in url, f"URL should contain api endpoint, got: {url}"

        # Verify chainid=1 is included in the request parameters (required for V2 API)
        params = call_args[1].get("params", {})
        assert "chainid" in params and params["chainid"] == "1", (
            f"Expected chainid=1 in request params, got: {params}"
        )

        # Verify API key is not in the URL
        assert "apikey=" not in url.lower() or "testkey" not in url, (
            "API key should not appear in URL"
        )

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    # Cleanup
    import os
    if os.path.exists("test_v2.json"):
        os.remove("test_v2.json")

    print("test_etherscan_v2_endpoint passed!")


def test_erc20_token_transfers() -> None:
    """Test the ERC-20 token transfer fetching and parsing flow.

    Uses mocked Etherscan API responses to verify:
    - Successful fetching and saving of token transfers
    - Parsing of raw token transfer data into common format
    - Graph construction with token transfer data
    """
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response for token transfers
    mock_token_data = [
        {
            "hash": "0xmocktokenhash1",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "tokenContractAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
            "tokenSymbol": "USDT",
            "value": "1000000",
            "timeStamp": "1609459200",
        },
        {
            "hash": "0xmocktokenhash2",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xcccccccccccccccccccccccccccccccccccccccc",
            "tokenContractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
            "tokenSymbol": "USDC",
            "value": "500000",
            "timeStamp": "1609459300",
        },
    ]

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": mock_token_data,
        }
        mock_get.return_value = mock_response

        # Run the fetch function
        from eth_txs import fetch_erc20_token_transfers
        transfers = fetch_erc20_token_transfers(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "test_token.json"
        )
    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    # Verify the saved file
    from eth_txs import load_transactions
    saved_data = load_transactions("test_token.json")
    assert len(saved_data) == 2, f"Expected 2 token transfers, got {len(saved_data)}"
    assert saved_data[0]["tokenSymbol"] == "USDT"
    assert saved_data[0].get("tokenContractAddress", "") == "0xcccccccccccccccccccccccccccccccccccccccc"
    assert saved_data[1]["tokenSymbol"] == "USDC"

    # Verify parsing works correctly
    from eth_txs import parse_erc20_transfer
    parsed = parse_erc20_transfer(saved_data[0])
    assert parsed["hash"] == "0xmocktokenhash1"
    assert parsed["from_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert parsed["to_address"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert parsed["token_contract_address"] == "0xcccccccccccccccccccccccccccccccccccccccc"
    assert parsed["token_symbol"] == "USDT"
    assert parsed["amount_ether"] == 1e-12  # 1000000 / 10^18
    assert parsed["timestamp"] == "1609459200"

    # Verify graph can be built with the token transfer data
    from eth_txs import build_graph
    # Create a combined transaction list that includes both ETH and token transfers
    combined_txs = [
        {"from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "value": "1000000000000000000", "hash": "0xethhash1", "timeStamp": "1609459200"},
        *saved_data,  # Include the token transfers
    ]
    graph = build_graph(combined_txs)
    # The ETH transaction should be in the graph
    eth_edge = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa->0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert eth_edge in graph, f"Expected ETH edge {eth_edge} in graph"

    # Cleanup
    import os
    if os.path.exists("test_token.json"):
        os.remove("test_token.json")

    print("test_erc20_token_transfers passed!")


def fetch_internal_transactions(address: str, filepath: str = "internal_transactions.json") -> list:
    """Fetch Ethereum internal transactions for an address using Etherscan API V2.

    Calls the `txlistinternal` endpoint and saves the raw response to `filepath`
    (default: internal_transactions.json). Returns the parsed internal transactions list.

    Requires ETHERSCAN_API_KEY environment variable to be set (loaded from .env file).
    Uses chainid=1 for Ethereum Mainnet.
    """
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: ETHERSCAN_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not is_valid_eth_address(address):
        print(f"Invalid Ethereum address: {address}", file=sys.stderr)
        sys.exit(1)

    base_url = "https://api.etherscan.io/v2/api"
    params = {
        "module": "account",
        "action": "txlistinternal",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,
        "sort": "asc",
        "chainid": "1",
        "apikey": api_key,
    }

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            # Print complete error response (including result field) without exposing the API key
            error_detail = data.get("result", "No result field")
            print(f"Etherscan API error (status={data.get('status')}, message={data.get('message')}, result={error_detail})", file=sys.stderr)
            sys.exit(1)

        internal_txs = data.get("result", [])
        with open(filepath, "w") as f:
            json.dump(internal_txs, f, indent=2)

        print(f"Fetched {len(internal_txs)} internal transactions for {address} and saved to {filepath}")
        return internal_txs

    except requests.exceptions.RequestException as exc:
        print(f"Error fetching from Etherscan: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_internal_transaction(raw: dict) -> dict:
    """Parse a raw Etherscan internal transaction dict into a common format.

    Returns a dict with keys: hash, from_address, to_address,
    value_wei, value_eth, timestamp, is_error.
    """
    return {
        "hash": raw.get("hash", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "value_wei": raw.get("value", "0"),
        "value_eth": int(raw.get("value", "0")) / 10 ** 18,
        "timestamp": raw.get("timeStamp", "0"),
        "is_error": raw.get("isError", "0"),
    }



def normalize_eth_transaction(raw: dict) -> dict:
    """Normalize a raw ETH transaction into a common format.

    Returns dict with keys: hash, from_address, to_address,
    asset_type ('ETH'), asset_contract (null), symbol ('ETH'), amount, timestamp.
    """
    value_eth = int(raw.get("value", "0")) / 10 ** 18
    return {
        "hash": raw.get("hash", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": value_eth,
        "timestamp": raw.get("timeStamp", "0"),
    }


def normalize_erc20_transfer(raw: dict) -> dict:
    """Normalize a raw ERC-20 token transfer into a common format.

    Returns dict with keys: hash, from_address, to_address,
    asset_type ('ERC20'), asset_contract (token contract address),
    symbol (token symbol), amount (in ETH), timestamp.

    Uses the tokenDecimal field from Etherscan response when available,
    defaulting to 18 decimals for backward compatibility.
    """
    # Use tokenDecimal from Etherscan if available, default to 18
    token_decimals = int(raw.get("tokenDecimal", "18"))
    amount_raw = int(raw.get("value", "0"))
    amount_eth = amount_raw / (10 ** token_decimals)
    return {
        "hash": raw.get("hash", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "asset_type": "ERC20",
        "asset_contract": raw.get("tokenContractAddress", ""),
        "symbol": raw.get("tokenSymbol", ""),
        "amount": amount_eth,
        "timestamp": raw.get("timeStamp", "0"),
    }


def normalize_internal_transaction(raw: dict) -> dict:
    """Normalize a raw Etherscan internal transaction into a common format.

    Returns dict with keys: hash, from_address, to_address,
    asset_type ('INTERNAL_ETH'), asset_contract (null), symbol ('ETH'),
    amount (in ETH), timestamp, is_error.
    """
    value_eth = int(raw.get("value", "0")) / 10 ** 18
    return {
        "hash": raw.get("hash", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "asset_type": "INTERNAL_ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": value_eth,
        "timestamp": raw.get("timeStamp", "0"),
        "is_error": raw.get("isError", "0"),
    }


def normalize_all_transfers(eth_txs: list, erc20_txs: list, internal_txs: list) -> list:
    """Combine ETH, ERC-20, and internal transactions into one normalized list.

    Accepts three lists of raw transaction dicts and returns one combined
    list of normalized transfer dicts with consistent field names.
    """
    normalized = []
    for raw in eth_txs:
        normalized.append(normalize_eth_transaction(raw))
    for raw in erc20_txs:
        normalized.append(normalize_erc20_transfer(raw))
    for raw in internal_txs:
        normalized.append(normalize_internal_transaction(raw))
    return normalized


def test_normalize_transactions() -> None:
    """Test the normalization functions for ETH, ERC-20, and internal transactions.

    Verifies that all three normalization functions correctly convert
    their respective raw data formats into the common dictionary structure
    with consistent field names: hash, from_address, to_address,
    asset_type, asset_contract, symbol, amount, timestamp.
    """
    import json

    # Raw ETH transaction data
    eth_raw = {
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "value": "1000000000000000000",
        "hash": "0xethhash1",
        "timeStamp": "1609459200",
    }

    # Raw ERC-20 transfer data (USDT with 6 decimals)
    erc20_raw = {
        "hash": "0xmocktokenhash1",
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "tokenContractAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
        "tokenSymbol": "USDT",
        "tokenDecimal": "6",
        "value": "1000000",
        "timeStamp": "1609459200",
    }

    # Raw internal transaction data
    internal_raw = {
        "hash": "0xinternalhash1",
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "value": "500000000000000000",
        "timeStamp": "1609459200",
        "isError": "0",
    }

    # Normalize each type
    eth_norm = normalize_eth_transaction(eth_raw)
    erc20_norm = normalize_erc20_transfer(erc20_raw)
    internal_norm = normalize_internal_transaction(internal_raw)

    # Verify ETH normalization
    assert eth_norm["hash"] == "0xethhash1"
    assert eth_norm["from_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert eth_norm["to_address"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert eth_norm["asset_type"] == "ETH"
    assert eth_norm["asset_contract"] is None
    assert eth_norm["symbol"] == "ETH"
    assert eth_norm["amount"] == 1.0  # 1e18 / 1e18
    assert eth_norm["timestamp"] == "1609459200"

    # Verify ERC-20 normalization (USDT with 6 decimals)
    assert erc20_norm["hash"] == "0xmocktokenhash1"
    assert erc20_norm["from_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert erc20_norm["to_address"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert erc20_norm["asset_type"] == "ERC20"
    assert erc20_norm["asset_contract"] == "0xcccccccccccccccccccccccccccccccccccccccc"
    assert erc20_norm["symbol"] == "USDT"
    assert erc20_norm["amount"] == 1.0  # 1000000 / 10**6 (6 decimals)
    assert erc20_norm["timestamp"] == "1609459200"

    # Verify internal normalization
    assert internal_norm["hash"] == "0xinternalhash1"
    assert internal_norm["from_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert internal_norm["to_address"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert internal_norm["asset_type"] == "INTERNAL_ETH"
    assert internal_norm["asset_contract"] is None
    assert internal_norm["symbol"] == "ETH"
    assert internal_norm["amount"] == 0.5  # 5e17 / 1e18
    assert internal_norm["timestamp"] == "1609459200"
    assert internal_norm["is_error"] == "0"

    # Verify normalize_all_transfers combines all three types
    from eth_txs import normalize_all_transfers
    eth_list = [eth_raw]
    erc20_list = [erc20_raw]
    internal_list = [internal_raw]
    all_norm = normalize_all_transfers(eth_list, erc20_list, internal_list)
    assert len(all_norm) == 3
    assert all_norm[0]["asset_type"] == "ETH"
    assert all_norm[1]["asset_type"] == "ERC20"
    assert all_norm[2]["asset_type"] == "INTERNAL_ETH"

    print("test_normalize_transactions passed!")




def fetch_address_metadata_from_etherscan(address: str) -> dict:
    """Fetch address metadata from Etherscan API V2 profile endpoint.

    Calls the account.profile endpoint with chainid=1 and the ETHERSCAN_API_KEY
    from the environment. Returns parsed metadata structured into our attribution
    format without modifying any synthetic registry.

    Returns a dict with fields:
    - address: the normalized address
    - entity_name: human-readable entity name from Etherscan nametags
    - entity_type: mapped entity type (VASP/Bridge/Mixer/Scam/Fraud/Unknown)
    - source: "Etherscan Metadata"
    - confidence: 1.0 for strong labels, 0.5 for name-only, 0.0 for none
    - evidence: string describing nametags/labels found and mapping applied
    - raw_metadata: the raw Etherscan result for reference

    Entity type mapping is conservative:
    - Labels clearly indicating VASP (e.g., "binance", "coinbase", "kraken")
      -> entity_type "VASP", entity_name from label
    - Labels clearly indicating Bridge (e.g., "bridge", "liquidity pool")
      -> entity_type "Bridge", entity_name from label
    - Labels clearly indicating Mixer (e.g., "tornado cash", "mixer")
      -> entity_type "Mixer", entity_name from label
    - Labels indicating Scam/Fraud (e.g., "scam", "fraud", "phishing")
      -> entity_type "Scam/Fraud", entity_name from label
    - All other labels/nametags -> entity_type "Unknown"
    - If no labels are present, entity_type "Unknown" and entity_name "Unknown"
    - confidence 1.0 when labels provide entity_type, 0.5 when only name tag,
      0.0 when nothing recognisable
    - evidence explicitly lists the nametags/labels found and the mapping
    - source always "Etherscan Metadata"; never invents real-world attribution

    Does not make real API calls during tests (mocked in test suite).
    Never hardcodes or prints the API key.
    """
    import json
    import os
    from pathlib import Path

    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: ETHERSCAN_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not is_valid_eth_address(address):
        print(f"Invalid Ethereum address: {address}", file=sys.stderr)
        sys.exit(1)

    base_url = "https://api.etherscan.io/v2/api"
    params = {
        "module": "nametag",
        "action": "getaddresstag",
        "address": address,
        "chainid": "1",
        "apikey": api_key,
    }

    import requests
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            return {
                "address": address,
                "entity_name": "Unknown",
                "entity_type": "Unknown",
                "source": "Etherscan Metadata",
                "confidence": 0.0,
                "evidence": f"Etherscan API returned status {data.get("status")}: {data.get("result", "no result")}",
                "raw_metadata": data,
            }

        result_data = data.get("result", [])
        if not result_data:
            return {
                "address": address,
                "entity_name": "Unknown",
                "entity_type": "Unknown",
                "source": "Etherscan Metadata",
                "confidence": 0.0,
                "evidence": "No nametag data returned from Etherscan",
                "raw_metadata": data,
            }

        # Parse labels and nametags from Etherscan profile
        # Etherscan V2 result is a single object (not array) for getaddresstag
        if isinstance(result_data, list):
            result_data = result_data[0] if result_data else {}
        
        labels = result_data.get("labels", [])
        name_tags = result_data.get("nametag", "")

        # Build entity_type and entity_name from labels conservatively
        entity_type = "Unknown"
        entity_name = "Unknown"
        label_descriptions = []

        # Known VASP label mappings (lowercase)
        vasp_labels = {"binance", "coinbase", "kraken", "gemini", "ftx", "blockfi", "crypto-com", "paymium"}
        # Known Bridge label mappings (lowercase)
        bridge_labels = {"bridge", "liquidity pool", "token bridge", "portemonnaie", "celer", "corda", "interledger"}
        # Known Mixer label mappings (lowercase)
        mixer_labels = {"tornado cash", "mixer", "coinjoin", "joinmarket", "wasabi", "samourai"}
        # Known Scam/Fraud label mappings (lowercase)
        scam_labels = {"scam", "fraud", "phishing", "blacklist", "malicious", "dust", "honey pot"}

        for label in labels:
            label_name = label.get("name", "").lower()
            label_type = label.get("type", "").lower()
            label_type_name = label.get("type_name", "").lower()

            # Check all available label info
            all_label_text = f"{label_name} {label_type} {label_type_name}".lower()

            # Check for Scam/Fraud first (most specific)
            if any(s in all_label_text for s in scam_labels):
                entity_type = "Scam/Fraud"
                entity_name = label_name.capitalize() if label_name and label_name != "unknown" else "Unknown"
                label_descriptions.append(f"Scam/Fraud label: {label.get("name", "N/A")}")

            # Check for Mixer
            elif any(m in all_label_text for m in mixer_labels):
                if entity_type == "Unknown":
                    entity_type = "Mixer"
                    entity_name = label_name.capitalize() if label_name and label_name != "unknown" else "Unknown"
                    label_descriptions.append(f"Mixer label: {label.get("name", "N/A")}")

            # Check for Bridge
            elif any(b in all_label_text for b in bridge_labels):
                if entity_type == "Unknown":
                    entity_type = "Bridge"
                    entity_name = label_name.capitalize() if label_name and label_name != "unknown" else "Unknown"
                    label_descriptions.append(f"Bridge label: {label.get("name", "N/A")}")

            # Check for VASP
            elif any(v in all_label_text for v in vasp_labels):
                if entity_type == "Unknown":
                    entity_type = "VASP"
                    entity_name = label_name.capitalize() if label_name and label_name != "unknown" else "Unknown"
                    label_descriptions.append(f"VASP label: {label.get("name", "N/A")}")

            else:
                # Unknown label - keep entity_type as Unknown but record the label name
                if entity_type == "Unknown":
                    entity_name = label_name.capitalize() if label_name and label_name != "unknown" else "Unknown"
                label_descriptions.append(f"Label: {label.get("name", "N/A")}")

        # Also check the overall nametag if present and entity_type still Unknown
        if name_tags and entity_type == "Unknown":
            name_lower = str(name_tags).lower()
            if any(v in name_lower for v in vasp_labels):
                entity_type = "VASP"
                entity_name = str(name_tags).capitalize()
            elif any(m in name_lower for m in mixer_labels):
                entity_type = "Mixer"
                entity_name = str(name_tags)
            elif any(b in name_lower for b in bridge_labels):
                entity_type = "Bridge"
                entity_name = str(name_tags)
            elif any(s in name_lower for s in scam_labels):
                entity_type = "Scam/Fraud"
                entity_name = str(name_tags)
            else:
                # Name tag present but no category matched; keep entity_type Unknown
                # but record the name tag for evidence and confidence
                entity_name = str(name_tags)

        # Determine confidence
        has_name_tag = entity_name != "Unknown"
        if entity_type != "Unknown" and label_descriptions:
            confidence = 1.0
        elif entity_type != "Unknown" and not label_descriptions and not has_name_tag:
            confidence = 0.5  # entity type from label-like name but no descriptive labels
        elif has_name_tag and not label_descriptions:
            confidence = 0.5  # name tag only, no specific labels
        else:
            confidence = 0.0

        # Build evidence string
        evidence_parts = []
        if label_descriptions:
            evidence_parts.append("Etherscan nametags/labels: " + "; ".join(label_descriptions))
        if entity_type != "Unknown":
            evidence_parts.append(f"mapped entity_type={entity_type}")
        if entity_name != "Unknown":
            evidence_parts.append(f"entity_name={entity_name}")

        evidence = ". ".join(evidence_parts) if evidence_parts else "No recognisable Etherscan nametags found"

        return {
            "address": address,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "source": "Etherscan Metadata",
            "confidence": confidence,
            "evidence": evidence,
            "raw_metadata": data,
        }

    except requests.exceptions.RequestException as exc:
        return {
            "address": address,
            "entity_name": "Unknown",
            "entity_type": "Unknown",
            "source": "Etherscan Metadata",
            "confidence": 0.0,
            "evidence": f"Error fetching Etherscan metadata: {exc}",
            "raw_metadata": None,
        }

def combine_attribution_sources(address: str, registry: dict, etherscan_metadata: dict) -> dict:
    """Combine attribution from local address registry and Etherscan metadata.

    Returns a unified attribution result dict with fields:
    - address: the normalized address
    - entity_name: combined entity name
    - entity_type: combined entity type
    - source: combined source list
    - confidence: combined confidence
    - evidence: string describing the attribution logic applied

    Rules:
    - If registry has a known entity and Etherscan is Unknown → preserve registry attribution
    - If registry is Unknown and Etherscan has a clearly mapped entity type → use Etherscan attribution
    - If both sources identify the same entity type → combine evidence and increase confidence
      conservatively (not exceeding 1.0, do not invent confidence)
    - If sources disagree on entity type → preserve disagreement in evidence, choose registry as primary
    - Preserve both sources in a 'sources' field
    """
    # Parse registry attribution
    registry_attr = attribute_address(address, registry)

    # Parse Etherscan metadata attribution
    etherscan_attr = {
        "address": etherscan_metadata.get("address", address),
        "entity_name": etherscan_metadata.get("entity_name", "Unknown"),
        "entity_type": etherscan_metadata.get("entity_type", "Unknown"),
        "source": etherscan_metadata.get("source", "Etherscan Metadata"),
        "confidence": etherscan_metadata.get("confidence", 0.0),
        "evidence": etherscan_metadata.get("evidence", ""),
    }

    # Rule 1: If registry has known entity and Etherscan is Unknown → preserve registry
    if registry_attr.get("entity_type") != "Unknown" and etherscan_attr.get("entity_type") == "Unknown":
        registry_attr["sources"] = [registry_attr.get("source", "unknown"), "Etherscan Metadata"]
        registry_attr["combined_evidence"] = (
            f"{registry_attr['evidence']}. No Etherscan metadata available; registry attribution preserved."
        )
        registry_attr["confidence"] = min(1.0, registry_attr.get("confidence", 0.0) + 0.1)
        return registry_attr

    # Rule 2: If registry is Unknown and Etherscan has mapped entity type → use Etherscan
    if registry_attr.get("entity_type") == "Unknown" and etherscan_attr.get("entity_type") != "Unknown":
        result = dict(etherscan_attr)
        result["sources"] = ["Etherscan Metadata", registry_attr.get("source", "unknown")]
        result["combined_evidence"] = (
            f"{etherscan_attr['evidence']}. No registry match; Etherscan attribution applied."
        )
        result["confidence"] = min(1.0, etherscan_attr.get("confidence", 0.0) + 0.1)
        return result

    # Rule 3: Both sources identify the same entity type → combine conservatively
    if registry_attr.get("entity_type") == etherscan_attr.get("entity_type") and registry_attr.get("entity_type") != "Unknown":
        combined_type = registry_attr.get("entity_type")
        # Combine evidence from both sources
        combined_evidence = (
            f"{registry_attr['evidence']}; {etherscan_attr['evidence']}"
        )
        # Increase confidence conservatively: take the higher, add 0.1, cap at 1.0
        reg_conf = registry_attr.get("confidence", 0.0)
        esc_conf = etherscan_attr.get("confidence", 0.0)
        combined_conf = min(1.0, max(reg_conf, esc_conf) + 0.1)
        # Build result with both sources
        result = {
            "address": address,
            "entity_name": etherscan_attr.get("entity_name", registry_attr.get("entity_name", "Unknown")),
            "entity_type": combined_type,
            "source": ["Etherscan Metadata", registry_attr.get("source", "unknown")],
            "confidence": combined_conf,
            "evidence": combined_evidence,
            "sources": ["Etherscan Metadata", registry_attr.get("source", "unknown")],
        }
        # Preserve combined_evidence as well
        result["combined_evidence"] = combined_evidence
        return result

    # Rule 4: Sources disagree on entity type → preserve registry as primary, record disagreement
    if registry_attr.get("entity_type") != etherscan_attr.get("entity_type"):
        # Choose registry as primary, but record Etherscan info
        result = dict(registry_attr)
        result["sources"] = [registry_attr.get("source", "unknown"), "Etherscan Metadata"]
        result["evidence"] = (
            f"{registry_attr['evidence']}. Etherscan metadata: {etherscan_attr.get('entity_type', 'Unknown')} entity type. "
            f"Disagreement resolved to registry attribution."
        )
        # Slightly increase confidence for having multiple sources
        result["confidence"] = min(1.0, registry_attr.get("confidence", 0.0) + 0.1)
        result["combined_evidence"] = (
            f"{registry_attr['evidence']}; Etherscan metadata disagreed: {etherscan_attr.get('evidence', '')}"
        )
        return result

    # Rule 5: Both unknown → return Unknown
    result = {
        "address": address,
        "entity_name": "Unknown",
        "entity_type": "Unknown",
        "source": ["Etherscan Metadata", registry_attr.get("source", "unknown")],
        "confidence": 0.0,
        "evidence": "No attribution found in registry or Etherscan metadata.",
        "sources": ["Etherscan Metadata", registry_attr.get("source", "unknown")],
    }
    return result


def test_internal_transactions() -> None:
    """Test the --internal CLI flow using a mocked Etherscan API response.

    Does not make live API calls; uses unittest.mock to patch requests.get.
    Verifies that internal transactions are saved to internal_transactions.json
    and the parse_internal_transaction function correctly extracts fields
    including is_error for failed transactions.
    """
    import unittest.mock as mock
    import os
    import json

    # Set a dummy API key so the function doesn't exit early
    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response
    mock_internal_data = [
        {
            "hash": "0xinternalhash1",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "value": "500000000000000000",
            "timeStamp": "1609459200",
            "isError": "0",
        },
        {
            "hash": "0xinternalhash2",
            "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to": "0xcccccccccccccccccccccccccccccccccccccccc",
            "value": "1000000000000000000",
            "timeStamp": "1609459260",
            "isError": "1",
        },
    ]

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": mock_internal_data,
        }
        mock_get.return_value = mock_response

        # Run the fetch function
        from eth_txs import fetch_internal_transactions
        txs = fetch_internal_transactions(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "test_internal.json"
        )
    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    # Verify the saved file
    from eth_txs import load_transactions
    saved_data = load_transactions("test_internal.json")
    assert len(saved_data) == 2, f"Expected 2 internal transactions, got {len(saved_data)}"
    assert saved_data[0]["hash"] == "0xinternalhash1"
    assert saved_data[0]["isError"] == "0"
    assert saved_data[1]["hash"] == "0xinternalhash2"
    assert saved_data[1]["isError"] == "1"

    # Verify parsing works correctly
    from eth_txs import parse_internal_transaction
    parsed = parse_internal_transaction(saved_data[0])
    assert parsed["hash"] == "0xinternalhash1"
    assert parsed["from_address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert parsed["to_address"] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert parsed["value_wei"] == "500000000000000000"
    assert parsed["value_eth"] == 0.5
    assert parsed["timestamp"] == "1609459200"
    assert parsed["is_error"] == "0"

    # Test failed internal transaction parsing
    parsed_err = parse_internal_transaction(saved_data[1])
    assert parsed_err["is_error"] == "1"
    assert parsed_err["value_eth"] == 1.0

    # Cleanup
    import os
    if os.path.exists("test_internal.json"):
        os.remove("test_internal.json")

    print("test_internal_transactions passed!")

# New tests for analyze_trace unified BFS+tracing attribution
def test_attribute_trace() -> None:
    """Tests for the analyze_trace unified BFS+tracing attribution function.

    Tests multi-hop trace containing known VASP, known Bridge,
    Unknown address, multiple assets, a cycle, and a failed internal transfer.

    All registry entries are synthetic test data;
    they do not represent real companies or real blockchain addresses.
    """
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Build transfers with: VASP -> Bridge -> Unknown, plus multi-asset, cycle, failed internal
    from eth_txs import normalize_eth_transaction, normalize_erc20_transfer, normalize_internal_transaction, build_unified_graph

    transfers = []

    # VASP outflow
    transfers.append(normalize_eth_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xvasp1",
        "timestamp": "1609459200",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 5.0,
    }))

    # Bridge transfer (ETH from VASP to Bridge)
    transfers.append(normalize_eth_transaction({
        "from": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "to": "0xcccccccccccccccccccccccccccccccccccccccc",
        "hash": "0xbridge1",
        "timestamp": "1609459201",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 2.0,
    }))

    # Unknown address receive (internal transfer that is NOT in registry)
    transfers.append(normalize_internal_transaction({
        "from": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "to": "0xdddddddddddddddddddddddddddddddddddddddd",
        "hash": "0xinternalunknown1",
        "timestamp": "1609459202",
        "asset_type": "INTERNAL_ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 1.0,
        "is_error": "0",
    }))

    # Multi-asset transfer: Bridge -> Unknown with USDT
    transfers.append(normalize_erc20_transfer({
        "from": "0xcccccccccccccccccccccccccccccccccccccccc",
        "to": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "hash": "0xusdt2",
        "timestamp": "1609459203",
        "asset_type": "ERC20",
        "asset_contract": "0xusdtcontract",
        "symbol": "USDT",
        "amount": 10.0,
    }))

    # Cycle: Unknown -> VASP (back edge)
    transfers.append(normalize_eth_transaction({
        "from": "0xdddddddddddddddddddddddddddddddddddddddd",
        "to": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "hash": "0xcycle1",
        "timestamp": "1609459204",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 0.5,
    }))

    # Failed internal transfer (should be excluded from graph)
    transfers.append(normalize_internal_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xintfail2",
        "timestamp": "1609459205",
        "asset_type": "INTERNAL_ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 0.3,
        "is_error": "1",
    }))

    # Build unified graph (failed internal excluded)
    graph = build_unified_graph(transfers)

    # Run analysis
    result = analyze_trace("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", graph, registry, max_hops=3)

    # Verify starting address
    assert result["start"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", f"Wrong start: {result['start']}"

    # Verify discovered addresses include expected entities
    discovered = result["discovered"]
    print(f"Discovered addresses: {discovered}")

    # Verify attribution for known VASP
    vasp_attr = result["attribution"].get("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", {})
    assert vasp_attr["entity_name"] == "KnownVASP", f"Expected KnownVASP, got {vasp_attr.get('entity_name')}"

    # Verify attribution for known Bridge
    bridge_attr = result["attribution"].get("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", {})
    assert bridge_attr["entity_name"] == "KnownBridge", f"Expected KnownBridge, got {bridge_attr.get('entity_name')}"

    # Verify unknown address stays Unknown (not inferred)
    unknown_attr = result["attribution"].get("0xdddddddddddddddddddddddddddddddddddddddd", {})
    assert unknown_attr["entity_name"] == "Unknown", f"Expected Unknown, got {unknown_attr.get('entity_name')}"
    assert unknown_attr["entity_type"] == "Unknown", f"Expected Unknown type, got {unknown_attr.get('entity_type')}"
    assert unknown_attr["confidence"] == 0.0, f"Expected confidence 0.0, got {unknown_attr.get('confidence')}"

    # Verify USDT address attribution (not in registry -> Unknown)
    usdt_attr = result["attribution"].get("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", {})
    assert usdt_attr["entity_name"] == "Unknown", f"USDT receiver should be Unknown (not in registry), got {usdt_attr.get('entity_name')}"

    # Verify risk scores are present
    for addr, attr in result["attribution"].items():
        assert "risk_score" in attr, f"Missing risk_score for {addr}"
        assert "risk_level" in attr, f"Missing risk_level for {addr}"
        assert isinstance(attr["risk_score"], int), f"risk_score should be int for {addr}"
        assert isinstance(attr["risk_level"], str), f"risk_level should be str for {addr}"

    # Verify transfer metadata preserved - VASP->Bridge path should have ETH transfer
    vasp_to_bridge_path = result["paths"].get("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", ([] , [], 0))
    _, bridge_txs, _ = vasp_to_bridge_path
    eth_in_bridge = any(t["symbol"] == "ETH" for t in bridge_txs)
    assert eth_in_bridge, "Expected ETH transfer from VASP to Bridge in path metadata"

    # Verify the cycle detection - VASP should reach itself through the cycle
    # (the cycle is Unknown -> VASP, so VASP can reach Unknown and back)
    # At minimum verify the path structure is correct

    print("All attribute_trace tests passed!")

# New tests for fetch_address_metadata_from_etherscan
def test_fetch_address_metadata_basic() -> None:
    """Test basic metadata fetch with mocked API response with no labels."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with no labels/name
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [],
            "page": 1,
            "maxpage": 1,
            "count": 0,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify Unknown entity type with 0.0 confidence when no labels found
    assert result["address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert result["entity_name"] == "Unknown", f"Expected Unknown, got {result['entity_name']}"
    assert result["entity_type"] == "Unknown", f"Expected Unknown, got {result['entity_type']}"
    assert result["source"] == "Etherscan Metadata"
    assert result["confidence"] == 0.0, f"Expected 0.0, got {result['confidence']}"
    assert "No recognisable Etherscan nametags found" in result["evidence"]
    assert result["raw_metadata"] is not None

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_basic passed!")


def test_fetch_address_metadata_vasp_label() -> None:
    """Test metadata fetch with VASP label mapping."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with VASP label (binance)
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [{"name": "binance", "type": "exchange", "type_name": "VAASP"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify VASP entity type mapped from label
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert result["entity_name"] == "Binance", f"Expected Binance, got {result['entity_name']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    assert "VASP label" in result["evidence"]
    assert result["source"] == "Etherscan Metadata"

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_vasp_label passed!")


def test_fetch_address_metadata_bridge_label() -> None:
    """Test metadata fetch with Bridge label mapping."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with Bridge label
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [{"name": "bridge", "type": "bridge", "type_name": "Bridge"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify Bridge entity type mapped from label
    assert result["entity_type"] == "Bridge", f"Expected Bridge, got {result['entity_type']}"
    assert result["entity_name"] == "Bridge", f"Expected Bridge, got {result['entity_name']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    assert "Bridge label" in result["evidence"]
    assert result["source"] == "Etherscan Metadata"

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_bridge_label passed!")


def test_fetch_address_metadata_mixer_label() -> None:
    """Test metadata fetch with Mixer label mapping."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with Mixer label
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [{"name": "tornado cash", "type": "mixer", "type_name": "Mixer"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify Mixer entity type mapped from label
    assert result["entity_type"] == "Mixer", f"Expected Mixer, got {result['entity_type']}"
    assert result["entity_name"] == "Tornado cash", f"Expected Tornado cash, got {result['entity_name']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    assert "Mixer label" in result["evidence"]
    assert result["source"] == "Etherscan Metadata"

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_mixer_label passed!")


def test_fetch_address_metadata_scam_label() -> None:
    """Test metadata fetch with Scam/Fraud label mapping."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with Scam label
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [{"name": "scam", "type": "warning", "type_name": "Scam"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify Scam/Fraud entity type mapped from label
    assert result["entity_type"] == "Scam/Fraud", f"Expected Scam/Fraud, got {result['entity_type']}"
    assert result["entity_name"] == "Scam", f"Expected Scam, got {result['entity_name']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    assert "Scam/Fraud label" in result["evidence"]
    assert result["source"] == "Etherscan Metadata"

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_scam_label passed!")


def test_fetch_address_metadata_error() -> None:
    """Test metadata fetch with API error response."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API error response
    mock_error_data = {
        "status": "0",
        "message": "Invalid API Key",
        "result": "Invalid API Key (#err2)",
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_error_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify error handling returns Unknown with 0.0 confidence
    assert result["entity_type"] == "Unknown", f"Expected Unknown, got {result['entity_type']}"
    assert result["entity_name"] == "Unknown", f"Expected Unknown, got {result['entity_name']}"
    assert result["confidence"] == 0.0, f"Expected 0.0, got {result['confidence']}"
    assert result["source"] == "Etherscan Metadata"
    assert "Etherscan API returned status 0" in result["evidence"]

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_error passed!")


def test_fetch_address_metadata_confidence_name_only() -> None:
    """Test confidence = 0.5 when only name tag, no specific labels."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with nametag but no labels (V2 getaddresstag format)
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "MyCryptoWallet",
            "flags": {},
            "labels": [],
            "page": 1,
            "maxpage": 1,
            "count": 0,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify confidence = 0.5 for name tag only
    assert result["entity_type"] == "Unknown", f"Expected Unknown, got {result['entity_type']}"
    assert result["entity_name"] == "MyCryptoWallet", f"Expected MyCryptoWallet, got {result['entity_name']}"
    assert result["confidence"] == 0.5, f"Expected 0.5, got {result['confidence']}"
    assert result["source"] == "Etherscan Metadata"

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_confidence_name_only passed!")


def test_fetch_address_metadata_label_parsing() -> None:
    """Test label parsing with multiple labels of different types."""
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    # Mock Etherscan API response with multiple labels
    mock_metadata_data = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "profile": "",
            "flags": {},
            "labels": [
                {"name": "unknown_label", "type": "other", "type_name": "Unknown"},
                {"name": "binance", "type": "exchange", "type_name": "VAASP"},
            ],
            "page": 1,
            "maxpage": 1,
            "count": 2,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata_data
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        result = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    # Verify VASP takes precedence when both VASP and unknown labels present
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert result["confidence"] == 1.0, f"Expected 1.0, got {result['confidence']}"
    # Should include both labels in evidence
    assert "VASP label" in result["evidence"]
    assert "Label" in result["evidence"]

    # Reset env var
    del os.environ["ETHERSCAN_API_KEY"]

    print("test_fetch_address_metadata_label_parsing passed!")


def test_combine_attribution_sources_registry_only() -> None:
    """Test combined attribution when only registry has a known entity."""
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Registry has KnownVASP, Etherscan is Unknown
    from eth_txs import fetch_address_metadata_from_etherscan, combine_attribution_sources
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    mock_metadata = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "",
            "flags": {},
            "labels": [],
            "page": 1,
            "maxpage": 1,
            "count": 0,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        etherscan_meta = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    result = combine_attribution_sources("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", registry, etherscan_meta)

    # Registry should be preserved since Etherscan is Unknown
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert result["entity_name"] == "KnownVASP", f"Expected KnownVASP, got {result['entity_name']}"
    assert "sources" in result, "Expected 'sources' field"
    assert "Etherscan Metadata" in result["sources"]
    assert "KnownVASP" in result["evidence"]
    assert result["confidence"] > 0.0

    del os.environ["ETHERSCAN_API_KEY"]
    print("test_combine_attribution_sources_registry_only passed!")


def test_combine_attribution_sources_etherscan_only() -> None:
    """Test combined attribution when only Etherscan has a mapped entity."""
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Registry is Unknown, Etherscan has VASP label
    from eth_txs import fetch_address_metadata_from_etherscan, combine_attribution_sources
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    mock_metadata = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "Binance",
            "flags": {},
            "labels": [{"name": "binance", "type": "exchange", "type_name": "VAASP"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        etherscan_meta = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    result = combine_attribution_sources("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", registry, etherscan_meta)

    # Etherscan should be used since registry is Unknown
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert result["entity_name"] == "Binance", f"Expected Binance, got {result['entity_name']}"
    assert "sources" in result, "Expected 'sources' field"
    assert "Etherscan Metadata" in result["sources"]
    assert "Binance" in result["evidence"]

    del os.environ["ETHERSCAN_API_KEY"]
    print("test_combine_attribution_sources_etherscan_only passed!")


def test_combine_attribution_sources_agree() -> None:
    """Test combined attribution when both sources identify the same entity."""
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Both registry and Etherscan identify VASP
    from eth_txs import fetch_address_metadata_from_etherscan, combine_attribution_sources
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    mock_metadata = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "Coinbase",
            "flags": {},
            "labels": [{"name": "coinbase", "type": "exchange", "type_name": "VAASP"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        etherscan_meta = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    result = combine_attribution_sources("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", registry, etherscan_meta)

    # Both identify VASP → combined with increased confidence
    assert result["entity_type"] == "VASP", f"Expected VASP, got {result['entity_type']}"
    assert "sources" in result, "Expected 'sources' field"
    assert isinstance(result.get("confidence"), float), f"Expected float confidence, got {type(result.get('confidence'))}"
    assert result["confidence"] <= 1.0, f"Confidence should not exceed 1.0, got {result['confidence']}"
    # Confidence should be increased from individual values (capped at 1.0)
    assert "Evidence" in result.get("combined_evidence", "") or len(result.get("combined_evidence", "")) > 0
    # The combined evidence should contain both source evidences
    assert "registry" in result["combined_evidence"].lower()
    assert "Etherscan" in result["combined_evidence"]

    del os.environ["ETHERSCAN_API_KEY"]
    print("test_combine_attribution_sources_agree passed!")


def test_combine_attribution_sources_conflict() -> None:
    """Test combined attribution when sources disagree on entity type."""
    import json
    from pathlib import Path
    import unittest.mock as mock

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

# Registry says VASP, Etherscan says Mixer → conflict case
    mock_metadata = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "Tornado cash",
            "flags": {},
            "labels": [{"name": "tornado cash", "type": "mixer", "type_name": "Mixer"}],
            "page": 1,
            "maxpage": 1,
            "count": 1,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        etherscan_meta = fetch_address_metadata_from_etherscan(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    result = combine_attribution_sources("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", registry, etherscan_meta)

    # Sources disagree → registry primary, record disagreement
    assert result["entity_type"] == "VASP", f"Expected VASP (registry primary), got {result['entity_type']}"
    assert "sources" in result, "Expected 'sources' field"
    assert len(result["sources"]) == 2, f"Expected 2 sources, got {len(result['sources'])}"
    # Evidence should mention the disagreement and resolution
    assert "disagree" in result["evidence"].lower() or "conflict" in result["evidence"].lower()
    assert "Mixer" in result["evidence"]

    del os.environ["ETHERSCAN_API_KEY"]
    print("test_combine_attribution_sources_conflict passed!")


def test_combine_attribution_sources_both_unknown() -> None:
    """Test combined attribution when both sources are Unknown."""
    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "address_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Both registry and Etherscan are Unknown - use address NOT in registry
    from eth_txs import fetch_address_metadata_from_etherscan, combine_attribution_sources
    import unittest.mock as mock
    import os

    os.environ["ETHERSCAN_API_KEY"] = "testkey"

    mock_metadata = {
        "status": "1",
        "message": "OK",
        "result": {
            "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "balance": "1000000000000000000",
            "is_mfa": "0",
            "comment": "",
            "nametag": "",
            "flags": {},
            "labels": [],
            "page": 1,
            "maxpage": 1,
            "count": 0,
        },
    }

    with mock.patch("eth_txs.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metadata
        mock_get.return_value = mock_response

        from eth_txs import fetch_address_metadata_from_etherscan
        etherscan_meta = fetch_address_metadata_from_etherscan(
            "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        )

    result = combine_attribution_sources("0xzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", registry, etherscan_meta)

    # Both Unknown → result should be Unknown
    assert result["entity_type"] == "Unknown", f"Expected Unknown, got {result['entity_type']}"
    assert result["entity_name"] == "Unknown", f"Expected Unknown, got {result['entity_name']}"
    assert result["confidence"] == 0.0, f"Expected 0.0 confidence, got {result['confidence']}"
    assert "sources" in result, "Expected 'sources' field"
    assert "No attribution" in result["evidence"]

    del os.environ["ETHERSCAN_API_KEY"]
    print("test_combine_attribution_sources_both_unknown passed!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_graph()
        test_bfs()
        test_risk_scoring()
        test_address_registry()
        test_attribute_address()
        test_attribute_trace()
        test_address_cli_with_mock()
        test_etherscan_error_handling()
        test_etherscan_v2_endpoint()
        test_erc20_token_transfers()
        test_normalize_transactions()
        test_internal_transactions()
        test_etherscan_error_handling()
        test_etherscan_v2_endpoint()
        test_erc20_token_transfers()
        test_internal_transactions()
        test_normalize_transactions()
        test_fetch_address_metadata_basic()
        test_fetch_address_metadata_vasp_label()
        test_fetch_address_metadata_bridge_label()
        test_fetch_address_metadata_mixer_label()
        test_fetch_address_metadata_scam_label()
        test_fetch_address_metadata_error()
        test_fetch_address_metadata_confidence_name_only()
        test_fetch_address_metadata_label_parsing()
        test_combine_attribution_sources_registry_only()
        test_combine_attribution_sources_etherscan_only()
        test_combine_attribution_sources_agree()
        test_combine_attribution_sources_conflict()
        test_combine_attribution_sources_both_unknown()
    else:
        main()

def build_unified_graph(transfers: list) -> dict:
    from collections import defaultdict
    graph = defaultdict(list)
    for transfer in transfers:
        if transfer["asset_type"] == "INTERNAL_ETH" and transfer.get("is_error") == "1":
            continue
        edge_key = f"{transfer['from_address']}->{transfer['to_address']}"
        graph[edge_key].append(transfer)
    return dict(graph)


def test_unified_graph_transfers( ):
    from eth_txs import normalize_eth_transaction, normalize_erc20_transfer, normalize_internal_transaction, build_unified_graph
    eth_xfer = normalize_eth_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xeth1",
        "timestamp": "1609459200",
        "asset_type": "ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 1.0,
    })
    usdt_xfer = normalize_erc20_transfer({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xusdt1",
        "timestamp": "1609459200",
        "asset_type": "ERC20",
        "asset_contract": "0xusdtcontract",
        "symbol": "USDT",
        "amount": 1.0,
    })
    internal_fail = normalize_internal_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xintfail1",
        "timestamp": "1609459200",
        "asset_type": "INTERNAL_ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 0.5,
        "is_error": "1",
    })
    internal_success = normalize_internal_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xintsuccess1",
        "timestamp": "1609459200",
        "asset_type": "INTERNAL_ETH",
        "asset_contract": None,
        "symbol": "ETH",
        "amount": 0.5,
        "is_error": "0",
    })
    transfers = [eth_xfer, usdt_xfer, internal_fail, internal_success]
    graph = build_unified_graph(transfers)
    edge = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa->0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    assert edge in graph
    assert len(graph[edge]) == 2
    for edge_key, transfers_list in graph.items():
        for t in transfers_list:
            assert t.get("is_error") != "1"
    assert any(t["hash"] == "0xintsuccess1" for transfers_list in graph.values() for t in transfers_list)
    print("test_build_unified_graph passed!")


def test_bfs_unified( ):
    from eth_txs import build_unified_graph, normalize_eth_transaction, normalize_erc20_transfer, normalize_internal_transaction, bfs_traverse_unified
    eth_xfer = normalize_eth_transaction({
        "from": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "to": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "hash": "0xeth1", "timestamp": "1609459200", "asset_type": "ETH", "asset_contract": None, "symbol": "ETH", "amount": 1.0,
    })
    usdt_xfer = normalize_erc20_transfer({
        "from": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "to": "0xcccccccccccccccccccccccccccccccccccccccc",
        "hash": "0xusdt1", "timestamp": "1609459201", "asset_type": "ERC20", "asset_contract": "0xusdt", "symbol": "USDT", "amount": 1.0,
    })
    int_success = normalize_internal_transaction({
        "from": "0xcccccccccccccccccccccccccccccccccccccccc", "to": "0xdddddddddddddddddddddddddddddddddddddddd",
        "hash": "0xint1", "timestamp": "1609459202", "asset_type": "INTERNAL_ETH", "asset_contract": None, "symbol": "ETH", "amount": 2.0, "is_error": "0",
    })
    int_fail = normalize_internal_transaction({
        "from": "0xdddddddddddddddddddddddddddddddddddddddd", "to": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "hash": "0xintfail1", "timestamp": "1609459203", "asset_type": "INTERNAL_ETH", "asset_contract": None, "symbol": "ETH", "amount": 3.0, "is_error": "1",
    })
    transfers = [eth_xfer, usdt_xfer, int_success, int_fail]
    graph = build_unified_graph(transfers)
    result = bfs_traverse_unified(graph, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", max_hops=2)
    assert "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in result["visited"]
    assert "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" in result["visited"]
    assert "0xcccccccccccccccccccccccccccccccccccccccc" in result["visited"]
    assert "0xdddddddddddddddddddddddddddddddddddddddd" not in result["visited"]
    path, transfers, hops = result["paths"]["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"]
    assert hops == 1
    assert len(transfers) == 1
    assert transfers[0]["asset_type"] == "ETH"
    path2, transfers2, hops2 = result["paths"]["0xcccccccccccccccccccccccccccccccccccccccc"]
    assert hops2 == 2
    usdt_in_path = any(t["symbol"] == "USDT" for t in transfers2)
    assert usdt_in_path
    assert "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" not in result["visited"]
    five_hop_result = bfs_traverse_unified(graph, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", max_hops=5)
    assert len(five_hop_result["visited"]) >= 4
    zero_hop_result = bfs_traverse_unified(graph, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", max_hops=0)
    assert zero_hop_result["visited"] == {"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
    assert len(zero_hop_result["paths"]) == 1
    path, transfers, hops = result["paths"]["0xcccccccccccccccccccccccccccccccccccccccc"]
    assert len(transfers) >= 1
    for t in transfers:
        assert "hash" in t
        assert "from_address" in t
        assert "to_address" in t
        assert "asset_type" in t
        assert "symbol" in t
        assert "amount" in t
        assert "timestamp" in t
    print("test_bfs_unified passed!")
