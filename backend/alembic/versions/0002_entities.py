"""Entity/address registry tables: entities, entity_addresses.

Revision ID: 0002_entities
Revises: 0001_initial
Create Date: 2026-08-28

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_entities"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("tag_source", sa.String(length=255), nullable=False),
        sa.Column("tag_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "entity_addresses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "entity_id",
            sa.Integer(),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chain_id", sa.String(length=32), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("imported_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "chain_id", "network", "address", name="uq_entity_addresses_chain_network_address"
        ),
    )
    op.create_index(
        "ix_entity_addresses_lookup", "entity_addresses", ["chain_id", "network", "address"]
    )


def downgrade() -> None:
    op.drop_index("ix_entity_addresses_lookup", table_name="entity_addresses")
    op.drop_table("entity_addresses")
    op.drop_table("entities")