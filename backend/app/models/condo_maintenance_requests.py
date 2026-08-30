"""
condo_maintenance_requests — the core entity. A resident-submitted work order tied to a
unit, with its own lifecycle (see docs/WORKFLOW.md for the full state machine).
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

priority_enum = ENUM(
    "low", "medium", "high", "urgent", name="condo_priority", create_type=False
)
status_enum = ENUM(
    "submitted", "assigned", "in_progress", "completed", "cancelled", "rejected",
    name="condo_request_status", create_type=False,
)


class CondoMaintenanceRequest(Base):
    __tablename__ = "condo_maintenance_requests"

    __table_args__ = (
        Index("ix_condo_maintenance_org_status", "organization_id", "status"),
        Index("ix_condo_maintenance_org_unit", "organization_id", "unit_id"),
        Index("ix_condo_maintenance_org_assignee", "organization_id", "assigned_to"),
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
    # requested_by / assigned_to: NO foreign key — loose reference to a user id, per contract.
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(priority_enum, nullable=False, default="medium")
    status: Mapped[str] = mapped_column(status_enum, nullable=False, default="submitted")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
