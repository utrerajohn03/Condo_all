"""
POST /api/auth/login
LOCAL SANDBOX STAND-IN ONLY — in real ARGO the platform issues this token before the user
ever reaches this module. Exists here solely so this module is testable standalone.
Not part of what's handed over at integration (see docs/API_CONTRACT.md).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models._local_stub_platform_tables import LocalStubUser
from app.core.security import verify_password, create_access_token
from app.schemas.condo import LoginRequest, LoginResponse

router = APIRouter(prefix='/api/auth', tags=['auth (local sandbox stand-in)'])


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Missing fields.')

    user = db.query(LocalStubUser).filter(LocalStubUser.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials.')

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='This account has been deactivated.')

    token = create_access_token(sub=str(user.id), org=str(user.organization_id), role=user.role)
    return LoginResponse(token=token, role=user.role)
