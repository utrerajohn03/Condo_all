"""
condo_portal_settings — condo-wide (organization-wide) key/value configuration,
managed exclusively through the Superadmin Portal (Administrator role only).
Examples: default late-fee percent, default due-day-of-month for dues, which
optional module sections are enabled, display currency, etc. Kept as a simple
key/value table (rather than a fixed-column settings row) so new settings can be
added without a migration — this matches how the panel described "portal
configuration" as an open-ended set of toggles, not a fixed schema.
Prefix: condo_ (Condominium Management module).
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CondoPortalSetting(Base):
    __tablename__ = "condo_portal_settings"

    __table_args__ = (
        UniqueConstraint("organization_id", "setting_key", name="uq_condo_portal_settings_org_key"),
        Index("ix_condo_portal_settings_org", "organization_id"),
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
    setting_key: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_value: Mapped[str] = mapped_column(String(2000), nullable=False)

    # ── audit block: copy verbatim into every table ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
