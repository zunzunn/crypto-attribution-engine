"""API tests for POST /api/v1/attribution/investigate.

Async tests run on the same event loop as the seeding calls (single SQLite
in-memory engine per test), and use no live chain APIs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.engine import build_session_factory
from app.main import create_app
from app.models import TokenTransferRecord
from app.repositories.transaction_repo import TransactionRepository
from app.schemas import EntityType
from app.services.attribution.registry import DatabaseAddressRegistry
from app.utils.time import as_naive_utc
from tests.factories import eth_addr, make_tx, tx_hash

SEED = eth_addr(1)
INTER = eth_addr(4)
VASP_A = eth_addr(100)
VASP_B = eth_addr(101)
BASE = datetime(2026, 5, 1, tzinfo=timezone.utc)

REPO = TransactionRepository()
REGISTRY = DatabaseAddressRegistry()

INVESTIGATE_URL = "/api/v1/attribution/investigate"


def _make_deployment():
    factory = build_session_factory("sqlite+aiosqlite:///:memory:")
    settings = Settings(db_auto_create=False)
    app = create_app(settings=settings, session_factory=factory)
    return app, factory


async def _create_schema(factory) -> None:
    from app.db.base import Base

    async with factory.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _seed(session, txs, *, vasp_addresses=(), mixer_addresses=()) -> None:
    await REPO.upsert_many(session, txs)
    for addr in vasp_addresses:
        await REGISTRY.register(
            session, chain_id="ethereum", network="mainnet", address=addr,
            category=EntityType.VASP, tag_source="fixture_list_v1", tag_version="v1",
        )
    for addr in mixer_addresses:
        await REGISTRY.register(
            session, chain_id="ethereum", network="mainnet", address=addr,
            category=EntityType.MIXER, tag_source="fixture_list_v1", tag_version="v1",
        )


@pytest.fixture
async def ctx():
    app, factory = _make_deployment()
    await _create_schema(factory)
    async with factory() as session:
        await _seed(
            session,
            [
                make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                        from_address=SEED, to_address=VASP_A),
                make_tx(tx_hash=tx_hash(2), block_number=11, block_timestamp=BASE,
                        from_address=SEED, to_address=INTER),
                make_tx(tx_hash=tx_hash(3), block_number=20,
                        block_timestamp=BASE + timedelta(days=1),
                        from_address=INTER, to_address=VASP_B),
            ],
            vasp_addresses=(VASP_A, VASP_B),
        )
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, factory
    await factory.dispose()


class TestInvestigate:
    async def test_returns_ranked_candidates(self, ctx) -> None:
        client, _ = ctx
        response = await client.post(
            INVESTIGATE_URL, json={"chain_id": "ethereum", "network": "mainnet",
                                   "seed_address": SEED, "max_hops": 3}
        )
        assert response.status_code == 200
        body = response.json()
        candidates = body["candidates"]
        assert len(candidates) == 2
        assert [c["matched_address"] for c in candidates] == [VASP_A, VASP_B]
        assert candidates[0]["hop_count"] == 1
        assert candidates[0]["path"]["hops"][0]["edge"]["tx_hash"] == tx_hash(1)
        assert candidates[0]["confidence"]["scoring_model_version"] == "scoring_model_v0"
        assert {"score", "tier", "base_score", "factors"} <= set(candidates[0]["confidence"])
        assert body["traversal"]["discovered_addresses"]
        assert body["request"]["seed_address"] == SEED

    async def test_no_matches_zero_hop(self, ctx) -> None:
        client, _ = ctx
        response = await client.post(
            INVESTIGATE_URL, json={"chain_id": "ethereum", "network": "mainnet",
                                   "seed_address": eth_addr(999), "max_hops": 2}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["candidates"] == []
        assert body["message"] is not None
        assert body["traversal"]["discovered_addresses"] == []

    async def test_unknown_chain_returns_404(self, ctx) -> None:
        client, _ = ctx
        response = await client.post(
            INVESTIGATE_URL, json={"chain_id": "bitcoin", "seed_address": SEED}
        )
        assert response.status_code == 404

    async def test_invalid_address_returns_422(self, ctx) -> None:
        client, _ = ctx
        response = await client.post(
            INVESTIGATE_URL, json={"chain_id": "ethereum", "seed_address": "not-an-address"}
        )
        assert response.status_code == 422

    async def test_bad_params_returns_422(self, ctx) -> None:
        client, _ = ctx
        for body in (
            {"chain_id": "ethereum", "seed_address": SEED, "max_hops": 0},
            {"chain_id": "ethereum", "seed_address": SEED, "max_hops": 21},
            {"chain_id": "ethereum", "seed_address": SEED,
             "time_from": (BASE + timedelta(days=2)).isoformat(),
             "time_to": BASE.isoformat()},
        ):
            response = await client.post(INVESTIGATE_URL, json=body)
            assert response.status_code == 422

    async def test_min_value_and_token_evidence_end_to_end(self, ctx) -> None:
        client, factory = ctx
        async with factory() as session:
            await REPO.upsert_many(
                session,
                [
                    make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                            from_address=SEED, to_address=VASP_A, value="5000000000000000000"),
                ],
            )
            session.add(
                TokenTransferRecord(
                    chain_id="ethereum", network="mainnet", tx_hash=tx_hash(1), transfer_index=0,
                    token_address=eth_addr(900), token_symbol="USDT", token_decimals=6,
                    from_address=SEED, to_address=VASP_A, value_raw="1000000",
                    source="test", fetched_at=as_naive_utc(BASE),
                )
            )
            await session.commit()

        response = await client.post(
            INVESTIGATE_URL, json={"chain_id": "ethereum", "network": "mainnet",
                                   "seed_address": SEED, "max_hops": 2, "min_value": "1000000"}
        )
        assert response.status_code == 200
        body = response.json()
        vasp = next(c for c in body["candidates"] if c["matched_address"] == VASP_A)
        assert vasp["path"]["hops"][0]["edge"]["token_transfers"][0]["token_symbol"] == "USDT"