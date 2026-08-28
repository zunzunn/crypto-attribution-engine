"""ORM model for token transfers (e.g., ERC-20).

Defined now so the canonical schema and database are forward-compatible; the
Phase 1 Ethereum adapter ingests native (ETH) transfers only, token ingestion
is a Phase 1 / Phase 2 follow-on.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TokenTransferRecord(Base):
    __tablename__ = "token_transfers"
    __table_args__ = (
        UniqueConstraint(
            "chain_id", "network", "tx_hash", "transfer_index",
            name="uq_token_transfers_chain_network_tx_index",
        ),
    )

    json_type = JSON().with_variant(JSONB(), "postgresql")

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tx_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    transfer_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_address: Mapped[str] = mapped_column(String(255), nullable=False)
    token_symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    token_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_raw: Mapped[str] = mapped_column(String(128), nullable=False, default="0")
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    raw: Mapped[dict | None] = mapped_column(json_type, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TokenTransferRecord tx={self.tx_hash[:12]}... idx={self.transfer_index}>"