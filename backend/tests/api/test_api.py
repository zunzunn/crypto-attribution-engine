"""API tests using an in-memory SQLite session factory and a stub adapter."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.errors import ChainNotSupportedError
from app.db.engine import build_session_factory
from app.main import create_app
from app.schemas import Transaction
from tests.factories import DEFAULT_HASH, make_two

ADDRESS = "0x" + "aa" * 20
RECEIVING = "0x" + "bb" * 20


class StubAdapter:
    chain_id = "ethereum"
    default_network: str | None = "mainnet"

    def __init__(self, transactions: list[Transaction]) -> None:
        self._transactions = transactions

    async def get_normalized_transactions(self, address: str) -> list[Transaction]:
        return [tx.model_copy() for tx in self._transactions]


class StubRegistry:
    def __init__(self, adapter: StubAdapter) -> None:
        self._adapter = adapter

    def get(self, chain_id: str):
        if chain_id != "ethereum":
            raise ChainNotSupportedError(chain_id)
        return self._adapter

    @property
    def supported_chains(self) -> list[str]:
        return ["ethereum"]


def _make_client() -> tuple[TestClient, StubRegistry]:
    factory = build_session_factory("sqlite+aiosqlite:///:memory:")
    stub = StubAdapter(make_two())
    app = create_app(session_factory=factory, registry=StubRegistry(stub))
    return TestClient(app), stub


class TestHealth:
    def test_health_ok(self) -> None:
        client, _ = _make_client()
        with client:
            response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"
        assert body["service"] == "crypto-attribution-engine"

    def test_health_degraded_when_db_unreachable(self) -> None:
        factory = build_session_factory(
            "postgresql+asyncpg://u:p@127.0.0.1:59999/does_not_exist"
        )
        app = create_app(session_factory=factory)
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["database"].startswith("unavailable")


class TestIngest:
    def test_ingest_then_idempotent_reingest(self) -> None:
        client, _ = _make_client()
        with client:
            first = client.post(f"/api/v1/ingest/ethereum/{ADDRESS}")
            assert first.status_code == 200
            body = first.json()
            assert body["status"] == "success"
            assert body["chain_id"] == "ethereum"
            assert body["address"] == ADDRESS
            assert body["inserted"] == 2
            assert body["skipped_existing"] == 0
            run_id = body["ingestion_run_id"]

            second = client.post(f"/api/v1/ingest/ethereum/{ADDRESS}")
            assert second.status_code == 200
            assert second.json()["inserted"] == 0
            assert second.json()["skipped_existing"] == 2

            run = client.get(f"/api/v1/ingestion-runs/{run_id}")
            assert run.status_code == 200
            assert run.json()["ingestion_run_id"] == run_id

            listed = client.get(f"/api/v1/ingest/ethereum/{ADDRESS}")
            assert listed.status_code == 200
            assert len(listed.json()) == 2

            by_hash = client.get(f"/api/v1/transactions/{DEFAULT_HASH}")
            assert by_hash.status_code == 200
            assert by_hash.json()["tx_hash"] == DEFAULT_HASH

    def test_unknown_chain_returns_404(self) -> None:
        client, _ = _make_client()
        with client:
            response = client.post("/api/v1/ingest/bitcoin/bc1qqqqqqqqqqqqqqqqqqqqqqqqqq")
        assert response.status_code == 404

    def test_invalid_address_returns_422(self) -> None:
        client, _ = _make_client()
        with client:
            response = client.post("/api/v1/ingest/ethereum/not-an-address")
        assert response.status_code == 422

    def test_unknown_transaction_returns_404(self) -> None:
        client, _ = _make_client()
        with client:
            response = client.get("/api/v1/transactions/" + "0x" + "ff" * 32)
        assert response.status_code == 404


class TestRoot:
    def test_root_info(self) -> None:
        client, _ = _make_client()
        with client:
            response = client.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "crypto-attribution-engine"