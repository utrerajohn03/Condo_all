"""
condo_unit_residents — links a platform user to a unit as owner/tenant/co-resident.
Kept separate from condo_units because occupancy changes over time without deleting history.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

relationship_type_enum = ENUM(
    "owner", "tenant", "co_resident", name="condo_relationship_type", create_type=False
)


class CondoUnitResident(Base):
    __tablename__ = "condo_unit_residents"

    __table_args__ = (
        Index("ix_condo_unit_residents_org", "organization_id"),
        Index("ix_condo_unit_residents_org_user", "organization_id", "user_id"),
        Index("ix_condo_unit_residents_unit", "unit_id"),
        # Only one active primary contact per unit at a time (partial unique index):
        Index(
            "uq_condo_unit_residents_primary_contact",
            "unit_id",
            unique=True,
            postgresql_where=text("is_primary_contact = true AND moved_out_at IS NULL"),
        ),
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
    # user_id: NO foreign key — loose reference to a platform user id, per the contract.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(relationship_type_enum, nullable=False)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    moved_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    moved_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
