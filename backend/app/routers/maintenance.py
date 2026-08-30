"""
Maintenance Requests router — implements docs/API_CONTRACT.md.

Threat-model mitigations applied throughout (see docs/THREAT_MODEL.md):
  - Every query filters by organization_id from the verified JWT (cross-tenant access)
  - require_permission() checked before any write (broken authorization)
  - Only whitelisted fields are read from request bodies (mass assignment)
  - All queries are parameterized via SQLAlchemy ORM (SQL injection)
  - unit_id is re-validated to belong to caller's org (cross-tenant FK reference)
  - Not-found vs wrong-org both return 404, so existence is never leaked
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission
from app.core.permissions import role_has_permission
from app.core.state_machine import is_transition_allowed, ASSIGNEE_RESTRICTED_TRANSITIONS
from app.models.condo_maintenance_requests import CondoMaintenanceRequest
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.models._local_stub_platform_tables import LocalStubUser
from app.schemas.condo import (
    MaintenanceRequestCreate, MaintenanceRequestListItem, MaintenanceRequestDetail,
    AssignRequestBody, StatusUpdateBody,
)

router = APIRouter(prefix='/api/condo/maintenance-requests', tags=['maintenance-requests'])


def _residents_unit_ids(db: Session, org_id: UUID, user_id: UUID) -> list:
    rows = db.query(CondoUnitResident.unit_id).filter(
        CondoUnitResident.organization_id == org_id,
        CondoUnitResident.user_id == user_id,
        CondoUnitResident.deleted_at.is_(None),
    ).all()
    return [r[0] for r in rows]


@router.get('', response_model=dict)
def list_requests(
    status_filter: Optional[str] = Query(default=None, alias='status'),
    unit_id: Optional[UUID] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    auth: AuthContext = Depends(require_permission('maintenance.view')),
    db: Session = Depends(get_db),
):
    query = db.query(CondoMaintenanceRequest, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoMaintenanceRequest.unit_id
    ).filter(
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
    )

    if auth.role in ('resident', 'unit_owner'):
        allowed_units = _residents_unit_ids(db, auth.organization_id, auth.user_id)
        query = query.filter(CondoMaintenanceRequest.unit_id.in_(allowed_units))

    if status_filter:
        query = query.filter(CondoMaintenanceRequest.status == status_filter)
    if unit_id:
        query = query.filter(CondoMaintenanceRequest.unit_id == unit_id)
    if priority:
        query = query.filter(CondoMaintenanceRequest.priority == priority)

    rows = query.order_by(CondoMaintenanceRequest.created_at.desc()).all()

    data = [
        MaintenanceRequestListItem(
            id=mr.id, status=mr.status, priority=mr.priority, category=mr.category,
            unit_number=unit_number, assigned_to=mr.assigned_to, created_at=mr.created_at,
        ).model_dump()
        for mr, unit_number in rows
    ]
    return {'data': data}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_request(
    payload: MaintenanceRequestCreate,
    auth: AuthContext = Depends(require_permission('maintenance.create')),
    db: Session = Depends(get_db),
):
    unit = db.query(CondoUnit).filter(
        CondoUnit.id == payload.unit_id,
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.deleted_at.is_(None),
    ).first()
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit not found in your organization.')

    if auth.role in ('resident', 'unit_owner'):
        linked = db.query(CondoUnitResident).filter(
            CondoUnitResident.organization_id == auth.organization_id,
            CondoUnitResident.unit_id == payload.unit_id,
            CondoUnitResident.user_id == auth.user_id,
            CondoUnitResident.deleted_at.is_(None),
        ).first()
        if linked is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                 detail='You are not linked to this unit.')
        # Mass-assignment guard: a Resident's own id always wins, regardless of what
        # (if anything) was sent in requested_by.
        requested_by = auth.user_id
    else:
        # Staff/Manager/Administrator may submit "on behalf of" a resident or unit owner
        # (docs/RBAC_MATRIX.md, Front Desk Staff: "Create a maintenance request on behalf
        # of a resident"). The target must be a resident/unit-owner-role user in the
        # caller's own org — never trust the id blindly, and never let this become a way
        # to forge a request as an arbitrary user.
        if payload.requested_by is not None:
            target_resident = db.query(LocalStubUser).filter(
                LocalStubUser.id == payload.requested_by,
                LocalStubUser.organization_id == auth.organization_id,
                LocalStubUser.role.in_(['resident', 'unit_owner']),
            ).first()
            if target_resident is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                     detail='Resident or unit owner not found in your organization.')
            requested_by = target_resident.id
        else:
            requested_by = auth.user_id

    mr = CondoMaintenanceRequest(
        organization_id=auth.organization_id,
        unit_id=payload.unit_id,
        requested_by=requested_by,
        category=payload.category,
        description=payload.description,
        priority=payload.priority,
        status='submitted',
        created_by=auth.user_id,
        updated_by=auth.user_id,
    )
    db.add(mr)
    db.commit()
    db.refresh(mr)

    return {'data': {'id': str(mr.id), 'status': mr.status, 'requested_by': str(mr.requested_by),
                      'created_at': mr.created_at.isoformat()}}


@router.get('/detail', response_model=dict)
def get_request_detail(
    id: UUID = Query(...),
    auth: AuthContext = Depends(require_permission('maintenance.view')),
    db: Session = Depends(get_db),
):
    mr = db.query(CondoMaintenanceRequest).filter(
        CondoMaintenanceRequest.id == id,
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
    ).first()

    if mr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')

    if auth.role in ('resident', 'unit_owner'):
        allowed_units = _residents_unit_ids(db, auth.organization_id, auth.user_id)
        if mr.unit_id not in allowed_units:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')

    result = MaintenanceRequestDetail.model_validate(mr)
    return {'data': result.model_dump()}


@router.post('/assign', response_model=dict)
def assign_request(
    id: UUID = Query(...),
    payload: AssignRequestBody = ...,
    auth: AuthContext = Depends(require_permission('maintenance.assign')),
    db: Session = Depends(get_db),
):
    mr = db.query(CondoMaintenanceRequest).filter(
        CondoMaintenanceRequest.id == id,
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
    ).first()
    if mr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')

    if mr.status != 'submitted':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                             detail=f'Request is not in submitted status (current: {mr.status}).')

    staff_user = db.query(LocalStubUser).filter(
        LocalStubUser.id == payload.assigned_to,
        LocalStubUser.organization_id == auth.organization_id,
        LocalStubUser.role.in_(['staff', 'manager', 'admin']),
    ).first()
    if staff_user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail='assigned_to must be a valid staff member in your organization.')

    mr.assigned_to = payload.assigned_to
    mr.status = 'assigned'
    mr.scheduled_at = datetime.utcnow()
    mr.updated_by = auth.user_id
    db.commit()
    db.refresh(mr)

    return {'data': {'id': str(mr.id), 'status': mr.status, 'assigned_to': str(mr.assigned_to)}}


@router.post('/status', response_model=dict)
def update_status(
    id: UUID = Query(...),
    payload: StatusUpdateBody = ...,
    auth: AuthContext = Depends(require_permission('maintenance.update_status')),
    db: Session = Depends(get_db),
):
    mr = db.query(CondoMaintenanceRequest).filter(
        CondoMaintenanceRequest.id == id,
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
    ).first()
    if mr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')

    target = payload.status

    if auth.role in ('resident', 'unit_owner'):
        if mr.requested_by != auth.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')
        if target != 'cancelled':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                 detail='Residents and Unit Owners may only cancel their own request.')
        if not is_transition_allowed(mr.status, 'cancelled'):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                 detail=f'Cannot cancel a request in "{mr.status}" status.')
    else:
        if not is_transition_allowed(mr.status, target):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                 detail=f'Invalid transition: "{mr.status}" -> "{target}".')

        if target in ASSIGNEE_RESTRICTED_TRANSITIONS:
            if mr.assigned_to != auth.user_id and not role_has_permission(auth.role, 'maintenance.assign'):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                     detail='Only the assignee, or someone holding maintenance.assign, may make this transition.')

        if target == 'rejected' and not payload.reason:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                 detail='A reason is required when rejecting a request.')

    mr.status = target
    mr.updated_by = auth.user_id
    if target == 'completed':
        mr.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(mr)

    return {'data': {'id': str(mr.id), 'status': mr.status}}


@router.delete('/{id}', response_model=dict)
def delete_request(
    id: UUID,
    auth: AuthContext = Depends(require_permission('maintenance.delete')),
    db: Session = Depends(get_db),
):
    mr = db.query(CondoMaintenanceRequest).filter(
        CondoMaintenanceRequest.id == id,
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
    ).first()
    if mr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Maintenance request not found.')

    mr.deleted_at = datetime.utcnow()
    mr.updated_by = auth.user_id
    db.commit()

    return {'data': {'id': str(mr.id), 'deleted': True}}
