"""condo_zzz_local_stub

LOCAL SANDBOX ONLY — this migration is NOT part of the module deliverable and is
discarded at integration. `organizations` and `users` already exist in the real ARGO
platform; this stub exists purely so this module's foreign keys resolve while
developing/testing standalone, outside of ARGO (see docs/ASSUMPTIONS_AND_TRADEOFFS.md
#1 and the Onboarding Contract, Part B §9).

At integration, the platform owner deletes this file and re-points condo_001_initial's
down_revision at Argo's real head — that is the only edit that happens to this
migration chain, and they do it, not the intern.

Revision ID: condo_zzz_local_stub
Revises:
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "condo_zzz_local_stub"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Guarded: additive/idempotent, per the contract — never re-create a table
    # that's already there (e.g. if the real Argo tables are ever present).
    if "organizations" not in existing_tables:
        op.create_table(
            "organizations",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False,
                      server_default=sa.text("now()")),
        )

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("full_name", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("role", sa.String(50), nullable=False,
                      server_default="resident"),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False,
                      server_default=sa.text("true")),
        )


def downgrade() -> None:
    # Reverse order of creation.
    op.drop_table("users")
    op.drop_table("organizations")
