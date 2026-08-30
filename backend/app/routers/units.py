"""
GET/POST/PATCH /api/condo/units — unit records, scoped to the caller's organization.
GET /api/condo/units/mine — the caller's own linked unit(s) (any authenticated role).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission, get_current_auth
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.schemas.condo import UnitCreate, UnitListItem, UnitUpdate

router = APIRouter(prefix='/api/condo/units', tags=['units'])


@router.get('', response_model=dict)
def list_units(
    auth: AuthContext = Depends(require_permission('unit.view')),
    db: Session = Depends(get_db),
):
    query = db.query(CondoUnit).filter(
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.deleted_at.is_(None),
    )

    # Residents and Unit Owners must not see other units — scope to units they are
    # currently linked to. Staff/Manager/Administrator see the full org list
    # ("View units" / "View all system records" per docs/RBAC_MATRIX.md).
    if auth.role in ('resident', 'unit_owner'):
        linked_unit_ids = [
            row[0] for row in db.query(CondoUnitResident.unit_id).filter(
                CondoUnitResident.organization_id == auth.organization_id,
                CondoUnitResident.user_id == auth.user_id,
                CondoUnitResident.deleted_at.is_(None),
                CondoUnitResident.moved_out_at.is_(None),
            ).all()
        ]
        query = query.filter(CondoUnit.id.in_(linked_unit_ids))

    units = query.order_by(CondoUnit.building, CondoUnit.unit_number).all()

    data = [UnitListItem.model_validate(u).model_dump() for u in units]
    return {'data': data}


@router.get('/mine', response_model=dict)
def list_my_units(
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """
    The caller's own currently-linked unit(s) — "View their assigned unit / unit
    information" (docs/RBAC_MATRIX.md, Resident). Available to every authenticated
    role (not permission-gated beyond auth) since it only ever returns the CALLER's
    own linkage rows, never anyone else's — there is nothing to over-expose here.
    """
    rows = db.query(CondoUnit).join(
        CondoUnitResident, CondoUnitResident.unit_id == CondoUnit.id
    ).filter(
        CondoUnitResident.organization_id == auth.organization_id,
        CondoUnitResident.user_id == auth.user_id,
        CondoUnitResident.deleted_at.is_(None),
        CondoUnitResident.moved_out_at.is_(None),
        CondoUnit.deleted_at.is_(None),
    ).all()

    data = [UnitListItem.model_validate(u).model_dump() for u in rows]
    return {'data': data}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_unit(
    payload: UnitCreate,
    auth: AuthContext = Depends(require_permission('unit.manage')),
    db: Session = Depends(get_db),
):
    existing = db.query(CondoUnit).filter(
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.building == payload.building,
        CondoUnit.unit_number == payload.unit_number,
        CondoUnit.deleted_at.is_(None),
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                             detail='A unit with this number already exists in this building.')

    unit = CondoUnit(
        organization_id=auth.organization_id,
        unit_number=payload.unit_number,
        building=payload.building,
        floor=payload.floor,
        status=payload.status,
        created_by=auth.user_id,
        updated_by=auth.user_id,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    return {'data': UnitListItem.model_validate(unit).model_dump()}


@router.patch('/{id}', response_model=dict)
def update_unit(
    id: UUID,
    payload: UnitUpdate,
    auth: AuthContext = Depends(require_permission('unit.manage')),
    db: Session = Depends(get_db),
):
    """Property Manager / Administrator: "Manage units" (docs/RBAC_MATRIX.md)."""
    unit = db.query(CondoUnit).filter(
        CondoUnit.id == id,
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.deleted_at.is_(None),
    ).first()
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit not found in your organization.')

    if payload.unit_number is not None:
        unit.unit_number = payload.unit_number
    if payload.building is not None:
        unit.building = payload.building
    if payload.floor is not None:
        unit.floor = payload.floor
    if payload.status is not None:
        unit.status = payload.status
    unit.updated_by = auth.user_id

    db.commit()
    db.refresh(unit)
    return {'data': UnitListItem.model_validate(unit).model_dump()}
