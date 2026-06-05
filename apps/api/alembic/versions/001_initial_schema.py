"""Initial PostGIS schema

Revision ID: 001
Revises:
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "productions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("shoot_date", sa.DateTime(timezone=True)),
        sa.Column("depot_location", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("call_time", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text()),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "optimization_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("production_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("productions.id")),
        sa.Column("solver_status", sa.String(64), nullable=False),
        sa.Column("total_distance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "saved_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("optimization_runs.id"),
            nullable=False,
        ),
        sa.Column("vehicle_id", sa.String(64), nullable=False),
        sa.Column("vehicle_name", sa.String(128), nullable=False),
        sa.Column("driver_name", sa.String(128), server_default=""),
        sa.Column("total_distance", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "saved_route_stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("saved_routes.id"),
            nullable=False,
        ),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("person_name", sa.String(255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("eta_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("address", sa.Text(), server_default=""),
    )


def downgrade() -> None:
    op.drop_table("saved_route_stops")
    op.drop_table("saved_routes")
    op.drop_table("optimization_runs")
    op.drop_table("addresses")
    op.drop_table("productions")
