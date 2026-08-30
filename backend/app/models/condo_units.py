"""
condo_units — a condo's physical unit inventory.
Prefix: condo_ (assigned to Utrera, Condominium Management module).
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CondoUnit(Base):
    __tablename__ = "condo_units"

    __table_args__ = (
        # Uniqueness is ALWAYS scoped to the org, never global:
        UniqueConstraint("organization_id", "building", "unit_number",
                          name="uq_condo_units_org_building_number"),
        Index("ix_condo_units_org", "organization_id"),
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

    # ── business columns ──
    unit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    building: Mapped[str | None] = mapped_column(String(50), nullable=True)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="vacant")
    # status values enforced in the Pydantic schema / DB CHECK constraint:
    # 'occupied' | 'vacant' | 'under_maintenance'

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
