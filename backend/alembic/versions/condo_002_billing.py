"""condo_002_billing

Adds the three tables backing Bill Management, Payments (owner/tenant), and the
Superadmin Portal's portal-configuration tab: condo_bills, condo_payments,
condo_portal_settings, plus their PostgreSQL enum types.

Revision ID: condo_002_billing
Revises: condo_001_initial
Create Date: 2026-08-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

# revision identifiers, used by Alembic.
revision: str = "condo_002_billing"
down_revision: Union[str, None] = "condo_001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

bill_type_enum = ENUM(
    "association_dues", "utility", "other", name="condo_bill_type", create_type=False
)
billing_cycle_enum = ENUM(
    "one_time", "monthly", "quarterly", "annual", name="condo_billing_cycle", create_type=False
)
bill_status_enum = ENUM(
    "pending", "partially_paid", "paid", "overdue", "void", name="condo_bill_status", create_type=False
)
payment_method_enum = ENUM(
    "cash", "bank_transfer", "online", "check", name="condo_payment_method", create_type=False
)
payment_status_enum = ENUM(
    "completed", "pending", "failed", name="condo_payment_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    bill_type_enum.create(bind, checkfirst=True)
    billing_cycle_enum.create(bind, checkfirst=True)
    bill_status_enum.create(bind, checkfirst=True)
    payment_method_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)

    # ── condo_bills ──
    if "condo_bills" not in existing_tables:
        op.create_table(
            "condo_bills",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unit_id", UUID(as_uuid=True),
                      sa.ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False),
            sa.Column("bill_type", bill_type_enum, nullable=False),
            sa.Column("description", sa.String(500), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("billing_cycle", billing_cycle_enum, nullable=False, server_default="one_time"),
            sa.Column("is_recurring_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("period_start", sa.Date(), nullable=True),
            sa.Column("period_end", sa.Date(), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("status", bill_status_enum, nullable=False, server_default="pending"),
            sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_condo_bills_organization_id", "condo_bills", ["organization_id"])
        op.create_index("ix_condo_bills_org", "condo_bills", ["organization_id"])
        op.create_index("ix_condo_bills_unit", "condo_bills", ["unit_id"])
        op.create_index("ix_condo_bills_org_status", "condo_bills", ["organization_id", "status"])

    # ── condo_payments ──
    if "condo_payments" not in existing_tables:
        op.create_table(
            "condo_payments",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("bill_id", UUID(as_uuid=True),
                      sa.ForeignKey("condo_bills.id", ondelete="CASCADE"), nullable=False),
            sa.Column("unit_id", UUID(as_uuid=True),
                      sa.ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False),
            sa.Column("paid_by", UUID(as_uuid=True), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("method", payment_method_enum, nullable=False, server_default="online"),
            sa.Column("reference_number", sa.String(100), nullable=True),
            sa.Column("status", payment_status_enum, nullable=False, server_default="completed"),
            sa.Column("paid_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("notes", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_condo_payments_organization_id", "condo_payments", ["organization_id"])
        op.create_index("ix_condo_payments_org", "condo_payments", ["organization_id"])
        op.create_index("ix_condo_payments_bill", "condo_payments", ["bill_id"])
        op.create_index("ix_condo_payments_unit", "condo_payments", ["unit_id"])

    # ── condo_portal_settings ──
    if "condo_portal_settings" not in existing_tables:
        op.create_table(
            "condo_portal_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True),
                      sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("setting_key", sa.String(100), nullable=False),
            sa.Column("setting_value", sa.String(2000), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
            sa.UniqueConstraint("organization_id", "setting_key", name="uq_condo_portal_settings_org_key"),
        )
        op.create_index("ix_condo_portal_settings_organization_id", "condo_portal_settings", ["organization_id"])
        op.create_index("ix_condo_portal_settings_org", "condo_portal_settings", ["organization_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("condo_portal_settings")
    op.drop_table("condo_payments")
    op.drop_table("condo_bills")

    payment_status_enum.drop(bind, checkfirst=True)
    payment_method_enum.drop(bind, checkfirst=True)
    bill_status_enum.drop(bind, checkfirst=True)
    billing_cycle_enum.drop(bind, checkfirst=True)
    bill_type_enum.drop(bind, checkfirst=True)
