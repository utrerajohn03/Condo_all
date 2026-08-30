"""
condo_payments — a payment applied against a condo_bill. Either self-service (a
Resident/Unit Owner paying their own bill) or recorded on their behalf by
Staff/Manager/Administrator (e.g. a cash or over-the-counter payment).
No real payment gateway is integrated in this vertical slice (out of scope, per
docs/SCOPING.md) — `method` captures how the payment was made/recorded, and
transactions are treated as immediately settled.
Prefix: condo_ (Condominium Management module).
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

payment_method_enum = ENUM(
    "cash", "bank_transfer", "online", "check", name="condo_payment_method", create_type=False
)
payment_status_enum = ENUM(
    "completed", "pending", "failed", name="condo_payment_status", create_type=False
)


class CondoPayment(Base):
    __tablename__ = "condo_payments"

    __table_args__ = (
        Index("ix_condo_payments_org", "organization_id"),
        Index("ix_condo_payments_bill", "bill_id"),
        Index("ix_condo_payments_unit", "unit_id"),
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
    bill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("condo_bills.id", ondelete="CASCADE"),  # same-module FK — allowed
        nullable=False,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("condo_units.id", ondelete="CASCADE"),  # same-module FK — allowed
        nullable=False,
    )

    # ── business columns ──
    # paid_by: NO foreign key — loose reference to a platform user id, per the contract
    # (matches condo_unit_residents.user_id / condo_maintenance_requests.requested_by).
    paid_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(payment_method_enum, nullable=False, default="online")
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(payment_status_enum, nullable=False, default="completed")
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

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
