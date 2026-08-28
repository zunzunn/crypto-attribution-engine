"""ORM model for normalized transactions (canonical schema, chain-agnostic).

The unique constraint (chain_id, network, tx_hash) is the idempotency key:
re-ingesting the same transaction never creates a second row.
``senders``/``recipients``/``raw`` are stored as JSON so UTXO chains can hold
multiple inputs/outputs without schema changes. ``from_address``/``to_address``
are denormalized for indexed address lookups (account-based chains).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TransactionRecord(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "chain_id", "network", "tx_hash",
            name="uq_transactions_chain_id_network_tx_hash",
        ),
        Index("ix_transactions_tx_hash", "chain_id", "network", "tx_hash"),
        Index("ix_transactions_from_address", "chain_id", "from_address"),
        Index("ix_transactions_to_address", "chain_id", "to_address"),
        Index("ix_transactions_block_time", "chain_id", "block_timestamp"),
    )

    json_type = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tx_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    block_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="confirmed")
    transaction_type: Mapped[str] = mapped_column(String(24), nullable=False, default="native")

    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    value: Mapped[str] = mapped_column(String(128), nullable=False, default="0")
    value_decimals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fee: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    senders: Mapped[list | None] = mapped_column(json_type, nullable=True)
    recipients: Mapped[list | None] = mapped_column(json_type, nullable=True)

    source: Mapped[str] = mapped_column(String(255), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    raw: Mapped[dict | None] = mapped_column(json_type, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TransactionRecord chain={self.chain_id} tx={self.tx_hash[:12]}...>"