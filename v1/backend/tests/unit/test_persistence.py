"""Persistence tests: idempotent upserts and canonical <-> ORM round trip."""

from __future__ import annotations

from sqlalchemy import select

from app.models import TransactionRecord
from app.repositories.transaction_repo import (
    TransactionRepository,
    canonical_to_orm,
    orm_to_canonical,
)
from tests.factories import DEFAULT_HASH, make_two, make_tx

repo = TransactionRepository()


class TestRoundTrip:
    async def test_canonical_to_orm_and_back(self, session) -> None:
        tx = make_two()[0]
        row = canonical_to_orm(tx)
        session.add(row)
        await session.flush()

        loaded = await session.get(TransactionRecord, row.id)
        assert loaded is not None
        assert loaded.tx_hash == tx.tx_hash
        assert loaded.chain_id == tx.chain_id
        assert loaded.from_address == tx.from_address

        back = orm_to_canonical(loaded)
        assert back.value == tx.value
        assert back.block_timestamp == tx.block_timestamp
        assert back.block_timestamp.tzinfo is not None
        assert back.value_decimals == 18

    async def test_naive_dt_stored_naive(self, session) -> None:
        tx = make_two()[0]
        row = canonical_to_orm(tx)
        assert row.block_timestamp.tzinfo is None
        assert row.fetched_at.tzinfo is None


class TestIdempotentUpsert:
    async def test_upsert_twice_is_noop_the_second_time(self, session) -> None:
        txs = make_two()
        inserted, skipped = await repo.upsert_many(session, txs)
        assert (inserted, skipped) == (2, 0)

        inserted_again, skipped_again = await repo.upsert_many(session, txs)
        assert (inserted_again, skipped_again) == (0, 2)

        count = len((await session.execute(select(TransactionRecord))).all())
        assert count == 2

    async def test_partial_overlap(self, session) -> None:
        first = make_two()
        await repo.upsert_many(session, first)

        fresh = make_tx(tx_hash="0x" + "55" * 32, value="777")
        inserted, skipped = await repo.upsert_many(session, [first[0], fresh])
        assert (inserted, skipped) == (1, 1)

        count = len((await session.execute(select(TransactionRecord))).all())
        assert count == 3

    async def test_same_hash_different_chain_coexists(self, session) -> None:
        # Same tx_hash on different chains is a different row (chain-aware key).
        a = make_two()[0]
        b = make_two()[0].model_copy(update={"chain_id": "tron", "network": "mainnet"})
        for txs in ([a], [b], [a], [b]):
            await repo.upsert_many(session, txs)

        count = len((await session.execute(select(TransactionRecord))).all())
        assert count == 2

    async def test_empty_batch(self, session) -> None:
        assert await repo.upsert_many(session, []) == (0, 0)


class TestQueries:
    async def test_list_by_address(self, session) -> None:
        txs = make_two()
        await repo.upsert_many(session, txs)

        found = await repo.list_by_address(
            session, address=txs[0].from_address, chain_id="ethereum"
        )
        assert len(found) == 2

        received = await repo.list_by_address(
            session, address=txs[0].to_address, chain_id="ethereum"
        )
        assert len(received) >= 1

    async def test_get_by_hash(self, session) -> None:
        await repo.upsert_many(session, [make_two()[0]])
        record = await repo.get_by_hash(
            session, chain_id="ethereum", network="mainnet", tx_hash=DEFAULT_HASH
        )
        assert record is not None
        assert record.tx_hash == DEFAULT_HASH

    async def test_get_by_hash_missing(self, session) -> None:
        assert (
            await repo.get_by_hash(
                session, chain_id="ethereum", network="mainnet", tx_hash="0x" + "ff" * 32
            )
            is None
        )

    async def test_count_by_address(self, session) -> None:
        await repo.upsert_many(session, make_two())
        count = await repo.count_by_address(
            session, address=make_two()[0].from_address, chain_id="ethereum"
        )
        assert count == 2