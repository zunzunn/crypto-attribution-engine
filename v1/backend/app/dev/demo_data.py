"""Deterministic, clearly-synthetic demo fixtures for manual end-to-end testing.

The addresses and hashes mirror the exact deterministic scheme used by the
test factories (``0x0000…0001``-style addresses, ``0x0000…01``-style hashes) so
a manually seeded development database looks identical to what the unit/API
tests exercise. Everything here is FAKE data: the addresses are dummy values,
never real exchange/VASP wallets, and the tag source marks the entity as a
development fixture.

See ``app/dev/seed_demo.py`` (and the ``make seed-demo`` / ``make reset-demo``
targets) for how this data is loaded into the development database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas import EntityType, Transaction

# --------------------------------------------------------------------------- #
# Chain / network scope
# --------------------------------------------------------------------------- #
DEMO_CHAIN = "ethereum"
DEMO_NETWORK = "mainnet"

# --------------------------------------------------------------------------- #
# Deterministic base clock for the demo snapshot
# --------------------------------------------------------------------------- #
DEMO_BASE = datetime(2026, 5, 1, tzinfo=timezone.utc)


def _eth_addr(n: int) -> str:
    """Deterministic pseudo-Ethereum address (same scheme as test factories)."""
    return f"0x{n:040x}"


def _tx_hash(n: int) -> str:
    """Deterministic pseudo-transaction hash (same scheme as test factories)."""
    return f"0x{n:064x}"


# --------------------------------------------------------------------------- #
# Demo graph: SEED -> INTER -> VASP_A  (all dummy addresses)
# --------------------------------------------------------------------------- #
SEED = _eth_addr(1)     # unhosted seed wallet under investigation
INTER = _eth_addr(4)    # intermediate hop (unregistered)
VASP_A = _eth_addr(100)  # synthetic known entity ("Candidate VASP alpha")

SEED_TO_INTER_TX = _tx_hash(1)
INTER_TO_VASP_TX = _tx_hash(2)
INTER_TO_VASP_BLOCK = 20
SEED_TO_INTER_BLOCK = 10

# 1 ETH in wei - matches the test factories' default value.
VALUE_WEI = "1000000000000000000"
VALUE_DECIMALS = 18

# --------------------------------------------------------------------------- #
# Synthetic entity metadata (clearly marked as a fixture, not a real VASP)
# --------------------------------------------------------------------------- #
VASP_A_NAME = "Candidate VASP alpha"
VASP_A_TAG_SOURCE = "demo_fixture_v1"
VASP_A_TAG_VERSION = "v1"
VASP_A_ENTITY_CATEGORY = EntityType.VASP

# --------------------------------------------------------------------------- #
# Transaction fixture builder
# --------------------------------------------------------------------------- #


def _transaction(
    *,
    tx_hash_value: str,
    block_number: int,
    block_timestamp: datetime,
    from_address: str,
    to_address: str,
) -> Transaction:
    """A single deterministic demo transaction (native ETH transfer)."""
    return Transaction(
        chain_id=DEMO_CHAIN,
        network=DEMO_NETWORK,
        tx_hash=tx_hash_value,
        block_number=block_number,
        block_timestamp=block_timestamp,
        from_address=from_address,
        to_address=to_address,
        value=VALUE_WEI,
        value_decimals=VALUE_DECIMALS,
        status="confirmed",
        transaction_type="native",
        input_data="0x",
        source="demo_fixture",
        fetched_at=DEMO_BASE,
    )


def build_transactions() -> list[Transaction]:
    """The demo chain SEED -> INTER -> VASP_A as canonical transactions."""
    return [
        _transaction(
            tx_hash_value=SEED_TO_INTER_TX,
            block_number=SEED_TO_INTER_BLOCK,
            block_timestamp=DEMO_BASE,
            from_address=SEED,
            to_address=INTER,
        ),
        _transaction(
            tx_hash_value=INTER_TO_VASP_TX,
            block_number=INTER_TO_VASP_BLOCK,
            block_timestamp=DEMO_BASE + timedelta(days=1),
            from_address=INTER,
            to_address=VASP_A,
        ),
    ]


def demo_tx_hashes() -> set[str]:
    """Transaction hashes owned by the demo dataset (used by reset)."""
    return {SEED_TO_INTER_TX, INTER_TO_VASP_TX}