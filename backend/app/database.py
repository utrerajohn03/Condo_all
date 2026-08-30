"""
Shared declarative Base + engine/session setup.

At integration into ARGO, this single import line is what the platform owner rebases:
    from app.database import Base   ->   from argo.database import Base
Every model file below imports Base from here, so the swap is one edit in one place.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings


class Base(DeclarativeBase):
    pass


# On Vercel, every request can land on a fresh serverless invocation, so a
# normal in-process connection pool just leaks connections against Supabase's
# connection limit. NullPool opens a connection per request and closes it
# right after — combined with Supabase's pgbouncer "Transaction" pooler
# (port 6543) on DATABASE_URL, this is the recommended combo for serverless.
# Locally (uvicorn --reload, one long-lived process) SQLAlchemy's normal
# pooling is used instead, since VERCEL is unset there.
_engine_kwargs = {"pool_pre_ping": True}
if os.environ.get("VERCEL"):
    _engine_kwargs = {"poolclass": NullPool}

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session and always closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
