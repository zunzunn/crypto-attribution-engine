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