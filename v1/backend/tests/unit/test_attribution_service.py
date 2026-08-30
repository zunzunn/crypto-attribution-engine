"""Attribution service tests: traversal + registry + scoring end-to-end.

DB-backed (uses the shared session fixture), deterministic fixtures only - no
live chain APIs. Covers direct VASP attribution, multi-hop, multiple ranked
candidates, max-hop enforcement, time-window filtering, cycle handling,
duplicate transactions, min-value filtering, no-attribution, token evidence,
and confidence behavior.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import TokenTransferRecord
from app.repositories.transaction_repo import TransactionRepository
from app.schemas import EntityType, TraversalRequest
from app.services.attribution.registry import DatabaseAddressRegistry
from app.services.attribution.scoring import ConfidenceScorer
from app.services.attribution.service import AttributionService
from app.services.graph.repository import DatabaseGraphExpander
from app.services.traversal.engine import TraversalEngine
from app.utils.time import as_naive_utc, utc_now
from tests.factories import eth_addr, make_tx, tx_hash

SEED = eth_addr(1)
A = eth_addr(2)
B = eth_addr(3)
INTER = eth_addr(4)
EXTRA = eth_addr(5)
VASP_A = eth_addr(100)
VASP_B = eth_addr(101)

BASE = datetime(2026, 5, 1, tzinfo=timezone.utc)
FRESH = utc_now() - timedelta(days=5)

REPO = TransactionRepository()
REGISTRY = DatabaseAddressRegistry()


def make_service() -> AttributionService:
    return AttributionService(
        engine=TraversalEngine(),
        expander=DatabaseGraphExpander(),
        registry=REGISTRY,
        scorer=ConfidenceScorer(),
    )


def request(seed=SEED, **kwargs) -> TraversalRequest:
    return TraversalRequest(chain_id="ethereum", network="mainnet", seed_address=seed, **kwargs)


async def investigate(session, **kwargs):
    service = make_service()
    return await service.investigate(session, request(**kwargs))


async def seed_txs(session, txs) -> None:
    await REPO.upsert_many(session, txs)


async def register_vasp(session, address, *, category=EntityType.VASP, name=None) -> None:
    await REGISTRY.register(
        session,
        chain_id="ethereum",
        network="mainnet",
        address=address,
        category=category,
        name=name,
        tag_source="fixture_list_v1",
        tag_version="v1",
        imported_at=FRESH,
    )


class TestDirectVasp:
    async def test_direct_known_address_match(self, session) -> None:
        tx = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A,
        )
        await seed_txs(session, [tx])
        await register_vasp(session, VASP_A, name="Candidate VASP alpha")

        response = await investigate(session)
        assert len(response.candidates) == 1
        candidate = response.candidates[0]
        assert candidate.entity.category == EntityType.VASP
        assert candidate.entity.name == "Candidate VASP alpha"
        assert candidate.matched_address == VASP_A
        assert candidate.hop_count == 1
        assert candidate.evidence_tx_hashes == [tx_hash(1)]
        assert candidate.path.hop_count == 1
        assert candidate.path.hops[0].edge.tx_hash == tx_hash(1)
        assert candidate.path.hops[0].edge.from_address == SEED
        assert response.message is None


class TestMultiHop:
    async def test_multi_hop_candidate_keeps_full_path(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=INTER),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=INTER, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)

        response = await investigate(session, max_hops=3)
        assert len(response.candidates) == 1
        candidate = response.candidates[0]
        assert candidate.hop_count == 2
        hops = candidate.path.hops
        assert [h.edge.from_address for h in hops] == [SEED, INTER]
        assert [h.edge.to_address for h in hops] == [INTER, VASP_A]
        assert [h.edge.tx_hash for h in hops] == [tx_hash(1), tx_hash(2)]
        # hop distance lowers confidence below the direct case
        assert round(candidate.confidence.score, 4) == 0.82


class TestRanking:
    async def test_multiple_candidates_ranked_deterministically(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=VASP_A),
            make_tx(tx_hash=tx_hash(2), block_number=11, block_timestamp=BASE,
                    from_address=SEED, to_address=INTER),
            make_tx(tx_hash=tx_hash(3), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=INTER, to_address=VASP_B),
            # Corroborating inbound tx to VASP_A (via a second intermediate).
            make_tx(tx_hash=tx_hash(4), block_number=12, block_timestamp=BASE,
                    from_address=SEED, to_address=EXTRA),
            make_tx(tx_hash=tx_hash(5), block_number=21, block_timestamp=BASE + timedelta(days=1),
                    from_address=EXTRA, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)
        await register_vasp(session, VASP_B)

        response = await investigate(session, max_hops=3)
        assert len(response.candidates) == 2
        first, second = response.candidates
        assert first.matched_address == VASP_A
        assert second.matched_address == VASP_B
        # VASP_A: hop 1 + 2 supporting txs -> 0.80 + fresh(0.05) + corroboration(0.05)
        assert round(first.confidence.score, 4) == 0.90
        # VASP_B: hop 2, single supporting tx -> 0.80 + fresh(0.05) - hop(0.03)
        assert round(second.confidence.score, 4) == 0.82
        assert first.confidence.score > second.confidence.score

    async def test_tie_breaks_by_hop_then_address(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=VASP_B),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE,
                    from_address=SEED, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)
        await register_vasp(session, VASP_B)

        response = await investigate(session)
        assert [c.matched_address for c in response.candidates] == [
            VASP_A, VASP_B,
        ]  # equal scores, ascending address


class TestConstraints:
    async def test_max_hops_blocks_deep_discovery(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=A),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=A, to_address=B),
            make_tx(tx_hash=tx_hash(3), block_number=30, block_timestamp=BASE + timedelta(days=2),
                    from_address=B, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)

        short = await investigate(session, max_hops=2)
        assert short.candidates == []
        assert short.message is not None

        full = await investigate(session, max_hops=3)
        assert len(full.candidates) == 1
        assert full.candidates[0].hop_count == 3
        assert round(full.candidates[0].confidence.score, 4) == 0.79

    async def test_time_window_filters_mid_path_edge(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=INTER),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE + timedelta(days=2),
                    from_address=INTER, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)

        response = await investigate(session, max_hops=2, time_to=BASE + timedelta(days=1))
        assert response.candidates == []
        assert response.traversal.pruned_by_reason.get("time_window") == 1

    async def test_min_value_filters_dust(self, session) -> None:
        tx = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A, value="100",
        )
        await seed_txs(session, [tx])
        await register_vasp(session, VASP_A)

        filtered = await investigate(session, min_value="1000")
        assert filtered.candidates == []
        assert filtered.traversal.pruned_by_reason.get("value_below_threshold") == 1

        kept = await investigate(session, min_value="50")
        assert len(kept.candidates) == 1


class TestCycles:
    async def test_cycle_terminates_and_still_attributes(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=A),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=A, to_address=B),
            make_tx(tx_hash=tx_hash(3), block_number=30, block_timestamp=BASE + timedelta(days=2),
                    from_address=B, to_address=A),  # cycle back to A
            make_tx(tx_hash=tx_hash(4), block_number=40, block_timestamp=BASE + timedelta(days=3),
                    from_address=B, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)

        response = await investigate(session, max_hops=4)
        assert response.traversal.cycles_encountered == 1
        assert response.traversal.pruned_by_reason.get("cycle") == 1
        assert len(response.candidates) == 1
        assert response.candidates[0].matched_address == VASP_A


class TestDuplicates:
    async def test_reingested_duplicate_produces_single_edge(self, session) -> None:
        tx = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A,
        )
        await seed_txs(session, [tx, tx])
        await register_vasp(session, VASP_A)

        response = await investigate(session)
        assert len(response.candidates) == 1
        assert response.candidates[0].evidence_tx_hashes == [tx_hash(1)]
        assert response.traversal.edges_examined == 1

    async def test_same_hash_other_chain_does_not_leak_in(self, session) -> None:
        ether_tx = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A,
        )
        tron_tx = make_tx(
            tx_hash=tx_hash(1), chain_id="tron", network="mainnet", block_number=5,
            block_timestamp=BASE, from_address=SEED, to_address=INTER,
        )
        await seed_txs(session, [ether_tx, tron_tx])
        await register_vasp(session, VASP_A)

        response = await investigate(session)
        assert len(response.candidates) == 1
        assert response.candidates[0].matched_address == VASP_A
        assert response.traversal.discovered_addresses == [VASP_A]


class TestNoAttribution:
    async def test_no_known_addresses_returns_message(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=A),
            make_tx(tx_hash=tx_hash(2), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=A, to_address=B),
        ]
        await seed_txs(session, txs)

        response = await investigate(session, max_hops=2)
        assert response.candidates == []
        assert response.message == "No known-address matches found within the explored graph."
        assert len(response.traversal.paths) == 2


class TestEvidence:
    async def test_token_transfers_attach_to_edge_evidence(self, session) -> None:
        tx = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A,
        )
        await seed_txs(session, [tx])
        await register_vasp(session, VASP_A)

        session.add(
            TokenTransferRecord(
                chain_id="ethereum", network="mainnet", tx_hash=tx_hash(1), transfer_index=0,
                token_address=eth_addr(900), token_symbol="USDT", token_name="Tether",
                token_decimals=6, from_address=SEED, to_address=VASP_A, value_raw="1000000",
                source="test", fetched_at=as_naive_utc(BASE),
            )
        )
        await session.flush()

        response = await investigate(session)
        assert len(response.candidates) == 1
        edge = response.candidates[0].path.hops[0].edge
        assert len(edge.token_transfers) == 1
        transfer = edge.token_transfers[0]
        assert transfer.token_symbol == "USDT"
        assert transfer.from_address == SEED
        assert transfer.to_address == VASP_A


class TestConfidenceBehavior:
    async def test_direct_hop_is_high_and_hop_penalty_absent(self, session) -> None:
        direct = make_tx(
            tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
            from_address=SEED, to_address=VASP_A,
        )
        await seed_txs(session, [direct])
        await register_vasp(session, VASP_A)
        candidate = (await investigate(session)).candidates[0]
        factor_names = {f.name for f in candidate.confidence.factors}
        assert "hop_distance" not in factor_names
        assert candidate.confidence.tier == "high"
        assert candidate.confidence.score >= 0.75

    async def test_correlated_supporting_txs_raise_confidence(self, session) -> None:
        txs = [
            make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                    from_address=SEED, to_address=INTER),
            make_tx(tx_hash=tx_hash(2), block_number=11, block_timestamp=BASE,
                    from_address=SEED, to_address=EXTRA),
            make_tx(tx_hash=tx_hash(3), block_number=20, block_timestamp=BASE + timedelta(days=1),
                    from_address=INTER, to_address=VASP_A),
            make_tx(tx_hash=tx_hash(4), block_number=21, block_timestamp=BASE + timedelta(days=1),
                    from_address=EXTRA, to_address=VASP_A),
        ]
        await seed_txs(session, txs)
        await register_vasp(session, VASP_A)

        response = await investigate(session, max_hops=2)
        candidate = response.candidates[0]
        factors = {f.name: f.delta for f in candidate.confidence.factors}
        assert factors.get("corroboration") == 0.05
        assert len(set(candidate.evidence_tx_hashes)) == 2