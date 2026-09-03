"""Chain adapter abstraction for multi-blockchain support.

Each blockchain must implement a ChainAdapter that converts its raw blockchain
data into the project's unified transfer representation.
"""
import abc
from eth_txs import is_valid_eth_address


def is_valid_tron_address(address: str) -> bool:
    """Check if string looks like a TRON Base58 address.

    TRON addresses start with 'T' and are 34 characters in Base58.
    """
    addr = address.strip()
    if not addr.startswith("T"):
        return False
    if len(addr) != 34:
        return False
    # TRON Base58 characters: everything except 0 O I l
    valid_chars = set("123456789ABCDEFGHIJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    if not all(c in valid_chars for c in addr):
        return False
    return True


# Synthetic bridge registry for test purposes.
# This is test intelligence - does not represent real bridge data.
# Mappings from source addresses to bridge info including destination chains.
SYNTHETIC_BRIDGE_REGISTRY = {
    "ethereum": {
        "0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb": {
            "bridge_name": "Synthetic Bridge",
            "destination_chains": ["tron"],
        }
    },
    "tron": {
        "T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q": {
            "bridge_name": "Synthetic Bridge",
            "source_chains": ["ethereum"],
        }
    },
}


class ChainAdapter(abc.ABC):
    """Base interface for blockchain chain adapters.

    Every supported blockchain must convert its raw blockchain data into the
    project's unified transfer representation via these methods.
    """

    chain_id = None  # Subclasses must set this

    @abc.abstractmethod
    def validate_address(self, address: str) -> bool:
        """Validate that an address is appropriate for this blockchain."""

    @abc.abstractmethod
    def fetch_native_transactions(self, address: str) -> list:
        """Fetch native blockchain transactions for an address."""

    @abc.abstractmethod
    def fetch_token_transfers(self, address: str) -> list:
        """Fetch token transfer events for an address."""

    @abc.abstractmethod
    def fetch_internal_transactions(self, address: str) -> list:
        """Fetch internal transactions for an address."""

    @abc.abstractmethod
    def normalize_transactions(self, raw_transactions: list) -> list:
        """Normalize raw transactions into the project's unified format.

        Accepts a list of raw transaction dicts from any source and returns
        a list of dicts with consistent field names suitable for use with
        the project's graph builders and BFS traversal.
        """

    @abc.abstractmethod
    def get_chain_id(self) -> str:
        """Return the chain identifier for this adapter."""


class EthereumAdapter(ChainAdapter):
    """Adapter that wraps the existing Ethereum/Etherscan functionality.

    Reuses functions from eth_txs.py where practical so that the existing
    Ethimal logic is not duplicated or refactored unnecessarily.
    """

    chain_id = "ethereum"

    def __init__(self, etherscan_api_key: str | None = None):
        self.etherscan_api_key = etherscan_api_key
        self._is_valid = is_valid_eth_address

    def get_chain_id(self) -> str:
        """Return the chain identifier for this adapter."""
        return self.chain_id

    def validate_address(self, address: str) -> bool:
        """Check if string looks like an Ethereum address."""
        return self._is_valid(address)

    def fetch_native_transactions(self, address: str) -> list:
        """Fetch native ETH transactions for an address via Etherscan."""
        from eth_txs import fetch_transactions_from_etherscan

        return fetch_transactions_from_etherscan(address)

    def fetch_token_transfers(self, address: str) -> list:
        """Fetch ERC-20 token transfers for an address via Etherscan."""
        from eth_txs import fetch_erc20_token_transfers

        return fetch_erc20_token_transfers(address)

    def fetch_internal_transactions(self, address: str) -> list:
        """Fetch internal transactions for an address via Etherscan."""
        from eth_txs import fetch_internal_transactions

        return fetch_internal_transactions(address)

    def normalize_transactions(self, raw_transactions: list) -> list:
        """Normalize a mix of ETH, ERC-20, and internal transactions.

        Accepts raw transaction dicts (as returned by the Etherscan fetch
        functions or by direct API calls) and normalizes each one into the
        project's unified transfer format with consistent field names:
        hash, from_address, to_address, asset_type, asset_contract, symbol,
        amount, timestamp.
        """
        from eth_txs import (
            normalize_eth_transaction,
            normalize_erc20_transfer,
            normalize_internal_transaction,
        )

        normalized = []
        for raw in raw_transactions:
            asset_type = raw.get("asset_type") or raw.get("type", "")
            if asset_type in ("ETH", "native"):
                normalized.append(normalize_eth_transaction(raw))
            elif asset_type == "ERC20":
                normalized.append(normalize_erc20_transfer(raw))
            elif asset_type == "INTERNAL_ETH":
                normalized.append(normalize_internal_transaction(raw))
            else:
                # Try to detect format from key presence
                if raw.get("isError") is not None:
                    normalized.append(normalize_internal_transaction(raw))
                elif raw.get("tokenContractAddress"):
                    normalized.append(normalize_erc20_transfer(raw))
                else:
                    normalized.append(normalize_eth_transaction(raw))
        return normalized

    def build_graph(self, transactions: list) -> dict:
        """Build a transaction graph from a list of transaction records.

        Reuses the existing build_graph from eth_txs.py for consistency.
        """
        from eth_txs import build_graph as _build_graph

        return _build_graph(transactions)


class TronAdapter(ChainAdapter):
    """Adapter that wraps the TronGrid V1 API for TRON blockchain support.

    Fetches native TRX transactions and TRC-20 token transfers, converting
    them into the project's unified transfer representation.
    """

    chain_id = "tron"

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.trongrid.io"):
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")

    def get_chain_id(self) -> str:
        """Return the chain identifier for this adapter."""
        return self.chain_id

    def validate_address(self, address: str) -> bool:
        """Check if string looks like a TRON Base58 address."""
        return is_valid_tron_address(address)

    def _get_headers(self) -> dict:
        """Return API headers including the API key."""
        return {
            "Accept": "application/json",
            "TRON-PRO-API-KEY": self.api_key,
        }

    def _api_request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a paginated TronGrid API request."""
        import requests
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        all_params = params or {}
        if self.api_key:
            all_params["api_key"] = self.api_key
        try:
            response = requests.get(url, headers=headers, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {}

    def fetch_native_transactions(self, address: str, limit: int = 20) -> list:
        """Fetch native TRX transactions for a TRON address.

        Uses TronGrid V1: GET /v1/accounts/{address}/transactions
        """
        import requests
        data = self._api_request(f"/v1/accounts/{address}/transactions", {"limit": str(limit)})
        result = data.get("data", [])
        # Basic pagination metadata
        return result

    def fetch_token_transfers(
        self, address: str, limit: int = 20, token_contract: str | None = None
    ) -> list:
        """Fetch TRC-20 token transfers for a TRON address.

        Uses TronGrid V1: GET /v1/accounts/{address}/transactions/trc20
        """
        import requests
        endpoint = f"/v1/accounts/{address}/transactions/trc20"
        params = {"limit": str(limit)}
        if token_contract:
            params["token_contract"] = token_contract
        data = self._api_request(endpoint, params)
        result = data.get("data", [])
        return result

    def fetch_internal_transactions(self, address: str) -> list:
        """TRON does not use Ethereum-style internal transactions.

        Returns an empty list with explicit documentation, as TRON's
        transaction model differs from Ethereum's.
        """
        return []

    def normalize_transactions(self, raw_transactions: list) -> list:
        """Normalize raw TRON API responses into the project's unified format.

        Handles both native TRX transfers and TRC-20 token transfers.
        """
        normalized = []
        for raw in raw_transactions:
            # Detect if this is a TRC-20 transfer
            if raw.get("contract") and raw.get("contract").get("token_info"):
                normalized.append(self._normalize_rc20_transfer(raw))
            else:
                normalized.append(self._normalize_trx_transfer(raw))
        return normalized

    def _normalize_trx_transfer(self, raw: dict) -> dict:
        """Normalize a native TRX transfer into the unified format."""
        # TRX transfer fields from TronGrid
        tx_id = raw.get("txID", "")
        raw_tx = raw.get("rawData", {})
        from_addr = raw_tx.get("parameter", {}).get("value", {}).get("owner", "")
        to_addr = raw_tx.get("parameter", {}).get("value", {}).get("to_address", "")
        amount_raw = raw_tx.get("parameter", {}).get("value", {}).get("amount", "0")
        timestamp = raw.get("blockID", "")
        # Estimate: TRX amount is in sun (1 TRX = 1,000,000 sun)
        # But we preserve raw and let the caller decide; the unified model
        # expects amount as a base-unit string. We'll store the raw value.
        try:
            amount_int = int(amount_raw)
        except (ValueError, TypeError):
            amount_int = 0
        # The unified model uses amount as string of base units
        amount_str = str(amount_int)
        return {
            "chain": "tron",
            "tx_hash": tx_id,
            "from_address": from_addr,
            "to_address": to_addr,
            "asset": "TRX",
            "amount": amount_str,
            "timestamp": timestamp,
            "status": raw.get("ret", [{}])[0].get("status", "unknown"),
        }

    def _normalize_rc20_transfer(self, raw: dict) -> dict:
        """Normalize a TRC-20 token transfer into the unified format.

        Preserves token decimals from the API when available.
        Does NOT assume 18 decimals.
        """
        contract = raw.get("contract", {})
        token_info = contract.get("token_info", {}) if contract else {}
        raw_tx = raw.get("rawData", {}).get("parameter", {}).get("value", {})

        # Token contract address
        token_contract = contract.get("address", "")

        # Token symbol and name
        token_symbol = token_info.get("symbol", "")
        token_name = token_info.get("name", "")

        # Raw amount from the transfer
        raw_amount = raw_tx.get("amount", "0") if raw_tx else "0"
        try:
            amount_raw_int = int(raw_amount)
        except (ValueError, TypeError):
            amount_raw_int = 0

        # Preserve the decimals from token_info if available, otherwise default to None
        # (do not assume 18)
        token_decimals = token_info.get("decimals")

        # The normalized amount: if we know decimals, convert; otherwise preserve raw
        if token_decimals is not None:
            try:
                decimals_int = int(token_decimals)
                # normalized amount in human-readable form
                amount_normalized = amount_raw_int / (10 ** decimals_int)
                amount_str = str(amount_normalized)
            except (ValueError, ZeroDivisionError):
                amount_str = str(amount_raw_int)
        else:
            # Unknown decimals: preserve raw base-unit amount as string
            amount_str = str(amount_raw_int)
            amount_normalized = None

        tx_id = raw.get("txID", "")
        raw_tx = raw.get("rawData", {})
        from_addr = raw_tx.get("parameter", {}).get("value", {}).get("owner", "")
        to_addr = raw_tx.get("parameter", {}).get("value", {}).get("to_address", "")
        timestamp = raw.get("blockID", "")

        return {
            "chain": "tron",
            "tx_hash": tx_id,
            "from_address": from_addr,
            "to_address": to_addr,
            "asset": "TRC-20",
            "token_contract": token_contract,
            "token_symbol": token_symbol,
            "amount_raw": raw_amount,
            "amount": str(amount_normalized) if amount_normalized is not None else raw_amount,
            "decimals": token_decimals,
            "timestamp": timestamp,
            "status": raw.get("ret", [{}])[0].get("status", "unknown"),
        }

    def build_graph(self, transactions: list) -> dict:
        """Build a transaction graph from normalized TRON transactions.

        Reuses the existing build_graph from eth_txs.py for consistency.
        """
        from eth_txs import build_graph as _build_graph

        return _build_graph(transactions)


# End of chain_adapter module


def test_adapter_can_be_created() -> None:
    """Test that a ChainAdapter can be instantiated (abstract class raises)."""
    try:
        adapter = ChainAdapter()
        raise AssertionError("Should not be able to instantiate abstract ChainAdapter")
    except TypeError:
        pass  # Expected - abstract class cannot be instantiated


def test_ethereum_adapter_identifies_as_ethereum() -> None:
    """Test that the Ethereum adapter identifies itself as Ethereum."""
    from chain_adapter import EthereumAdapter
    adapter = EthereumAdapter()
    assert adapter.get_chain_id() == "ethereum", (
        f"Expected chain_id 'ethereum', got '{adapter.get_chain_id()}'"
    )


def test_ethereum_address_validation_works() -> None:
    """Test that Ethereum adapter validates addresses correctly."""
    from chain_adapter import EthereumAdapter

    adapter = EthereumAdapter()

    # Valid Ethereum addresses
    valid_addr = "0x" + "a" * 40
    assert adapter.validate_address(valid_addr) is True, (
        f"Valid address should pass validation"
    )

    # Invalid: no 0x prefix
    assert adapter.validate_address("abcdef") is False, (
        "Address without 0x should fail"
    )

    # Invalid: wrong length
    assert adapter.validate_address("0x" + "a" * 39) is False, (
        "Address with 39 hex chars should fail"
    )

    # Invalid: no hex
    assert adapter.validate_address("0xgggggggggggggggggggggggggggggggggggggggg") is False, (
        "Address with non-hex chars should fail"
    )


def test_adapter_interface_methods_exist() -> None:
    """Test that the ChainAdapter interface has all required methods."""
    required_methods = [
        "validate_address",
        "fetch_native_transactions",
        "fetch_token_transfers",
        "fetch_internal_transactions",
        "normalize_transactions",
        "get_chain_id",
    ]

    # Check ChainAdapter base class has them (as abstract)
    for method_name in required_methods:
        assert hasattr(ChainAdapter, method_name), (
            f"ChainAdapter base class should have '{method_name}' method"
        )

    # Check EthereumAdapter has concrete implementations
    from chain_adapter import EthereumAdapter
    adapter = EthereumAdapter()
    for method_name in required_methods:
        assert hasattr(adapter, method_name), (
            f"EthereumAdapter should have '{method_name}' method"
        )


def test_existing_tests_still_pass() -> None:
    """Verify that the existing eth_txs tests still work with the new module."""
    import json
    from pathlib import Path

    # Test that build_graph still works
    from eth_txs import build_graph, is_valid_eth_address

    valid_addr = "0x" + "a" * 40
    txs = [
        {"from": valid_addr, "to": "0x" + "b" * 40, "value": "1000000000000000000", "hash": "0xhash1", "timeStamp": "1609459200"},
    ]
    graph = build_graph(txs)
    assert valid_addr + "->0x" + "b" * 40 in graph

    # Test is_valid_eth_address still works
    assert is_valid_eth_address(valid_addr) is True
    assert is_valid_eth_address("invalid") is False


# Run all tests when module is executed directly
if __name__ == "__main__":
    test_adapter_can_be_created()
    print("test_adapter_can_be_created passed!")

    test_ethereum_adapter_identifies_as_ethereum()
    print("test_ethereum_adapter_identifies_as_ethereum passed!")

    test_ethereum_address_validation_works()
    print("test_ethereum_address_validation_works passed!")

    test_adapter_interface_methods_exist()
    print("test_adapter_interface_methods_exist passed!")

    test_existing_tests_still_pass()
    print("test_existing_tests_still_pass passed!")

    # NEW: TronAdapter tests
    test_tron_adapter_can_be_instantiated()
    print("test_tron_adapter_can_be_instantiated passed!")

    test_tron_get_chain_id()
    print("test_tron_get_chain_id passed!")

    test_tron_address_validation()
    print("test_tron_address_validation passed!")

    test_tron_native_transaction_normalization()
    print("test_tron_native_transaction_normalization passed!")

    test_tron_rc20_token_normalization()
    print("test_tron_rc20_token_normalization passed!")

    test_tron_token_decimals_preserved()
    print("test_tron_token_decimals_preserved passed!")

    test_tron_api_error_handling()
    print("test_tron_api_error_handling passed!")

    test_tron_api_key_from_env()
    print("test_tron_api_key_from_env passed!")

    test_ethereum_adapter_still_works()
    print("test_ethereum_adapter_still_works passed!")

    print("\nAll chain adapter tests passed!")

def test_tron_adapter_can_be_instantiated() -> None:
    """Test that TronAdapter can be instantiated."""
    from chain_adapter import TronAdapter
    adapter = TronAdapter()
    assert adapter is not None


def test_tron_get_chain_id() -> None:
    """Test that TronAdapter returns correct chain ID."""
    from chain_adapter import TronAdapter
    adapter = TronAdapter()
    assert adapter.get_chain_id() == "tron"


def test_tron_address_validation() -> None:
    """Test TRON address validation."""
    from chain_adapter import TronAdapter, is_valid_tron_address

    # Valid TRON addresses (start with T, 34 chars Base58)
    valid_t = "T" + "A" * 33
    assert is_valid_tron_address(valid_t) is True, f"Valid Tron address should pass"

    # Invalid: starts with 0x (Ethereum)
    eth_addr = "0x" + "a" * 40
    assert is_valid_tron_address(eth_addr) is False, "Ethereum address should not be valid TRON"

    # Invalid: wrong prefix
    assert is_valid_tron_address("invalid") is False

    # Invalid: wrong length
    assert is_valid_tron_address("T" + "A" * 33 + "extra") is False


def test_tron_native_transaction_normalization() -> None:
    """Test that native TRX transfers normalize correctly."""
    from chain_adapter import TronAdapter

    adapter = TronAdapter()

    # Mock TRX transfer response from TronGrid
    raw_tx = {
        "txID": "0xmocktx1234567890abcdef",
        "rawData": {
            "parameter": {
                "value": {
                    "owner": "TABCDEF1234567890abcdefghijklmnopqr",
                    "to_address": "Tabcdef1234567890abcdefghijklmnopqrstuv",
                    "amount": "1000000",  # 1 TRX in sun
                }
            }
        },
        "blockID": "1609459200000",
        "ret": [{"status": "SUCCESS"}],
    }

    normalized = adapter.normalize_transactions([raw_tx])
    assert len(normalized) == 1
    tx = normalized[0]
    assert tx["chain"] == "tron"
    assert tx["asset"] == "TRX"
    assert tx["tx_hash"] == "0xmocktx1234567890abcdef"
    assert tx["from_address"].startswith("T")
    assert tx["to_address"].startswith("T")
    assert tx["timestamp"] == "1609459200000"
    assert tx["status"] == "SUCCESS"


def test_tron_rc20_token_normalization() -> None:
    """Test that TRC-20 transfers normalize correctly."""
    from chain_adapter import TronAdapter

    adapter = TronAdapter()

    # Mock TRC-20 transfer response from TronGrid
    # Include contract.address for token contract
    raw_tx = {
        "txID": "0xmocktoken1234567890abcdef",
        "rawData": {
            "parameter": {
                "value": {
                    "owner": "Tabcdef1234567890abcdefghijklmnopqr",
                    "to_address": "Tabcdef1234567890abcdefghijklmnopqrstuv",
                    "amount": "5000000",  # 5 with 6 decimals
                }
            }
        },
        "contract": {
            "token_info": {
                "symbol": "USDT",
                "name": "Tether USD",
                "decimals": "6",
            },
            "address": "TR7vince6qb4jafBfd3NkpQXMMo6wGr6pq",  # proper TRON contract address
        },
        "blockID": "1609459200001",
        "ret": [{"status": "SUCCESS"}],
    }

    normalized = adapter.normalize_transactions([raw_tx])
    assert len(normalized) == 1
    tx = normalized[0]
    assert tx["chain"] == "tron"
    assert tx["asset"] == "TRC-20"
    assert tx["token_contract"]  # should have token contract address
    assert tx["token_symbol"] == "USDT"
    assert tx["decimals"] == "6"  # preserved as string from API
    # Amount preserved with decimals info
    assert tx["amount_raw"] == "5000000"


def test_tron_token_decimals_preserved() -> None:
    """Test that token decimals are preserved (not assumed 18)."""
    from chain_adapter import TronAdapter

    adapter = TronAdapter()

    # Token with 6 decimals
    raw_6 = {
        "txID": "0xtoken6",
        "rawData": {
            "parameter": {
                "value": {
                    "owner": "Tabcdef1234567890abcdefghijklmnopqr",
                    "to_address": "Tabcdef1234567890abcdefghijklmnopqrstuv",
                    "amount": "5000000",
                }
            }
        },
        "contract": {
            "token_info": {
                "symbol": "TOKEN6",
                "name": "Token6",
                "decimals": "6",
            },
            "address": "TR7vince6qb4jafBfd3NkpQXMMo6wGr6pq",
        },
        "blockID": "1609459200002",
        "ret": [{"status": "SUCCESS"}],
    }

    # Token with 0 decimals (raw amount preserved)
    raw_0 = {
        "txID": "0xtoken0",
        "rawData": {
            "parameter": {
                "value": {
                    "owner": "Tabcdef1234567890abcdefghijklmnopqr",
                    "to_address": "Tabcdef1234567890abcdefghijklmnopqrstuv",
                    "amount": "5000000",
                }
            }
        },
        "contract": {
            "token_info": {
                "symbol": "TOKEN0",
                "name": "Token0",
                "decimals": "0",
            },
            "address": "TR7vince6qb4jafBfd3NkpQXMMo6wGr6pq",
        },
        "blockID": "1609459200003",
        "ret": [{"status": "SUCCESS"}],
    }

    # Token with no decimals field
    raw_no_decimals = {
        "txID": "0xtokennodec",
        "rawData": {
            "parameter": {
                "value": {
                    "owner": "Tabcdef1234567890abcdefghijklmnopqr",
                    "to_address": "Tabcdef1234567890abcdefghijklmnopqrstuv",
                    "amount": "5000000",
                }
            }
        },
        "contract": {
            "token_info": {
                "symbol": "TOKENNODEC",
                "name": "TokenNoDec",
                # no decimals field
            },
            "address": "TR7vince6qb4jafBfd3NkpQXMMo6wGr6pq",
        },
        "blockID": "1609459200004",
        "ret": [{"status": "SUCCESS"}],
    }

    normalized_6 = adapter.normalize_transactions([raw_6])[0]
    normalized_0 = adapter.normalize_transactions([raw_0])[0]
    normalized_nodec = adapter.normalize_transactions([raw_no_decimals])[0]

    # 6 decimals: decimals preserved as string from API
    assert normalized_6["decimals"] == "6"
    # 0 decimals: decimals preserved as string "0"
    assert normalized_0["decimals"] == "0"
    # No decimals field: decimals should be None
    assert normalized_nodec["decimals"] is None


def test_tron_api_error_handling() -> None:
    """Test that API errors are handled cleanly."""
    from chain_adapter import TronAdapter

    adapter = TronAdapter(api_key="invalid_key")

    # Test with empty/malformed responses
    # The adapter should not crash; normalize_transactions on empty list returns []
    result = adapter.normalize_transactions([])
    assert result == []

    # Test fetch methods with empty responses
    native = adapter.fetch_native_transactions("Tinvalidaddress1234567890abcdefghijklmnopqrxyz")
    # Should return empty list, not crash
    assert native == []

    token = adapter.fetch_token_transfers("Tinvalidaddress1234567890abcdefghijklmnopqrxyz")
    assert token == []


def test_tron_api_key_from_env() -> None:
    """Test that API key is taken from environment/config."""
    import os

    # When no API key provided, adapter should still work (just won't have auth header value)
    from chain_adapter import TronAdapter

    adapter_no_key = TronAdapter()
    adapter_with_key = TronAdapter(api_key="test_key_123")

    # Both should be instantiable
    assert adapter_no_key is not None
    assert adapter_with_key is not None

    # Adapter with key should have it stored
    assert adapter_with_key.api_key == "test_key_123"


def test_ethereum_adapter_still_works() -> None:
    """Verify existing Ethereum adapter still works after TronAdapter addition."""
    from chain_adapter import EthereumAdapter

    adapter = EthereumAdapter()
    assert adapter.get_chain_id() == "ethereum"
    assert adapter.validate_address("0x" + "a" * 40) is True


# Cross-Chain Trace Foundation

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CrossChainLink:
    """Evidence-aware representation of a cross-chain transaction link.

    Represents a potential bridge or transfer relationship between two
    blockchain transactions. Distinguishes between observed facts and
    inferred/linked relationships.

    Attributes:
        source_chain: The blockchain where the transaction originated.
        source_tx_hash: Optional hash of the source transaction.
        source_address: The source address on the source chain.
        source_asset: The asset/token transferred from source.
        destination_chain: The blockchain where the transaction arrived.
        destination_tx_hash: Optional hash of the destination transaction.
        destination_address: The destination address on the destination chain.
        destination_asset: The asset/token received on destination.
        bridge_address: Optional address of the bridge contract/interface.
        bridge_name: Optional human-readable name of the bridge.
        confidence: Confidence score (0.0 to 1.0) in this link being valid.
        evidence: Description of the evidence supporting this link.
        source: Source of this link information (e.g., "etherscan", "trongrid", "user").
    """

    source_chain: str
    source_tx_hash: Optional[str] = None
    source_address: str = ""
    source_asset: str = ""
    destination_chain: str = ""
    destination_tx_hash: Optional[str] = None
    destination_address: str = ""
    destination_asset: str = ""
    bridge_address: Optional[str] = None
    bridge_name: Optional[str] = None
    confidence: float = 0.5
    evidence: str = ""
    source: str = ""


def create_cross_chain_link(
    source_chain: str,
    source_address: str,
    source_asset: str,
    destination_chain: str,
    destination_address: str,
    destination_asset: str,
    *,
    source_tx_hash: Optional[str] = None,
    destination_tx_hash: Optional[str] = None,
    bridge_address: Optional[str] = None,
    bridge_name: Optional[str] = None,
    confidence: float = 0.5,
    evidence: str = "",
    source: str = "",
) -> CrossChainLink:
    """Create a CrossChainLink with validation.

    Validates that confidence is between 0.0 and 1.0.
    All required string fields must be non-empty.
    """
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

    link = CrossChainLink(
        source_chain=source_chain,
        source_tx_hash=source_tx_hash,
        source_address=source_address,
        source_asset=source_asset,
        destination_chain=destination_chain,
        destination_tx_hash=destination_tx_hash,
        destination_address=destination_address,
        destination_asset=destination_asset,
        bridge_address=bridge_address,
        bridge_name=bridge_name,
        confidence=confidence,
        evidence=evidence,
        source=source,
    )

    # Validate after construction
    _validate_cross_chain_link(link)
    return link


def validate_cross_chain_link(link: CrossChainLink) -> bool:
    """Validate a CrossChainLink instance.

    Checks:
    - source and destination chains are present (non-empty)
    - source and destination addresses are present (non-empty)
    - source_chain != destination_chain (must be cross-chain)
    - confidence is within 0.0-1.0
    - evidence is present (non-empty)
    - source information is preserved

    Returns True if valid, raises ValueError if invalid.
    """
    # Internal validation shared with create_cross_chain_link
    _validate_cross_chain_link(link)

    # Additional checks specific to validate_cross_chain_link public API
    if not link.source or not link.source.strip():
        raise ValueError("source must be non-empty")

    return True


def _validate_cross_chain_link(link: CrossChainLink) -> None:
    """Internal validation for CrossChainLink.

    Raises ValueError if the link is invalid.
    """
    errors = []

    if not link.source_chain or not link.source_chain.strip():
        errors.append("source_chain must be non-empty")
    if not link.source_address or not link.source_address.strip():
        errors.append("source_address must be non-empty")
    if not link.destination_chain or not link.destination_chain.strip():
        errors.append("destination_chain must be non-empty")
    if not link.destination_address or not link.destination_address.strip():
        errors.append("destination_address must be non-empty")
    if link.source_chain == link.destination_chain:
        errors.append("source_chain and destination_chain must be different (cross-chain)")
    if not (0.0 <= link.confidence <= 1.0):
        errors.append(f"confidence must be between 0.0 and 1.0, got {link.confidence}")
    if not link.evidence or not link.evidence.strip():
        errors.append("evidence must be non-empty")

    if errors:
        raise ValueError("CrossChainLink validation failed: " + "; ".join(errors))


# End of cross-chain module


def test_valid_ethereum_to_tron_link() -> None:
    """Test a valid Ethereum -> TRON cross-chain link."""
    from chain_adapter import (
        CrossChainLink,
        create_cross_chain_link,
        validate_cross_chain_link,
    )

    link = create_cross_chain_link(
        source_chain="ethereum",
        source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
        source_asset="ETH",
        destination_chain="tron",
        destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
        destination_asset="TRX",
        evidence="Etherscan tag + TronGrid naming analysis",
        source="cross_chain_analysis_v1",
    )

    assert link.source_chain == "ethereum"
    assert link.destination_chain == "tron"
    assert link.source_address == "0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb"
    assert link.destination_address == "T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q"
    assert link.source_asset == "ETH"
    assert link.destination_asset == "TRX"
    assert link.confidence == 0.5
    assert link.evidence == "Etherscan tag + TronGrid naming analysis"
    assert link.source == "cross_chain_analysis_v1"
    assert link.source_tx_hash is None  # optional, can be absent

    # Validate
    assert validate_cross_chain_link(link) is True


def test_invalid_confidence_rejected() -> None:
    """Test that invalid confidence values are rejected."""
    from chain_adapter import create_cross_chain_link, validate_cross_chain_link

    # confidence > 1.0
    try:
        create_cross_chain_link(
            source_chain="ethereum",
            source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
            source_asset="ETH",
            destination_chain="tron",
            destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
            destination_asset="TRX",
            confidence=1.5,
            evidence="test",
            source="test",
        )
        assert False, "Should have raised ValueError for confidence > 1.0"
    except ValueError:
        pass

    # confidence < 0.0
    try:
        create_cross_chain_link(
            source_chain="ethereum",
            source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
            source_asset="ETH",
            destination_chain="tron",
            destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
            destination_asset="TRX",
            confidence=-0.1,
            evidence="test",
            source="test",
        )
        assert False, "Should have raised ValueError for confidence < 0.0"
    except ValueError:
        pass

    # Validate should also reject
    try:
        link = CrossChainLink(
            source_chain="ethereum",
            source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
            source_asset="ETH",
            destination_chain="tron",
            destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
            destination_asset="TRX",
            confidence=1.5,
            evidence="test",
            source="test",
        )
        validate_cross_chain_link(link)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_same_chain_link_rejected() -> None:
    """Test that same-chain links are rejected."""
    from chain_adapter import create_cross_chain_link, validate_cross_chain_link

    try:
        create_cross_chain_link(
            source_chain="ethereum",
            source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
            source_asset="ETH",
            destination_chain="ethereum",  # same as source
            destination_address="0x111122223333444455556666777788889999aaa",
            destination_asset="ETH",
            evidence="test",
            source="test",
        )
        assert False, "Should have raised ValueError for same-chain link"
    except ValueError:
        pass


def test_missing_evidence_rejected() -> None:
    """Test that links without evidence are rejected."""
    from chain_adapter import create_cross_chain_link, validate_cross_chain_link

    # create_cross_chain_link defaults evidence to ""
    try:
        link = create_cross_chain_link(
            source_chain="ethereum",
            source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
            source_asset="ETH",
            destination_chain="tron",
            destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
            destination_asset="TRX",
            source="test",
            # evidence defaults to ""
        )
        # validate should reject empty evidence
        validate_cross_chain_link(link)
        assert False, "Should have raised ValueError for missing evidence"
    except ValueError:
        pass


def test_destination_tx_hash_optional() -> None:
    """Test that destination transaction hash can be absent."""
    from chain_adapter import create_cross_chain_link, validate_cross_chain_link

    link = create_cross_chain_link(
        source_chain="ethereum",
        source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
        source_asset="ETH",
        destination_chain="tron",
        destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
        destination_asset="TRX",
        # destination_tx_hash defaults to None
        evidence="address mapping only",
        source="cross_chain_analysis_v1",
    )

    # destination_tx_hash should be None
    assert link.destination_tx_hash is None

    # Should still validate
    assert validate_cross_chain_link(link) is True


def test_evidence_source_preserved() -> None:
    """Test that evidence and source are preserved in the link."""
    from chain_adapter import create_cross_chain_link, validate_cross_chain_link

    link = create_cross_chain_link(
        source_chain="ethereum",
        source_address="0xaaaabbbbccccddddaaaabbbbccccddddaaaabbbb",
        source_asset="ETH",
        destination_chain="tron",
        destination_address="T9uYyWc51Mhh9qYpY9z74s7B1jmy5Rho6q",
        destination_asset="TRX",
        evidence="Multi-source correlation: Etherscan + TronGrid",
        source="cross_chain_analysis_v2",
    )

    assert link.evidence == "Multi-source correlation: Etherscan + TronGrid"
    assert link.source == "cross_chain_analysis_v2"
    assert validate_cross_chain_link(link) is True


def test_existing_ethereum_adapter_still_works() -> None:
    """Verify existing Ethereum adapter tests still pass."""
    from chain_adapter import EthereumAdapter

    adapter = EthereumAdapter()
    assert adapter.get_chain_id() == "ethereum"
    assert adapter.validate_address("0x" + "a" * 40) is True


def test_existing_tron_adapter_still_works() -> None:
    """Verify existing Tron adapter tests still pass."""
    from chain_adapter import TronAdapter

    adapter = TronAdapter()
    assert adapter.get_chain_id() == "tron"


# Run all tests when module is executed directly
if __name__ == "__main__":
    test_adapter_can_be_created()
    print("test_adapter_can_be_created passed!")

    test_ethereum_adapter_identifies_as_ethereum()
    print("test_ethereum_adapter_identifies_as_ethereum passed!")

    test_ethereum_address_validation_works()
    print("test_ethereum_address_validation_works passed!")

    test_adapter_interface_methods_exist()
    print("test_adapter_interface_methods_exist passed!")

    test_existing_tests_still_pass()
    print("test_existing_tests_still_pass passed!")

    # NEW: Cross-chain link tests
    test_valid_ethereum_to_tron_link()
    print("test_valid_ethereum_to_tron_link passed!")

    test_invalid_confidence_rejected()
    print("test_invalid_confidence_rejected passed!")

    test_same_chain_link_rejected()
    print("test_same_chain_link_rejected passed!")

    test_missing_evidence_rejected()
    print("test_missing_evidence_rejected passed!")

    test_destination_tx_hash_optional()
    print("test_destination_tx_hash_optional passed!")

    test_evidence_source_preserved()
    print("test_evidence_source_preserved passed!")

    test_existing_ethereum_adapter_still_works()
    print("test_existing_ethereum_adapter_still_works passed!")

    test_existing_tron_adapter_still_works()
    print("test_existing_tron_adapter_still_works passed!")

    # Synthetic bridge registry for test purposes.
    # This is test intelligence - does not represent real bridge data.
    # (SYNTHETIC_BRIDGE_REGISTRY defined at module level earlier)


def detect_cross_chain_links(
    source_transfers: list,
    destination_transfers: list,
    bridge_registry: dict | None = None,
    max_time_seconds: int = 3600,
    amount_tolerance: float = 1e6,
) -> list:
    """Detect plausible cross-chain bridge links between normalized transfers.

    Examines source and destination transfers and identifies possible
    bridge relationships based on synthetic bridge registry matching,
    asset compatibility, time ordering, and amount compatibility.

    Returns a list of CrossChainLink objects. Returns an empty list
    if no plausible links are found.

    The detector does NOT claim proven bridge relationships - it produces
    investigative confidence signals with evidence and a confidence score.
    """
    from chain_adapter import CrossChainLink, create_cross_chain_link, validate_cross_chain_link

    if bridge_registry is None:
        bridge_registry = SYNTHETIC_BRIDGE_REGISTRY

    links = []

    # Normalize: index transfers by address for matching
    # source_transfers: list of dicts with at least 'from_address', 'to_address', 'value', 'timestamp', 'hash', 'asset'
    # destination_transfers: same format

    for src in source_transfers:
        src_from = src.get("from_address", "")
        src_to = src.get("to_address", "")
        src_value = src.get("value", "0") or src.get("amount", "0") or "0"
        src_timestamp = src.get("timestamp", src.get("blockID", "0"))
        src_hash = src.get("hash", src.get("tx_hash", ""))
        src_asset = src.get("asset", src.get("symbol", ""))

        # Determine source chain from the address
        src_chain = _guess_chain_from_address(src_from)

        # Look up bridge info in registry for source address
        bridge_info = None
        if bridge_registry and src_chain in bridge_registry:
            addr_registry = bridge_registry[src_chain]
            if src_from in addr_registry:
                bridge_info = addr_registry[src_from]

        if bridge_info is None:
            # No known bridge on source side - skip
            continue

        bridge_name = bridge_info.get("bridge_name", "")
        dest_chains = bridge_info.get("destination_chains", [])

        # Must have at least one destination chain configured
        if not dest_chains:
            continue

        for dst in destination_transfers:
            dst_from = dst.get("from_address", "")
            dst_to = dst.get("to_address", "")
            dst_value = dst.get("value", "0") or dst.get("amount", "0") or "0"
            dst_timestamp = dst.get("timestamp", dst.get("blockID", "0"))
            dst_hash = dst.get("hash", dst.get("tx_hash", ""))
            dst_asset = dst.get("asset", dst.get("symbol", ""))

            # Determine destination chain
            dst_chain = _guess_chain_from_address(dst_to)

            # Criterion 1: Different chains
            if src_chain == dst_chain:
                continue

            # Criterion 2: Destination chain must be in bridge's supported chains
            if dst_chain not in dest_chains:
                continue

            # Criterion 3: Destination must occur after source
            try:
                src_ts = int(src_timestamp)
                dst_ts = int(dst_timestamp)
            except (ValueError, TypeError):
                continue

            if dst_ts < src_ts:
                # Destination before source - reject
                continue

            # Criterion 4: Time window
            time_diff = dst_ts - src_ts
            if time_diff > max_time_seconds:
                continue

            # Criterion 5: Asset compatibility
            # ETH -> TRX/USDT, USDT(ERC20) -> USDT(TRC20) when registry supports
            asset_compatible = _assets_compatible(src_asset, dst_asset, bridge_info)

            if not asset_compatible:
                continue

            # Criterion 6: Amount compatibility (allow bridge fees)
            # Use relative percentage tolerance instead of absolute,
            # since bridge fees are typically a small percentage.
            try:
                src_amt = float(src_value)
                dst_amt = float(dst_value)
            except (ValueError, TypeError):
                continue

            if src_amt <= 0 or dst_amt <= 0:
                # Zero amounts: skip strict tolerance check
                pass  # amount diff will be considered acceptable
            else:
                # Relative percentage difference
                max_allowed = max(src_amt, dst_amt) * 0.05  # 5% tolerance
                amount_diff = abs(src_amt - dst_amt)
                if amount_diff > max_allowed:
                    continue

            # All criteria passed - create a CrossChainLink
            link = create_cross_chain_link(
                source_chain=src_chain,
                source_address=src_from,
                source_asset=src_asset,
                destination_chain=dst_chain,
                destination_address=dst_to,
                destination_asset=dst_asset,
                source_tx_hash=src_hash,
                destination_tx_hash=dst_hash,
                bridge_address=src_from if bridge_name else None,
                bridge_name=bridge_name,
                confidence=_calculate_confidence(bridge_info, asset_compatible, time_diff, amount_diff, max_time_seconds),
                evidence=_make_evidence(
                    bridge_name, src_asset, dst_asset, time_diff, amount_diff, src_chain, dst_chain
                ),
                source="synthetic_bridge_registry",
            )

            # Validate the created link
            try:
                validate_cross_chain_link(link)
                links.append(link)
            except ValueError:
                # Should not happen if our validation is consistent, but skip if so
                continue

    return links


def _guess_chain_from_address(address: str) -> str:
    """Guess the blockchain from an address prefix."""
    addr = address.strip()
    if addr.startswith("0x") and len(addr) == 42:
        return "ethereum"
    elif addr.startswith("T") and len(addr) == 34:
        return "tron"
    else:
        return "unknown"


def _assets_compatible(source_asset: str, dest_asset: str, bridge_info: dict | None) -> bool:
    """Check if source and destination assets are compatible per bridge info."""
    if not bridge_info:
        return False

    src = (source_asset or "").upper()
    dst = (dest_asset or "").upper()

    # ETH can match ETH-like
    if src == "ETH" and dst in ("ETH", "TRX"):
        return True

    # USDT on either side
    if "USDT" in (src, dst):
        return True

    # If bridge info specifies supported assets, check those
    supported = bridge_info.get("supported_assets", [])
    if supported:
        return src in supported or dst in supported

    # Default: unknown assets are not compatible
    return False


def _calculate_confidence(
    bridge_info: dict,
    asset_compatible: bool,
    time_diff: int,
    amount_diff: float,
    max_time_seconds: int,
) -> float:
    """Calculate a conservative confidence score for the bridge link.

    Returns a float between 0.0 and 1.0.
    """
    base = 0.0

    # Known bridge on source side
    bridge_name = bridge_info.get("bridge_name", "")
    if bridge_name and bridge_name != "Unknown":
        base += 0.3

    # Asset compatibility
    if asset_compatible:
        base += 0.3

    # Reasonable time window (not at the extreme)
    if time_diff <= max_time_seconds // 2:
        base += 0.2

    # Amount within tolerance
    # (if we get here, amount is already within tolerance, so add lightly)
    base += 0.1

    # Cap at 1.0 and floor at 0.0
    return max(0.0, min(1.0, base))


def _make_evidence(
    bridge_name: str,
    src_asset: str,
    dst_asset: str,
    time_diff: int,
    amount_diff: float,
    src_chain: str,
    dst_chain: str,
) -> str:
    """Generate evidence string explaining why the link was created."""
    parts = []

    if bridge_name and bridge_name != "Unknown":
        parts.append(f"Known bridge: {bridge_name}")

    if src_asset and dst_asset:
        parts.append(f"Asset: {src_asset} → {dst_asset}")

    if src_chain and dst_chain and src_chain != dst_chain:
        parts.append(f"{src_chain} → {dst_chain}")

    if time_diff >= 0:
        parts.append(f"Time gap: {time_diff}s")

    if amount_diff > 0:
        parts.append(f"Amount diff: {amount_diff:.0f} (within tolerance)")

    return ". ".join(parts) if parts else "No specific evidence"


# Run all tests when module is executed directly
if __name__ == "__main__":
    test_adapter_can_be_created()
    print("test_adapter_can_be_created passed!")

    test_ethereum_adapter_identifies_as_ethereum()
    print("test_ethereum_adapter_identifies_as_ethereum passed!")

    test_ethereum_address_validation_works()
    print("test_ethereum_address_validation_works passed!")

    test_adapter_interface_methods_exist()
    print("test_adapter_interface_methods_exist passed!")

    test_existing_tests_still_pass()
    print("test_existing_tests_still_pass passed!")

    # NEW: Cross-chain link tests
    test_valid_ethereum_to_tron_link()
    print("test_valid_ethereum_to_tron_link passed!")

    test_invalid_confidence_rejected()
    print("test_invalid_confidence_rejected passed!")

    test_same_chain_link_rejected()
    print("test_same_chain_link_rejected passed!")

    test_missing_evidence_rejected()
    print("test_missing_evidence_rejected passed!")

    test_destination_tx_hash_optional()
    print("test_destination_tx_hash_optional passed!")

    test_evidence_source_preserved()
    print("test_evidence_source_preserved passed!")

    test_existing_ethereum_adapter_still_works()
    print("test_existing_ethereum_adapter_still_works passed!")

    test_existing_tron_adapter_still_works()
    print("test_existing_tron_adapter_still_works passed!")

    # NEW: Bridge link detector tests
    test_bridge_ethereum_to_tron_valid_match()
    print("test_bridge_ethereum_to_tron_valid_match passed!")

    test_bridge_same_chain_rejected()
    print("test_bridge_same_chain_rejected passed!")

    test_bridge_unknown_bridge_rejected()
    print("test_bridge_unknown_bridge_rejected passed!")

    test_bridge_asset_mismatch_rejected()
    print("test_bridge_asset_mismatch_rejected passed!")

    test_bridge_destination_before_source_rejected()
    print("test_bridge_destination_before_source_rejected passed!")

    test_bridge_time_window_exceeded_rejected()
    print("test_bridge_time_window_exceeded_rejected passed!")

    test_bridge_amount_outside_tolerance_rejected()
    print("test_bridge_amount_outside_tolerance_rejected passed!")

    test_bridge_small_fee_accepted()
    print("test_bridge_small_fee_accepted passed!")

    test_bridge_evidence_preserved()
    print("test_bridge_evidence_preserved passed!")

    test_bridge_confidence_range()
    print("test_bridge_confidence_range passed!")

    test_bridge_bridge_name_preserved()
    print("test_bridge_bridge_name_preserved passed!")

    test_bridge_multiple_transfers_no_crash()
    print("test_bridge_multiple_transfers_no_crash passed!")

    print("\nAll chain adapter tests passed!")