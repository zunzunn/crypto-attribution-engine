"""Normalization: raw Etherscan records -> canonical Transactions.

Pure functions with no I/O, which makes them trivially unit-testable. The
Etherscan V1/V2 ``txlist`` records carry the same fields (``timeStamp``,
``hash``, ``from``, ``to``, ``value``, ``gasUsed``, ``gasPrice``, ``isError``,
``input``, ...).
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import AddressAmount, Transaction
from app.utils.addresses import validate_ethereum_address


def _int_or_none(value: str | int | None) -> int | None:
    if value in (None, "", "0x0"):
        return None
    try:
        return int(value, 16) if isinstance(value, str) and value.startswith("0x") else int(value)
    except (TypeError, ValueError):
        return None


def _timestamp(item: dict) -> datetime | None:
    raw = item.get("timeStamp", item.get("timestamp"))
    ts = _int_or_none(raw)
    if ts is None or ts <= 0:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _status(item: dict) -> str:
    is_error = str(item.get("isError", "0")).lower()
    receipt_status = str(item.get("txreceipt_status", "1"))
    if is_error in ("1", "true") or receipt_status == "0":
        return "failed"
    return "confirmed"


def _fee(item: dict) -> str | None:
    gas_used = _int_or_none(item.get("gasUsed"))
    gas_price = _int_or_none(item.get("gasPrice"))
    if gas_used is None or gas_price is None:
        return None
    return str(gas_used * gas_price)


def normalize_etherscan_native(
    record: dict,
    *,
    chain_id: str,
    network: str | None,
    source: str,
    fetched_at: datetime,
    value_decimals: int = 18,
) -> Transaction:
    """Convert one Etherscan ``txlist`` record into a canonical Transaction.

    ``to`` may be empty for contract-creation transactions, in which case the
    recipient is omitted rather than mistagged.
    """
    tx_hash: str = str(record["hash"]).lower()
    from_addr = validate_ethereum_address(str(record["from"]))
    raw_to = str(record.get("to") or "").strip()
    to_addr = raw_to.lower() if raw_to.lower().startswith("0x") else None

    value_raw = str(record.get("value") or "0").strip()
    value = str(int(value_raw)) if value_raw.lstrip("-").isdigit() else "0"

    senders = [AddressAmount(address=from_addr, value=value)]
    recipients = [AddressAmount(address=to_addr, value=value)] if to_addr else []

    return Transaction(
        chain_id=chain_id,
        network=network,
        tx_hash=tx_hash,
        block_number=_int_or_none(record.get("blockNumber")),
        block_hash=record.get("blockHash") or None,
        block_timestamp=_timestamp(record),
        status=_status(record),
        transaction_type="native",
        from_address=from_addr,
        to_address=to_addr,
        value=value,
        value_decimals=value_decimals,
        fee=_fee(record),
        input_data=str(record.get("input") or "0x"),
        senders=senders,
        recipients=recipients,
        source=source,
        fetched_at=fetched_at,
    )


def normalize_etherscan_native_batch(
    records: list[dict],
    *,
    chain_id: str,
    network: str | None,
    source: str,
    fetched_at: datetime,
    value_decimals: int = 18,
) -> list[Transaction]:
    """Normalize a batch of Etherscan ``txlist`` records."""
    return [
        normalize_etherscan_native(
            record,
            chain_id=chain_id,
            network=network,
            source=source,
            fetched_at=fetched_at,
            value_decimals=value_decimals,
        )
        for record in records
    ]