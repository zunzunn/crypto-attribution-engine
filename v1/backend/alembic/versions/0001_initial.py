"""Initial schema: transactions, token_transfers, ingestion_runs.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-28

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chain_id", sa.String(length=32), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=True),
        sa.Column("tx_hash", sa.String(length=255), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("block_hash", sa.String(length=255), nullable=True),
        sa.Column("block_timestamp", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="confirmed"),
        sa.Column("transaction_type", sa.String(length=24), nullable=False, server_default="native"),
        sa.Column("from_address", sa.String(length=255), nullable=True),
        sa.Column("to_address", sa.String(length=255), nullable=True),
        sa.Column("value", sa.String(length=128), nullable=False, server_default="0"),
        sa.Column("value_decimals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fee", sa.String(length=128), nullable=True),
        sa.Column("input_data", sa.Text(), nullable=True),
        sa.Column("senders", sa.JSON(), nullable=True),
        sa.Column("recipients", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("chain_id", "network", "tx_hash", name="uq_transactions_chain_id_network_tx_hash"),
    )
    op.create_index("ix_transactions_tx_hash", "transactions", ["chain_id", "network", "tx_hash"])
    op.create_index("ix_transactions_from_address", "transactions", ["chain_id", "from_address"])
    op.create_index("ix_transactions_to_address", "transactions", ["chain_id", "to_address"])
    op.create_index("ix_transactions_block_time", "transactions", ["chain_id", "block_timestamp"])

    op.create_table(
        "token_transfers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chain_id", sa.String(length=32), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=True),
        sa.Column("tx_hash", sa.String(length=255), nullable=False),
        sa.Column("transfer_index", sa.Integer(), nullable=False),
        sa.Column("token_address", sa.String(length=255), nullable=False),
        sa.Column("token_symbol", sa.String(length=64), nullable=True),
        sa.Column("token_name", sa.String(length=255), nullable=True),
        sa.Column("token_decimals", sa.Integer(), nullable=True),
        sa.Column("from_address", sa.String(length=255), nullable=True),
        sa.Column("to_address", sa.String(length=255), nullable=True),
        sa.Column("value_raw", sa.String(length=128), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("chain_id", "network", "tx_hash", "transfer_index", name="uq_token_transfers_chain_network_tx_index"),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chain_id", sa.String(length=32), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("total_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_existing", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_table("token_transfers")
    op.drop_index("ix_transactions_block_time", table_name="transactions")
    op.drop_index("ix_transactions_to_address", table_name="transactions")
    op.drop_index("ix_transactions_from_address", table_name="transactions")
    op.drop_index("ix_transactions_tx_hash", table_name="transactions")
    op.drop_table("transactions")