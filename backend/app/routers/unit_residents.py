"""
/api/condo/unit-residents — "Resident Assignments" (Staff: view only; Manager/Admin: manage).

Links a platform user (loose UUID — no FK, per the Onboarding Contract's "FK to users —
never" rule) to a unit as owner/tenant/co-resident. Kept as its own table (not just a
column on units) because occupancy changes over time without deleting history.
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission
from app.models.condo_unit_residents import CondoUnitResident
from app.models.condo_units import CondoUnit
from app.models._local_stub_platform_tables import LocalStubUser
from app.schemas.condo import UnitResidentCreate, UnitResidentListItem

router = APIRouter(prefix='/api/condo/unit-residents', tags=['resident-assignments'])


@router.get('', response_model=dict)
def list_assignments(
    auth: AuthContext = Depends(require_permission('assignment.view')),
    db: Session = Depends(get_db),
):
    """Staff: "View resident-to-unit assignments". Manager/Admin also have this via
    assignment.manage-implying-view membership in ROLE_PERMISSIONS.

    Unit Owner: same permission, but scoped to only the unit(s) they currently own —
    an owner may see who else (e.g. a tenant) is linked to their own unit, but must
    not see assignment data for units they have no stake in (ownership scoping is
    layered on top of the permission check, same pattern as units.py/billing.py)."""
    query = db.query(CondoUnitResident, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoUnitResident.unit_id
    ).filter(
        CondoUnitResident.organization_id == auth.organization_id,
        CondoUnitResident.deleted_at.is_(None),
    )

    if auth.role == 'unit_owner':
        owned_unit_ids = [
            row[0] for row in db.query(CondoUnitResident.unit_id).filter(
                CondoUnitResident.organization_id == auth.organization_id,
                CondoUnitResident.user_id == auth.user_id,
                CondoUnitResident.relationship_type == 'owner',
                CondoUnitResident.deleted_at.is_(None),
                CondoUnitResident.moved_out_at.is_(None),
            ).all()
        ]
        query = query.filter(CondoUnitResident.unit_id.in_(owned_unit_ids))

    rows = query.order_by(CondoUnitResident.moved_in_at.desc()).all()

    # user_id has no FK (per contract), so resident name/email is resolved with a
    # second, explicit lookup rather than a SQL join across module boundaries.
    user_ids = {row[0].user_id for row in rows}
    users_by_id = {
        u.id: u for u in db.query(LocalStubUser).filter(LocalStubUser.id.in_(user_ids)).all()
    } if user_ids else {}

    data = []
    for ur, unit_number in rows:
        resident = users_by_id.get(ur.user_id)
        data.append(UnitResidentListItem(
            id=ur.id,
            unit_id=ur.unit_id,
            unit_number=unit_number,
            user_id=ur.user_id,
            resident_name=resident.full_name if resident else '(unknown user)',
            resident_email=resident.email if resident else '',
            relationship_type=ur.relationship_type,
            is_primary_contact=ur.is_primary_contact,
            moved_in_at=ur.moved_in_at,
            moved_out_at=ur.moved_out_at,
        ).model_dump())

    return {'data': data}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_assignment(
    payload: UnitResidentCreate,
    auth: AuthContext = Depends(require_permission('assignment.manage')),
    db: Session = Depends(get_db),
):
    """Manager/Administrator: "Manage resident-to-unit assignments"."""
    unit = db.query(CondoUnit).filter(
        CondoUnit.id == payload.unit_id,
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.deleted_at.is_(None),
    ).first()
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit not found in your organization.')

    resident = db.query(LocalStubUser).filter(
        LocalStubUser.id == payload.user_id,
        LocalStubUser.organization_id == auth.organization_id,
    ).first()
    if resident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found in your organization.')

    if payload.is_primary_contact:
        conflict = db.query(CondoUnitResident).filter(
            CondoUnitResident.unit_id == payload.unit_id,
            CondoUnitResident.is_primary_contact.is_(True),
            CondoUnitResident.moved_out_at.is_(None),
        ).first()
        if conflict is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                 detail='This unit already has an active primary contact.')

    ur = CondoUnitResident(
        organization_id=auth.organization_id,
        unit_id=payload.unit_id,
        user_id=payload.user_id,
        relationship_type=payload.relationship_type,
        is_primary_contact=payload.is_primary_contact,
        moved_in_at=payload.moved_in_at or datetime.utcnow(),
        created_by=auth.user_id,
        updated_by=auth.user_id,
    )
    db.add(ur)
    db.commit()
    db.refresh(ur)

    return {'data': {
        'id': str(ur.id), 'unit_id': str(ur.unit_id), 'user_id': str(ur.user_id),
        'relationship_type': ur.relationship_type, 'moved_in_at': ur.moved_in_at.isoformat(),
    }}


@router.post('/end', response_model=dict)
def end_assignment(
    id: UUID = Query(...),
    auth: AuthContext = Depends(require_permission('assignment.manage')),
    db: Session = Depends(get_db),
):
    """Manager/Administrator: ends an active assignment (sets moved_out_at) without
    deleting the history row — matches units_residents' move-in/move-out design intent."""
    ur = db.query(CondoUnitResident).filter(
        CondoUnitResident.id == id,
        CondoUnitResident.organization_id == auth.organization_id,
        CondoUnitResident.deleted_at.is_(None),
    ).first()
    if ur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Assignment not found in your organization.')
    if ur.moved_out_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This assignment has already ended.')

    ur.moved_out_at = datetime.utcnow()
    ur.updated_by = auth.user_id
    db.commit()
    db.refresh(ur)

    return {'data': {'id': str(ur.id), 'moved_out_at': ur.moved_out_at.isoformat()}}
