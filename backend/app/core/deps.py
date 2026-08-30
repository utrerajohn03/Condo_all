"""
FastAPI dependencies for authentication (JWT) and RBAC enforcement.
"""
from dataclasses import dataclass
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.core.permissions import role_has_permission
from app.models._local_stub_platform_tables import LocalStubUser

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    """
    Identity/tenant context for the current request, derived exclusively from the
    verified JWT payload. Nothing from the request body, query string, or headers
    is ever used for identity/tenant purposes.
    """
    user_id: UUID
    organization_id: UUID
    role: str


def get_current_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token.')

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token.')

    user_id = payload.get('sub')
    org_id = payload.get('org')
    role = payload.get('role')
    if not user_id or not org_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Malformed token payload.')

    user = db.query(LocalStubUser).filter(
        LocalStubUser.id == user_id, LocalStubUser.organization_id == org_id
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Account no longer exists.')
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='This account has been deactivated.')

    return AuthContext(user_id=UUID(str(user_id)), organization_id=UUID(str(org_id)), role=role)


def require_permission(permission: str):
    """
    Dependency factory: raises 403 if the caller's role lacks the given permission.
    Usage: Depends(require_permission('maintenance.assign'))
    """
    def _checker(auth: AuthContext = Depends(get_current_auth)) -> AuthContext:
        if not role_has_permission(auth.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                 detail=f'Role "{auth.role}" lacks permission "{permission}".')
        return auth
    return _checker
