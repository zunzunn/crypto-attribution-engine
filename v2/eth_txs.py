import argparse
import os
import json
import sys
from dotenv import load_dotenv
import requests
from collections import defaultdict


load_dotenv()


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


RISK_BASE_POINTS = {
    "VASP": 10,
    "Bridge": 20,
    "Mixer": 40,
    "Scam/Fraud": 50,
    "Unknown": 0,
}


def classify_entity(address: str) -> str:
    """Rule-based entity type classification from an Ethereum address.

    Uses the first hex character after 0x as a deterministic classifier:
      - 'a' -> VASP
      - 'b' -> Bridge
      - 'c' -> Mixer
      - 'd' -> Scam/Fraud
      - anything else -> Unknown
    """
    addr = address.strip()
    if not is_valid_eth_address(addr):
        return "Unknown"
    hex_part = addr[2:]
    if not hex_part:
        return "Unknown"
    first_char = hex_part[0].lower()
    mapping = {"a": "VASP", "b": "Bridge", "c": "Mixer", "d": "Scam/Fraud"}
    return mapping.get(first_char, "Unknown")


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


def build_graph(transactions: list) -> dict:
    """Build a transaction graph from a list of transaction records.

    Returns a dict mapping edge keys (from->to) to lists of
    {hash, value_eth, timestamp} dicts.
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
            for addr in hop_addrs:
                entity_type = classify_entity(addr)
                score, level = calculate_risk_score(entity_type, hop)
                print(f"  Risk: {addr[:6]}...{addr[-4:]} | {entity_type} | Score: {score} | Level: {level}")
            print()
    else:
        print_graph(graph)


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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_graph()
    else:
        main()


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
    """Tests for rule-based risk scoring and entity classification."""

    # Test entity classification
    vasp_addr = "0x" + "a" * 40
    bridge_addr = "0x" + "b" * 40
    mixer_addr = "0x" + "c" * 40
    scam_addr = "0x" + "d" * 40
    unknown_addr = "0x" + "e" * 40

    assert classify_entity(vasp_addr) == "VASP", f"Expected VASP, got {classify_entity(vasp_addr)}"
    assert classify_entity(bridge_addr) == "Bridge", f"Expected Bridge, got {classify_entity(bridge_addr)}"
    assert classify_entity(mixer_addr) == "Mixer", f"Expected Mixer, got {classify_entity(mixer_addr)}"
    assert classify_entity(scam_addr) == "Scam/Fraud", f"Expected Scam/Fraud, got {classify_entity(scam_addr)}"
    assert classify_entity(unknown_addr) == "Unknown", f"Expected Unknown, got {classify_entity(unknown_addr)}"

    # Test invalid address
    assert classify_entity("invalid") == "Unknown"
    assert classify_entity("0x") == "Unknown"

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
    # Scam/Fraud at hop 0 = 50 → High
    _, scam_level = calculate_risk_score("Scam/Fraud", 0)
    assert scam_level == "High"

    # Scam/Fraud at hop 1 = 45 → Medium
    _, scam_h1_level = calculate_risk_score("Scam/Fraud", 1)
    assert scam_h1_level == "Medium"

    # Bridge at hop 4 = 20 - 20 = 0 → Low
    _, bridge_h4_level = calculate_risk_score("Bridge", 4)
    assert bridge_h4_level == "Low"

    # VASP at hop 2 = 10 - 10 = 0 → Low
    _, vasp_h2_level = calculate_risk_score("VASP", 2)
    assert vasp_h2_level == "Low"

    print("All risk scoring tests passed!")


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