"""
/api/condo/users — "Manage Users" (Administrator) + GET /me (own profile, any role).

LOCAL SANDBOX STAND-IN ONLY. In real ARGO, users/organizations are platform-owned —
per the Onboarding Contract (Part B §4), this module must never take a foreign key to
`users`, and per §9 the local `users` table itself is a throwaway bootstrap stub. These
endpoints exist only so "Administrator manages users" is demonstrable standalone in this
assessment, the same way POST /api/auth/login stands in for platform authentication.
None of this is handed over at integration — in real ARGO, account management happens
in the platform's own admin surface, not inside the condo_ module.
"""
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission, get_current_auth
from app.core.security import hash_password
from app.models._local_stub_platform_tables import LocalStubUser
from app.schemas.condo import UserProfileOut, UserListItem, UserCreate, UserUpdate

router = APIRouter(prefix='/api/condo/users', tags=['users'])


@router.get('/me', response_model=dict)
def get_my_profile(
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """"View their own profile" — every authenticated role, own record only."""
    user = db.query(LocalStubUser).filter(
        LocalStubUser.id == auth.user_id,
        LocalStubUser.organization_id == auth.organization_id,
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Profile not found.')
    return {'data': UserProfileOut.model_validate(user).model_dump()}


@router.get('', response_model=dict)
def list_users(
    role: str | None = Query(default=None, description='Optional filter, e.g. role=resident'),
    auth: AuthContext = Depends(require_permission('user.view')),
    db: Session = Depends(get_db),
):
    """Staff/Manager/Administrator: "View residents" / "View users" — org-scoped list."""
    query = db.query(LocalStubUser).filter(LocalStubUser.organization_id == auth.organization_id)
    if role:
        query = query.filter(LocalStubUser.role == role)
    users = query.order_by(LocalStubUser.full_name).all()
    return {'data': [UserListItem.model_validate(u).model_dump() for u in users]}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_user(
    payload: UserCreate,
    auth: AuthContext = Depends(require_permission('user.manage')),
    db: Session = Depends(get_db),
):
    """Administrator: "Add users"."""
    existing = db.query(LocalStubUser).filter(LocalStubUser.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already in use.')

    user = LocalStubUser(
        id=uuid4(),
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization_id=auth.organization_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'data': UserListItem.model_validate(user).model_dump()}


@router.patch('/{id}', response_model=dict)
def update_user(
    id: UUID,
    payload: UserUpdate,
    auth: AuthContext = Depends(require_permission('user.manage')),
    db: Session = Depends(get_db),
):
    """Administrator: "Edit users"."""
    user = db.query(LocalStubUser).filter(
        LocalStubUser.id == id, LocalStubUser.organization_id == auth.organization_id,
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found in your organization.')

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return {'data': UserListItem.model_validate(user).model_dump()}


@router.post('/{id}/activate', response_model=dict)
def activate_user(
    id: UUID,
    auth: AuthContext = Depends(require_permission('user.manage')),
    db: Session = Depends(get_db),
):
    """Administrator: "Activate ... users"."""
    return _set_active(id, True, auth, db)


@router.post('/{id}/deactivate', response_model=dict)
def deactivate_user(
    id: UUID,
    auth: AuthContext = Depends(require_permission('user.manage')),
    db: Session = Depends(get_db),
):
    """Administrator: "... or deactivate users". A deactivated user can no longer log in
    (see routers/auth.py) but the record itself is preserved, not deleted."""
    if id == auth.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail='You cannot deactivate your own account.')
    return _set_active(id, False, auth, db)


def _set_active(id: UUID, is_active: bool, auth: AuthContext, db: Session) -> dict:
    user = db.query(LocalStubUser).filter(
        LocalStubUser.id == id, LocalStubUser.organization_id == auth.organization_id,
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found in your organization.')
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return {'data': UserListItem.model_validate(user).model_dump()}


@router.delete('/{id}', response_model=dict)
def delete_user(
    id: UUID,
    auth: AuthContext = Depends(require_permission('user.manage')),
    db: Session = Depends(get_db),
):
    """Administrator: "Delete users". Hard delete on this local-stub-only table (it carries
    no deleted_at/audit trail requirement — unlike condo_ business tables, which always
    soft-delete)."""
    if id == auth.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail='You cannot delete your own account.')
    user = db.query(LocalStubUser).filter(
        LocalStubUser.id == id, LocalStubUser.organization_id == auth.organization_id,
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found in your organization.')
    db.delete(user)
    db.commit()
    return {'data': {'id': str(id), 'deleted': True}}
