"""Chain adapter abstraction for multi-blockchain support.

Each blockchain must implement a ChainAdapter that converts its raw blockchain
data into the project's unified transfer representation.
"""
import abc
from eth_txs import is_valid_eth_address


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

    print("\nAll chain adapter tests passed!")