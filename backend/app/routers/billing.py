"""
GET/POST/PATCH /api/condo/bills — bill management (association dues, utilities, and
one-time/other charges), scoped to the caller's organization.
GET /api/condo/bills/mine — the caller's own unit(s) bills (Resident / Unit Owner).

Same threat-model mitigations as the rest of this module (see docs/THREAT_MODEL.md):
every query filters by organization_id from the verified JWT, require_permission() is
checked before any write, unit_id is re-validated to belong to the caller's org, and
Resident/Unit Owner scoping is layered on top of (not instead of) the permission check.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission
from app.models.condo_bills import CondoBill
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.schemas.condo import BillCreate, BillListItem, BillUpdate

router = APIRouter(prefix='/api/condo/bills', tags=['bills'])


def _linked_unit_ids(db: Session, org_id: UUID, user_id: UUID) -> list:
    rows = db.query(CondoUnitResident.unit_id).filter(
        CondoUnitResident.organization_id == org_id,
        CondoUnitResident.user_id == user_id,
        CondoUnitResident.deleted_at.is_(None),
        CondoUnitResident.moved_out_at.is_(None),
    ).all()
    return [r[0] for r in rows]


@router.get('', response_model=dict)
def list_bills(
    unit_id: Optional[UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias='status'),
    bill_type: Optional[str] = Query(default=None),
    auth: AuthContext = Depends(require_permission('billing.view')),
    db: Session = Depends(get_db),
):
    query = db.query(CondoBill, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoBill.unit_id
    ).filter(
        CondoBill.organization_id == auth.organization_id,
        CondoBill.deleted_at.is_(None),
    )

    # Resident / Unit Owner: bills for units they're currently linked to only.
    # Staff/Manager/Administrator: full org view ("bill management" surface).
    if auth.role in ('resident', 'unit_owner'):
        allowed_units = _linked_unit_ids(db, auth.organization_id, auth.user_id)
        query = query.filter(CondoBill.unit_id.in_(allowed_units))

    if unit_id is not None:
        query = query.filter(CondoBill.unit_id == unit_id)
    if status_filter is not None:
        query = query.filter(CondoBill.status == status_filter)
    if bill_type is not None:
        query = query.filter(CondoBill.bill_type == bill_type)

    rows = query.order_by(CondoBill.due_date.desc()).all()
    data = [
        BillListItem.model_validate({**bill.__dict__, 'unit_number': unit_number}).model_dump()
        for bill, unit_number in rows
    ]
    return {'data': data}


@router.get('/mine', response_model=dict)
def list_my_bills(
    auth: AuthContext = Depends(require_permission('billing.view')),
    db: Session = Depends(get_db),
):
    """The caller's own bills, across every unit they're currently linked to — the
    core data source for both the Owner Portal and the tenant-facing Payments section.
    """
    allowed_units = _linked_unit_ids(db, auth.organization_id, auth.user_id)
    rows = db.query(CondoBill, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoBill.unit_id
    ).filter(
        CondoBill.organization_id == auth.organization_id,
        CondoBill.unit_id.in_(allowed_units),
        CondoBill.deleted_at.is_(None),
    ).order_by(CondoBill.due_date.asc()).all()

    data = [
        BillListItem.model_validate({**bill.__dict__, 'unit_number': unit_number}).model_dump()
        for bill, unit_number in rows
    ]
    return {'data': data}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_bill(
    payload: BillCreate,
    auth: AuthContext = Depends(require_permission('billing.manage')),
    db: Session = Depends(get_db),
):
    """Property Manager / Administrator: create a recurring or one-time bill
    (association dues, utility, or other) for a unit in their own organization."""
    unit = db.query(CondoUnit).filter(
        CondoUnit.id == payload.unit_id,
        CondoUnit.organization_id == auth.organization_id,
        CondoUnit.deleted_at.is_(None),
    ).first()
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Unit not found in your organization.')

    bill = CondoBill(
        organization_id=auth.organization_id,
        unit_id=payload.unit_id,
        bill_type=payload.bill_type,
        description=payload.description,
        amount=payload.amount,
        billing_cycle=payload.billing_cycle,
        is_recurring_template=payload.billing_cycle != 'one_time',
        period_start=payload.period_start,
        period_end=payload.period_end,
        due_date=payload.due_date,
        status='pending',
        amount_paid=0,
        created_by=auth.user_id,
        updated_by=auth.user_id,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    return {'data': BillListItem.model_validate({**bill.__dict__, 'unit_number': unit.unit_number}).model_dump()}


@router.patch('/{id}', response_model=dict)
def update_bill(
    id: UUID,
    payload: BillUpdate,
    auth: AuthContext = Depends(require_permission('billing.manage')),
    db: Session = Depends(get_db),
):
    """Property Manager / Administrator: edit or void a bill."""
    bill = db.query(CondoBill).filter(
        CondoBill.id == id,
        CondoBill.organization_id == auth.organization_id,
        CondoBill.deleted_at.is_(None),
    ).first()
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bill not found in your organization.')

    if payload.description is not None:
        bill.description = payload.description
    if payload.amount is not None:
        bill.amount = payload.amount
    if payload.due_date is not None:
        bill.due_date = payload.due_date
    if payload.status is not None:
        bill.status = payload.status
    bill.updated_by = auth.user_id

    db.commit()
    db.refresh(bill)
    unit = db.query(CondoUnit).filter(CondoUnit.id == bill.unit_id).first()
    return {'data': BillListItem.model_validate({**bill.__dict__, 'unit_number': unit.unit_number}).model_dump()}
