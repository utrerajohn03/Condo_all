"""
Password hashing (bcrypt via passlib) and JWT issuance/verification (python-jose).
LOCAL SANDBOX STAND-IN — mints a token shaped like ARGO's expected JWT so this module is
testable standalone. Not part of the delivered module (see docs/API_CONTRACT.md).
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(raw_password, hashed_password)


def create_access_token(*, sub: str, org: str, role: str) -> str:
    """
    Issues a JWT whose payload carries `sub` (user id) and `org` (organization id)
    as the ONLY source of identity/tenant context for downstream requests — matching
    the shape ARGO's real platform JWT is expected to have.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {'sub': sub, 'org': org, 'role': role, 'exp': expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
