"""
LOCAL SANDBOX STUB ONLY — this file is NOT part of the module deliverable.

organizations and users already exist in the real ARGO platform. This stub exists purely so
this module's foreign keys resolve while developing/testing standalone, outside of ARGO. At
integration, this file is deleted; the real Argo `organizations` and `users` tables take over
and this module's foreign keys line up automatically without any change on this module's side.

Do not hand this file over as part of the submission's /backend source — it is referenced here
(and in a matching Alembic migration, condo_zzz_local_stub) only for local runnability.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LocalStubOrganization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LocalStubUser(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="resident")
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Added for the "Manage Users" feature (activate/deactivate). Local-stub-only column —
    # in real ARGO this lives on the platform's own users table, not this module's.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
