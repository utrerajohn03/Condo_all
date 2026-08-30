"""
Pydantic v2 schemas for request validation and response shaping.
Matches docs/API_CONTRACT.md exactly.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

VALID_PRIORITIES = {'low', 'medium', 'high', 'urgent'}


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str


class MaintenanceRequestCreate(BaseModel):
    """
    Only these fields are ever read from the client. Anything else sent
    (organization_id, status, created_by, etc.) is silently ignored —
    never trusted, per docs/THREAT_MODEL.md (mass assignment).

    `requested_by` is the one exception: it is accepted from the body, but ONLY
    honored when the caller is Staff/Manager/Administrator submitting "on behalf of"
    a resident (see docs/RBAC_MATRIX.md, Front Desk Staff). If the caller is a
    Resident, this field is always ignored server-side and requested_by is forced to
    the caller's own id — the mass-assignment guard for residents is unchanged.
    """
    unit_id: UUID
    category: Optional[str] = Field(default=None, max_length=30)
    description: str = Field(min_length=10, max_length=2000)
    priority: str = Field(default='medium')
    requested_by: Optional[UUID] = None

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(f'priority must be one of {sorted(VALID_PRIORITIES)}')
        return v


class MaintenanceRequestListItem(BaseModel):
    id: UUID
    status: str
    priority: str
    category: Optional[str]
    unit_number: str
    assigned_to: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class MaintenanceRequestDetail(BaseModel):
    id: UUID
    organization_id: UUID
    unit_id: UUID
    requested_by: UUID
    assigned_to: Optional[UUID]
    category: Optional[str]
    description: str
    priority: str
    status: str
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignRequestBody(BaseModel):
    assigned_to: UUID


class StatusUpdateBody(BaseModel):
    status: str
    reason: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {'assigned', 'in_progress', 'completed', 'cancelled', 'rejected'}
        if v not in allowed:
            raise ValueError(f'status must be one of {sorted(allowed)}')
        return v


class UnitCreate(BaseModel):
    unit_number: str = Field(max_length=20)
    building: Optional[str] = Field(default=None, max_length=50)
    floor: Optional[int] = None
    status: str = Field(default='vacant')

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {'occupied', 'vacant', 'under_maintenance'}
        if v not in allowed:
            raise ValueError(f'status must be one of {sorted(allowed)}')
        return v


class UnitListItem(BaseModel):
    id: UUID
    unit_number: str
    building: Optional[str]
    floor: Optional[int]
    status: str

    class Config:
        from_attributes = True


class UnitUpdate(BaseModel):
    """Partial update — only fields the caller sends are changed."""
    unit_number: Optional[str] = Field(default=None, max_length=20)
    building: Optional[str] = Field(default=None, max_length=50)
    floor: Optional[int] = None
    status: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {'occupied', 'vacant', 'under_maintenance'}
        if v not in allowed:
            raise ValueError(f'status must be one of {sorted(allowed)}')
        return v


# ── Users (Manage Users) ──
# LOCAL SANDBOX STAND-IN ONLY. In real ARGO, users/organizations are platform-owned —
# this module never manages accounts there (see Onboarding Contract, Part B §4: "FK to
# users — never"). These endpoints exist only so "Administrator manages users" is
# demonstrable standalone, exactly like the condo_zzz_local_stub migration and
# POST /api/auth/login. Not part of what's handed over at integration.

VALID_USER_ROLES = {'resident', 'unit_owner', 'staff', 'manager', 'admin'}


class UserProfileOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    organization_id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(default='resident')

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_USER_ROLES:
            raise ValueError(f'role must be one of {sorted(VALID_USER_ROLES)}')
        return v


class UserUpdate(BaseModel):
    """Partial update — only fields the caller sends are changed. Password is optional
    (omit to leave unchanged); organization_id/id are never editable via this endpoint."""
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=255)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in VALID_USER_ROLES:
            raise ValueError(f'role must be one of {sorted(VALID_USER_ROLES)}')
        return v


# ── Resident Assignments (unit <-> user linkage) ──

VALID_RELATIONSHIP_TYPES = {'owner', 'tenant', 'co_resident'}


class UnitResidentCreate(BaseModel):
    unit_id: UUID
    user_id: UUID
    relationship_type: str = Field(default='tenant')
    is_primary_contact: bool = False
    moved_in_at: Optional[datetime] = None  # defaults to now() if omitted

    @field_validator('relationship_type')
    @classmethod
    def validate_relationship_type(cls, v: str) -> str:
        if v not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(f'relationship_type must be one of {sorted(VALID_RELATIONSHIP_TYPES)}')
        return v


class UnitResidentListItem(BaseModel):
    id: UUID
    unit_id: UUID
    unit_number: str
    user_id: UUID
    resident_name: str
    resident_email: str
    relationship_type: str
    is_primary_contact: bool
    moved_in_at: datetime
    moved_out_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Bills (Bill Management) ──
# Association dues, utility charges, or a one-off charge, billed to a unit. Both
# recurring (billing_cycle != 'one_time') and one-time bills are supported —
# see docs/SCOPING.md and app/models/condo_bills.py.

VALID_BILL_TYPES = {'association_dues', 'utility', 'other'}
VALID_BILLING_CYCLES = {'one_time', 'monthly', 'quarterly', 'annual'}
VALID_BILL_STATUSES = {'pending', 'partially_paid', 'paid', 'overdue', 'void'}


class BillCreate(BaseModel):
    unit_id: UUID
    bill_type: str
    description: str = Field(min_length=1, max_length=500)
    amount: float = Field(gt=0)
    billing_cycle: str = Field(default='one_time')
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    due_date: date

    @field_validator('bill_type')
    @classmethod
    def validate_bill_type(cls, v: str) -> str:
        if v not in VALID_BILL_TYPES:
            raise ValueError(f'bill_type must be one of {sorted(VALID_BILL_TYPES)}')
        return v

    @field_validator('billing_cycle')
    @classmethod
    def validate_billing_cycle(cls, v: str) -> str:
        if v not in VALID_BILLING_CYCLES:
            raise ValueError(f'billing_cycle must be one of {sorted(VALID_BILLING_CYCLES)}')
        return v


class BillUpdate(BaseModel):
    """Partial update — only fields the caller sends are changed. Property Manager /
    Administrator only (billing.manage)."""
    description: Optional[str] = Field(default=None, max_length=500)
    amount: Optional[float] = Field(default=None, gt=0)
    due_date: Optional[date] = None
    status: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in VALID_BILL_STATUSES:
            raise ValueError(f'status must be one of {sorted(VALID_BILL_STATUSES)}')
        return v


class BillListItem(BaseModel):
    id: UUID
    unit_id: UUID
    unit_number: str
    bill_type: str
    description: str
    amount: float
    amount_paid: float
    billing_cycle: str
    period_start: Optional[date]
    period_end: Optional[date]
    due_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Payments ──
# A payment applied against a bill — either self-service (Resident/Unit Owner paying
# their own bill) or recorded on their behalf by Staff/Manager/Administrator.

VALID_PAYMENT_METHODS = {'cash', 'bank_transfer', 'online', 'check'}


class PaymentCreate(BaseModel):
    bill_id: UUID
    amount: float = Field(gt=0)
    method: str = Field(default='online')
    reference_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    # Only honored when the caller is Staff/Manager/Administrator recording a payment
    # on behalf of a resident/unit owner (mirrors MaintenanceRequestCreate.requested_by).
    # A Resident/Unit Owner calling this endpoint always pays as themselves — this
    # field is silently ignored for them, per the same mass-assignment guard used
    # throughout this module.
    paid_by: Optional[UUID] = None

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f'method must be one of {sorted(VALID_PAYMENT_METHODS)}')
        return v


class PaymentListItem(BaseModel):
    id: UUID
    bill_id: UUID
    unit_id: UUID
    unit_number: str
    paid_by: UUID
    amount: float
    method: str
    reference_number: Optional[str]
    status: str
    paid_at: datetime

    class Config:
        from_attributes = True


# ── Superadmin Portal ──
# Condo-wide settings, users, billing, and portal configuration. Administrator only
# (superadmin.access). User management reuses the existing /api/condo/users
# endpoints — the Superadmin Portal is a frontend surface that aggregates them
# alongside organization-wide settings, not a separate account store.

class OrganizationOut(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class PortalSettingUpdate(BaseModel):
    setting_value: str = Field(max_length=2000)


class PortalSettingOut(BaseModel):
    setting_key: str
    setting_value: str

    class Config:
        from_attributes = True


class SuperadminOverview(BaseModel):
    total_units: int
    total_users: int
    active_users: int
    total_bills_outstanding: float
    total_collected: float
    pending_maintenance_requests: int
