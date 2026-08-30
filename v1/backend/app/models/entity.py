"""ORM models for the local entity/address registry.

``entities`` is the catalog of known services/actors (each with a documented
``tag_source``/``tag_version``). ``entity_addresses`` maps one wallet address to
its primary entity for a given (chain, network) - the unique key
(chain_id, network, address) makes the mapping idempotent and deterministic.

This local registry is intentionally *not* comprehensive. It is the first,
database-backed implementation of the ``AddressRegistry`` abstraction so an
external intelligence source can be added later behind the same interface
without touching traversal or attribution logic.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EntityRecord(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(24), nullable=False)  # EntityType value
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tag_source: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    addresses: Mapped[list[EntityAddressRecord]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<EntityRecord id={self.id} category={self.category}>"


class EntityAddressRecord(Base):
    __tablename__ = "entity_addresses"
    __table_args__ = (
        UniqueConstraint(
            "chain_id", "network", "address",
            name="uq_entity_addresses_chain_network_address",
        ),
        Index("ix_entity_addresses_lookup", "chain_id", "network", "address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    chain_id: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    entity: Mapped[EntityRecord] = relationship(back_populates="addresses")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<EntityAddressRecord chain={self.chain_id} addr={self.address[:12]}...>"