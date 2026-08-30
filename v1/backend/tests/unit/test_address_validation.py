"""Address validation tests."""

from __future__ import annotations

import pytest

from app.core.errors import ChainNotSupportedError, InvalidAddressError
from app.utils.addresses import validate_chain_address, validate_ethereum_address


class TestEthereumAddress:
    @pytest.mark.parametrize(
        "address",
        [
            "0x" + "a" * 40,
            "0x" + "A" * 40,
            "0x" + "Ab12cD34" * 5,
            "0x" + "ab" * 20,
        ],
    )
    def test_valid_addresses_normalize_to_lowercase(self, address: str) -> None:
        normalized = validate_ethereum_address(address)
        assert normalized == address.lower()

    @pytest.mark.parametrize(
        "address",
        [
            "",
            "   ",
            "abc",
            "0x1234",  # too short
            "1234" + "a" * 40,  # missing 0x
            "0x" + "g" * 40,  # non-hex
            "0x" + "a" * 39,  # off-by-one length
        ],
    )
    def test_invalid_addresses_raise(self, address: str) -> None:
        with pytest.raises(InvalidAddressError):
            validate_ethereum_address(address)


class TestChainDispatch:
    def test_unknown_chain_raises(self) -> None:
        with pytest.raises(ChainNotSupportedError):
            validate_chain_address("bitcoin", "bc1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
            # bitcoin not implemented yet (Phase 1-follow on)

    def test_valid_chain_delegates(self) -> None:
        assert validate_chain_address("ethereum", "0x" + "B" * 40) == "0x" + "b" * 40