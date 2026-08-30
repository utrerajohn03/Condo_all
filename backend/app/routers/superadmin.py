"""
Superadmin Portal — condo-wide settings, users, billing configuration, and portal
configuration. Administrator-only (`superadmin.access`; see docs/RBAC_MATRIX.md).

User management itself is NOT duplicated here — the Superadmin Portal frontend
surface reuses the existing /api/condo/users endpoints (list/create/update/
activate/deactivate/delete), all of which already require Administrator-only
`user.manage` for writes. This router only covers what the Superadmin Portal adds
on top of that: organization identity, billing defaults, and open-ended portal
configuration toggles (condo_portal_settings).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import AuthContext, require_permission
from app.models._local_stub_platform_tables import LocalStubOrganization, LocalStubUser
from app.models.condo_bills import CondoBill
from app.models.condo_maintenance_requests import CondoMaintenanceRequest
from app.models.condo_portal_settings import CondoPortalSetting
from app.models.condo_units import CondoUnit
from app.schemas.condo import (
    OrganizationOut, OrganizationUpdate, PortalSettingOut, PortalSettingUpdate,
    SuperadminOverview,
)

router = APIRouter(prefix='/api/superadmin', tags=['superadmin'])

# Sensible defaults for known configuration keys, returned even before an
# Administrator has explicitly saved a value — the Portal Configuration tab reads
# and writes against this same key set.
_DEFAULT_PORTAL_SETTINGS = {
    'currency': 'PHP',
    'late_fee_percent': '2',
    'dues_due_day_of_month': '5',
    'enable_owner_portal': 'true',
    'enable_online_payments': 'true',
    'enable_maintenance_requests': 'true',
}


@router.get('/overview', response_model=dict)
def get_overview(
    auth: AuthContext = Depends(require_permission('superadmin.access')),
    db: Session = Depends(get_db),
):
    """Condo-wide KPIs for the Superadmin Portal landing tab."""
    total_units = db.query(CondoUnit).filter(
        CondoUnit.organization_id == auth.organization_id, CondoUnit.deleted_at.is_(None),
    ).count()
    total_users = db.query(LocalStubUser).filter(
        LocalStubUser.organization_id == auth.organization_id,
    ).count()
    active_users = db.query(LocalStubUser).filter(
        LocalStubUser.organization_id == auth.organization_id, LocalStubUser.is_active.is_(True),
    ).count()
    outstanding_bills = db.query(CondoBill).filter(
        CondoBill.organization_id == auth.organization_id,
        CondoBill.deleted_at.is_(None),
        CondoBill.status.in_(['pending', 'partially_paid', 'overdue']),
    ).all()
    total_outstanding = sum(float(b.amount) - float(b.amount_paid or 0) for b in outstanding_bills)
    all_bills = db.query(CondoBill).filter(
        CondoBill.organization_id == auth.organization_id, CondoBill.deleted_at.is_(None),
    ).all()
    total_collected = sum(float(b.amount_paid or 0) for b in all_bills)
    pending_maintenance = db.query(CondoMaintenanceRequest).filter(
        CondoMaintenanceRequest.organization_id == auth.organization_id,
        CondoMaintenanceRequest.deleted_at.is_(None),
        CondoMaintenanceRequest.status.in_(['submitted', 'assigned', 'in_progress']),
    ).count()

    overview = SuperadminOverview(
        total_units=total_units,
        total_users=total_users,
        active_users=active_users,
        total_bills_outstanding=round(total_outstanding, 2),
        total_collected=round(total_collected, 2),
        pending_maintenance_requests=pending_maintenance,
    )
    return {'data': overview.model_dump()}


@router.get('/organization', response_model=dict)
def get_organization(
    auth: AuthContext = Depends(require_permission('superadmin.access')),
    db: Session = Depends(get_db),
):
    org = db.query(LocalStubOrganization).filter(
        LocalStubOrganization.id == auth.organization_id,
    ).first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found.')
    return {'data': OrganizationOut.model_validate(org).model_dump()}


@router.patch('/organization', response_model=dict)
def update_organization(
    payload: OrganizationUpdate,
    auth: AuthContext = Depends(require_permission('superadmin.access')),
    db: Session = Depends(get_db),
):
    """Administrator: rename the condominium corporation (condo-wide setting)."""
    org = db.query(LocalStubOrganization).filter(
        LocalStubOrganization.id == auth.organization_id,
    ).first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found.')
    org.name = payload.name
    db.commit()
    db.refresh(org)
    return {'data': OrganizationOut.model_validate(org).model_dump()}


@router.get('/portal-config', response_model=dict)
def get_portal_config(
    auth: AuthContext = Depends(require_permission('superadmin.access')),
    db: Session = Depends(get_db),
):
    """Every portal configuration key/value for this organization, merged over the
    documented defaults so the frontend always has something to render."""
    rows = db.query(CondoPortalSetting).filter(
        CondoPortalSetting.organization_id == auth.organization_id,
    ).all()
    merged = dict(_DEFAULT_PORTAL_SETTINGS)
    merged.update({row.setting_key: row.setting_value for row in rows})
    data = [PortalSettingOut(setting_key=k, setting_value=v).model_dump() for k, v in merged.items()]
    return {'data': data}


@router.put('/portal-config/{key}', response_model=dict)
def set_portal_config(
    key: str,
    payload: PortalSettingUpdate,
    auth: AuthContext = Depends(require_permission('superadmin.access')),
    db: Session = Depends(get_db),
):
    """Administrator: create or update a single portal-configuration key (billing
    defaults, feature toggles, etc.) — condo-wide, per organization."""
    row = db.query(CondoPortalSetting).filter(
        CondoPortalSetting.organization_id == auth.organization_id,
        CondoPortalSetting.setting_key == key,
    ).first()
    if row is None:
        row = CondoPortalSetting(
            organization_id=auth.organization_id,
            setting_key=key,
            setting_value=payload.setting_value,
            created_by=auth.user_id,
            updated_by=auth.user_id,
        )
        db.add(row)
    else:
        row.setting_value = payload.setting_value
        row.updated_by = auth.user_id
    db.commit()
    db.refresh(row)
    return {'data': PortalSettingOut.model_validate(row).model_dump()}
