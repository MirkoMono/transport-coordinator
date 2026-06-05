"""Add driver check-in and delay fields to stops

Revision ID: 002
Revises: 001
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "saved_route_stops",
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saved_route_stops",
        sa.Column("delay_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "saved_route_stops",
        sa.Column("delay_note", sa.Text(), server_default="", nullable=True),
    )


def downgrade() -> None:
    op.drop_column("saved_route_stops", "delay_note")
    op.drop_column("saved_route_stops", "delay_minutes")
    op.drop_column("saved_route_stops", "checked_in_at")
