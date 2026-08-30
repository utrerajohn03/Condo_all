"""
GET /api/condo/payments — payment history, scoped to the caller's organization.
GET /api/condo/payments/mine — the caller's own payment history (Resident / Unit Owner).
POST /api/condo/payments — make a payment (Resident / Unit Owner, on their own bill) or
record a payment on behalf of a resident/unit owner (Staff / Manager / Administrator).

Same threat-model mitigations as the rest of this module — see docs/THREAT_MODEL.md.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission
from app.models.condo_bills import CondoBill
from app.models.condo_payments import CondoPayment
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.schemas.condo import PaymentCreate, PaymentListItem

router = APIRouter(prefix='/api/condo/payments', tags=['payments'])


def _linked_unit_ids(db: Session, org_id: UUID, user_id: UUID) -> list:
    rows = db.query(CondoUnitResident.unit_id).filter(
        CondoUnitResident.organization_id == org_id,
        CondoUnitResident.user_id == user_id,
        CondoUnitResident.deleted_at.is_(None),
        CondoUnitResident.moved_out_at.is_(None),
    ).all()
    return [r[0] for r in rows]


@router.get('', response_model=dict)
def list_payments(
    unit_id: Optional[UUID] = Query(default=None),
    bill_id: Optional[UUID] = Query(default=None),
    auth: AuthContext = Depends(require_permission('payment.view')),
    db: Session = Depends(get_db),
):
    query = db.query(CondoPayment, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoPayment.unit_id
    ).filter(
        CondoPayment.organization_id == auth.organization_id,
        CondoPayment.deleted_at.is_(None),
    )

    if auth.role in ('resident', 'unit_owner'):
        allowed_units = _linked_unit_ids(db, auth.organization_id, auth.user_id)
        query = query.filter(CondoPayment.unit_id.in_(allowed_units))

    if unit_id is not None:
        query = query.filter(CondoPayment.unit_id == unit_id)
    if bill_id is not None:
        query = query.filter(CondoPayment.bill_id == bill_id)

    rows = query.order_by(CondoPayment.paid_at.desc()).all()
    data = [
        PaymentListItem.model_validate({**p.__dict__, 'unit_number': unit_number}).model_dump()
        for p, unit_number in rows
    ]
    return {'data': data}


@router.get('/mine', response_model=dict)
def list_my_payments(
    auth: AuthContext = Depends(require_permission('payment.view')),
    db: Session = Depends(get_db),
):
    """The caller's own payment history — Owner Portal / Payments section."""
    rows = db.query(CondoPayment, CondoUnit.unit_number).join(
        CondoUnit, CondoUnit.id == CondoPayment.unit_id
    ).filter(
        CondoPayment.organization_id == auth.organization_id,
        CondoPayment.paid_by == auth.user_id,
        CondoPayment.deleted_at.is_(None),
    ).order_by(CondoPayment.paid_at.desc()).all()

    data = [
        PaymentListItem.model_validate({**p.__dict__, 'unit_number': unit_number}).model_dump()
        for p, unit_number in rows
    ]
    return {'data': data}


@router.post('', status_code=status.HTTP_201_CREATED, response_model=dict)
def create_payment(
    payload: PaymentCreate,
    auth: AuthContext = Depends(require_permission('payment.record')),
    db: Session = Depends(get_db),
):
    """
    Resident / Unit Owner: pay one of their own bills — `paid_by` is always forced to
    the caller's own id (mass-assignment guard, mirrors MaintenanceRequestCreate).
    Staff / Manager / Administrator: record a payment on behalf of a resident/unit
    owner (e.g. cash received at the front desk) — `paid_by` is honored from the body.
    """
    bill = db.query(CondoBill).filter(
        CondoBill.id == payload.bill_id,
        CondoBill.organization_id == auth.organization_id,
        CondoBill.deleted_at.is_(None),
    ).first()
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Bill not found in your organization.')
    if bill.status in ('paid', 'void'):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                             detail=f'This bill is already {bill.status} and cannot accept further payments.')

    if auth.role in ('resident', 'unit_owner'):
        allowed_units = _linked_unit_ids(db, auth.organization_id, auth.user_id)
        if bill.unit_id not in allowed_units:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                 detail='Bill not found in your organization.')
        paid_by = auth.user_id
    else:
        paid_by = payload.paid_by or auth.user_id

    payment = CondoPayment(
        organization_id=auth.organization_id,
        bill_id=bill.id,
        unit_id=bill.unit_id,
        paid_by=paid_by,
        amount=payload.amount,
        method=payload.method,
        reference_number=payload.reference_number,
        notes=payload.notes,
        status='completed',
        created_by=auth.user_id,
        updated_by=auth.user_id,
    )
    db.add(payment)

    # Update the bill's running total / status. Overpayment is capped at the bill
    # amount for status purposes but the full payment amount is still recorded.
    bill.amount_paid = float(bill.amount_paid or 0) + payload.amount
    if bill.amount_paid >= float(bill.amount):
        bill.status = 'paid'
    else:
        bill.status = 'partially_paid'
    bill.updated_by = auth.user_id

    db.commit()
    db.refresh(payment)

    unit = db.query(CondoUnit).filter(CondoUnit.id == payment.unit_id).first()
    return {'data': PaymentListItem.model_validate({**payment.__dict__, 'unit_number': unit.unit_number}).model_dump()}
