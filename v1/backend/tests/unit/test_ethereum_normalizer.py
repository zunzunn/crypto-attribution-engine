"""Normalizer tests: raw Etherscan records -> canonical Transactions."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.ingestion.ethereum_normalizer import (
    normalize_etherscan_native,
    normalize_etherscan_native_batch,
)

FETCHED_AT = datetime(2026, 8, 28, 12, 0, 0, tzinfo=timezone.utc)
FROM = "0x" + "00" * 18 + "ab"  # mixed-case not needed; lowercase expected output
TO = "0x" + "11" * 19 + "cd"


def _record(**overrides) -> dict:
    base = {
        "blockNumber": "21000000",
        "timeStamp": "1710000000",
        "hash": "0xABCDEFabcdefabcdefabcdABCdefABCDEFabcdefabcdefabcdABCdefABCDEF",
        "from": "0x" + "aa" * 20,
        "to": "0x" + "bb" * 20,
        "value": "1500000000000000000",
        "gas": "21000",
        "gasUsed": "21000",
        "gasPrice": "20000000000",
        "input": "0x",
        "isError": "0",
        "txreceipt_status": "1",
        "confirmations": "345",
    }
    base.update(overrides)
    return base


class TestSingleNormalization:
    def test_basic_fields(self) -> None:
        tx = normalize_etherscan_native(
            _record(),
            chain_id="ethereum",
            network="mainnet",
            source="etherscan:mainnet",
            fetched_at=FETCHED_AT,
        )
        assert tx.chain_id == "ethereum"
        assert tx.network == "mainnet"
        assert tx.tx_hash.startswith("0x")
        assert tx.tx_hash == tx.tx_hash.lower()
        assert tx.block_number == 21000000
        assert tx.status == "confirmed"
        assert tx.transaction_type == "native"
        assert tx.value == "1500000000000000000"
        assert tx.value_decimals == 18
        assert tx.from_address == "0x" + "aa" * 20
        assert tx.to_address == "0x" + "bb" * 20

    def test_value_normalized_without_leading_zeros(self) -> None:
        tx = normalize_etherscan_native(
            _record(value="0001500000000000000000"),
            chain_id="ethereum", network="mainnet", source="s",
            fetched_at=FETCHED_AT,
        )
        assert tx.value == "1500000000000000000"

    def test_fee_is_gas_used_times_gas_price(self) -> None:
        tx = normalize_etherscan_native(
            _record(gasUsed="21000", gasPrice="20000000000"),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.fee == str(21000 * 20000000000)

    def test_failed_transaction_maps_to_failed(self) -> None:
        tx = normalize_etherscan_native(
            _record(isError="1"),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.status == "failed"

    def test_contract_creation_has_no_recipient(self) -> None:
        tx = normalize_etherscan_native(
            _record(to="", value="0"),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.to_address is None
        assert tx.recipients == []

    def test_balance_preserved_in_senders(self) -> None:
        tx = normalize_etherscan_native(
            _record(value="42"),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.senders[0].address == "0x" + "aa" * 20
        assert tx.senders[0].value == "42"

    def test_timestamp_parsed_as_utc(self) -> None:
        tx = normalize_etherscan_native(
            _record(timeStamp="1710000000"),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.block_timestamp is not None
        assert tx.block_timestamp == datetime.fromtimestamp(1710000000, tz=timezone.utc)

    def test_empty_input_becomes_0x(self) -> None:
        tx = normalize_etherscan_native(
            _record(input=""),
            chain_id="ethereum", network="mainnet", source="s", fetched_at=FETCHED_AT,
        )
        assert tx.input_data == "0x"


class TestBatchNormalization:
    def test_batch_returns_same_count(self) -> None:
        records = [_record(), _record(hash="0x" + "12" * 32), _record(hash="0x" + "34" * 32)]
        txs = normalize_etherscan_native_batch(
            records,
            chain_id="ethereum",
            network="mainnet",
            source="etherscan:mainnet",
            fetched_at=FETCHED_AT,
        )
        assert len(txs) == 3
        assert {tx.tx_hash for tx in txs} == {
            "0x" + "12" * 32,
            "0x" + "34" * 32,
            _record()["hash"].lower(),
        }