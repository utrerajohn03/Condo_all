"""
condo_bills — a charge billed to a unit: association dues, utilities, or a one-off
charge. Supports both one-time bills and recurring bills (a recurring bill is
represented by a template row with billing_cycle != 'one_time'; a scheduler/job would
generate the next period's instance from it — out of scope for this vertical slice,
see docs/ASSUMPTIONS_AND_TRADEOFFS.md).
Prefix: condo_ (Condominium Management module).
"""
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

bill_type_enum = ENUM(
    "association_dues", "utility", "other", name="condo_bill_type", create_type=False
)
billing_cycle_enum = ENUM(
    "one_time", "monthly", "quarterly", "annual", name="condo_billing_cycle", create_type=False
)
bill_status_enum = ENUM(
    "pending", "partially_paid", "paid", "overdue", "void", name="condo_bill_status", create_type=False
)


class CondoBill(Base):
    __tablename__ = "condo_bills"

    __table_args__ = (
        Index("ix_condo_bills_org", "organization_id"),
        Index("ix_condo_bills_unit", "unit_id"),
        Index("ix_condo_bills_org_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("condo_units.id", ondelete="CASCADE"),  # same-module FK — allowed
        nullable=False,
    )

    # ── business columns ──
    bill_type: Mapped[str] = mapped_column(bill_type_enum, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    billing_cycle: Mapped[str] = mapped_column(billing_cycle_enum, nullable=False, default="one_time")
    is_recurring_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(bill_status_enum, nullable=False, default="pending")
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # ── audit block: copy verbatim into every table ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
