"""condo_001_initial

Creates the three condo_ business tables (condo_units, condo_unit_residents,
condo_maintenance_requests) and their PostgreSQL enum types.

Enum types are created explicitly here (not by the ORM) because every condo_ model
sets create_type=False — Alembic is the single source of truth for schema, per the
Onboarding Contract. This keeps `alembic upgrade head` idempotent even if a type or
table already exists from an earlier partial run.

Revision ID: condo_001_initial
Revises: condo_zzz_local_stub
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

# revision identifiers, used by Alembic.
revision: str = "condo_001_initial"
down_revision: Union[str, None] = "condo_zzz_local_stub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── enum definitions (create_type=False: creation/drop is handled by hand below,
#    matching the app.models.* enum objects field-for-field) ──
relationship_type_enum = ENUM(
    "owner", "tenant", "co_resident", name="condo_relationship_type", create_type=False
)
priority_enum = ENUM(
    "low", "medium", "high", "urgent", name="condo_priority", create_type=False
)
status_enum = ENUM(
    "submitted", "assigned", "in_progress", "completed", "cancelled", "rejected",
    name="condo_request_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Enum types first — checkfirst makes this safe to re-run.
    relationship_type_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # ── condo_units ──
    if "condo_units" not in existing_tables:
        op.create_table(
            "condo_units",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unit_number", sa.String(20), nullable=False),
            sa.Column("building", sa.String(50), nullable=True),
            sa.Column("floor", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="vacant"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("organization_id", "building", "unit_number",
                                 name="uq_condo_units_org_building_number"),
        )
        op.create_index("ix_condo_units_organization_id", "condo_units", ["organization_id"])
        op.create_index("ix_condo_units_org", "condo_units", ["organization_id"])

    # ── condo_unit_residents ──
    if "condo_unit_residents" not in existing_tables:
        op.create_table(
            "condo_unit_residents",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unit_id", UUID(as_uuid=True),
                      sa.ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("relationship_type", relationship_type_enum, nullable=False),
            sa.Column("is_primary_contact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("moved_in_at", sa.DateTime(), nullable=False),
            sa.Column("moved_out_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_condo_unit_residents_organization_id", "condo_unit_residents", ["organization_id"])
        op.create_index("ix_condo_unit_residents_org", "condo_unit_residents", ["organization_id"])
        op.create_index("ix_condo_unit_residents_org_user", "condo_unit_residents",
                         ["organization_id", "user_id"])
        op.create_index("ix_condo_unit_residents_unit", "condo_unit_residents", ["unit_id"])
        # Partial unique index: only one active primary contact per unit at a time.
        op.create_index(
            "uq_condo_unit_residents_primary_contact",
            "condo_unit_residents",
            ["unit_id"],
            unique=True,
            postgresql_where=sa.text("is_primary_contact = true AND moved_out_at IS NULL"),
        )

    # ── condo_maintenance_requests ──
    if "condo_maintenance_requests" not in existing_tables:
        op.create_table(
            "condo_maintenance_requests",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unit_id", UUID(as_uuid=True),
                      sa.ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False),
            sa.Column("requested_by", UUID(as_uuid=True), nullable=False),
            sa.Column("assigned_to", UUID(as_uuid=True), nullable=True),
            sa.Column("category", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("priority", priority_enum, nullable=False, server_default="medium"),
            sa.Column("status", status_enum, nullable=False, server_default="submitted"),
            sa.Column("scheduled_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_condo_maintenance_requests_organization_id", "condo_maintenance_requests",
                         ["organization_id"])
        op.create_index("ix_condo_maintenance_org_status", "condo_maintenance_requests",
                         ["organization_id", "status"])
        op.create_index("ix_condo_maintenance_org_unit", "condo_maintenance_requests",
                         ["organization_id", "unit_id"])
        op.create_index("ix_condo_maintenance_org_assignee", "condo_maintenance_requests",
                         ["organization_id", "assigned_to"])


def downgrade() -> None:
    bind = op.get_bind()

    # Reverse order of creation — condo_maintenance_requests and
    # condo_unit_residents both FK to condo_units, so they must drop first.
    op.drop_table("condo_maintenance_requests")
    op.drop_table("condo_unit_residents")
    op.drop_table("condo_units")

    status_enum.drop(bind, checkfirst=True)
    priority_enum.drop(bind, checkfirst=True)
    relationship_type_enum.drop(bind, checkfirst=True)
