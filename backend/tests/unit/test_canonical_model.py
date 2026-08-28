"""Unit tests for the canonical transaction schema."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas import Transaction
from tests.factories import DEFAULT_HASH, make_tx


class TestCanonicalTransaction:
    def test_valid_minimal_transaction(self) -> None:
        tx = make_tx()
        assert tx.chain_id == "ethereum"
        assert tx.tx_hash == DEFAULT_HASH
        assert tx.status == "confirmed"
        assert tx.senders == []
        assert tx.recipients == []
        assert tx.token_transfers == []

    def test_large_value_preserved_as_string(self) -> None:
        big = "1234567890123456789012345678901234567890"
        tx = make_tx(value=big)
        assert tx.value == big
        assert int(tx.value) == int(big)

    def test_value_must_not_be_float(self) -> None:
        # Pydantic's str field rejects floats, preserving base-unit precision.
        with pytest.raises(ValidationError):
            make_tx(value=1e18)  # type: ignore[arg-type]

    def test_value_must_not_be_int(self) -> None:
        with pytest.raises(ValidationError):
            make_tx(value=123)  # type: ignore[arg-type]

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(ValidationError):
            Transaction(chain_id="ethereum", tx_hash="")  # missing value/source/fetched_at
        with pytest.raises(ValidationError):
            Transaction(
                chain_id="ethereum",
                value="0",
                source="test",
                fetched_at=datetime.now(timezone.utc),
            )  # missing tx_hash

    def test_naive_timestamp_normalized_to_utc_aware(self) -> None:
        # Constructing a naive datetime is deliberate (verifying the coercion).
        naive = datetime(2024, 1, 2, 3, 4, 5)  # noqa: DTZ001
        tx = make_tx(block_timestamp=naive)
        assert tx.block_timestamp == naive.replace(tzinfo=timezone.utc)
        assert tx.block_timestamp.tzinfo is not None

    def test_chain_agnostic_lists(self) -> None:
        from app.schemas import AddressAmount

        tx = make_tx()
        tx.senders = [AddressAmount(address="0xaaa", value="1")]
        tx.recipients = [
            AddressAmount(address="0xbbb", value="2"),
            AddressAmount(address="0xccc", value="3"),
        ]
        assert [r.address for r in tx.recipients] == ["0xbbb", "0xccc"]