"""Chain adapter protocol shared by every future blockchain adapter.

A chain adapter is the ONLY component that knows about a specific chain's
data provider. Everything downstream (persistence, later traversal and
attribution) consumes canonical ``Transaction`` objects only.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import Transaction


class ChainAdapter(Protocol):
    chain_id: str
    default_network: str | None

    async def get_normalized_transactions(self, address: str) -> list[Transaction]:
        """Fetch, normalize, and return transactions touching ``address``."""
        ...