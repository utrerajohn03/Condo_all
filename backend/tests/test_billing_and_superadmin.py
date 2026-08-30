"""
Automated tests for the additions made on top of the original vertical slice:
  - The Unit Owner role (5th user type) and its ownership scoping
  - Bill Management (condo_bills) — one-time/recurring charges, billing.manage RBAC
  - Payments (condo_payments) — self-pay vs. record-on-behalf, status transitions
  - The Superadmin Portal (organization settings + portal configuration)

Same two mandatory security properties as tests/test_condo_module.py are re-proven
here for the new endpoints: cross-tenant isolation and RBAC denial — since a
brand-new resource type is exactly the kind of change most likely to accidentally
skip one of those checks.

Run with: pytest tests/ -v
Requires a running PostgreSQL instance reachable via DATABASE_URL / .env — this
suite creates its own throwaway schema/data and does not depend on manual seeding.
"""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models._local_stub_platform_tables import LocalStubOrganization, LocalStubUser
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.models.condo_bills import CondoBill
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture(scope="module")
def db_setup():
    """Two fully isolated organizations (A and B), each with an admin, manager,
    staff, resident (tenant), and unit owner — plus a shared unit 101 owned by the
    org's Unit Owner and tenanted by its Resident, with one pending bill."""
    Base.metadata.create_all(engine)
    db = SessionLocal()

    def make_org(name):
        org = LocalStubOrganization(id=uuid.uuid4(), name=name)
        db.add(org)
        db.commit()

        def make_user(role, full_name):
            u = LocalStubUser(id=uuid.uuid4(), organization_id=org.id, full_name=full_name,
                               email=f"{role}-{org.id}@test.local", password_hash=hash_password("Password123!"),
                               role=role)
            db.add(u)
            return u

        admin = make_user("admin", "Admin")
        manager = make_user("manager", "Manager")
        staff = make_user("staff", "Staff")
        resident = make_user("resident", "Resident")
        unit_owner = make_user("unit_owner", "Unit Owner")
        db.commit()

        unit = CondoUnit(id=uuid.uuid4(), organization_id=org.id, unit_number="101",
                          building="Tower A", floor=1, status="occupied", created_by=admin.id)
        db.add(unit)
        db.commit()

        owner_link = CondoUnitResident(id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                                        user_id=unit_owner.id, relationship_type="owner",
                                        is_primary_contact=True, moved_in_at=datetime.utcnow())
        tenant_link = CondoUnitResident(id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                                         user_id=resident.id, relationship_type="tenant",
                                         is_primary_contact=False, moved_in_at=datetime.utcnow())
        db.add_all([owner_link, tenant_link])
        db.commit()

        bill = CondoBill(id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                          bill_type="association_dues", description="Monthly dues", amount=2500.00,
                          billing_cycle="monthly", is_recurring_template=True,
                          due_date=date.today() + timedelta(days=10), status="pending", amount_paid=0,
                          created_by=admin.id, updated_by=admin.id)
        db.add(bill)
        db.commit()

        return {"org": org, "admin": admin, "manager": manager, "staff": staff,
                "resident": resident, "unit_owner": unit_owner, "unit": unit, "bill": bill}

    org_a = make_org(f"Bills Test Org A {uuid.uuid4()}")
    org_b = make_org(f"Bills Test Org B {uuid.uuid4()}")

    yield {"org_a": org_a, "org_b": org_b}
    db.close()


def _login(email):
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200
    return resp.json()["token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# Unit Owner role: ownership scoping (own units/bills only, never org-wide)
# ======================================================================
def test_unit_owner_sees_only_own_unit(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)

    resp = client.get("/api/condo/units", headers=_auth_headers(token))
    assert resp.status_code == 200
    unit_ids = {u["id"] for u in resp.json()["data"]}
    assert unit_ids == {str(org_a["unit"].id)}


def test_unit_owner_bills_mine_scoped_to_own_unit(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)

    resp = client.get("/api/condo/bills/mine", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(org_a["bill"].id)


def test_resident_tenant_sees_same_shared_unit_bill(db_setup):
    """Resident (tenant) and Unit Owner are linked to the same physical unit — both
    should see the same bill on that unit via /bills/mine."""
    org_a = db_setup["org_a"]
    token = _login(org_a["resident"].email)

    resp = client.get("/api/condo/bills/mine", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(org_a["bill"].id)


# ======================================================================
# Bill Management RBAC: only billing.manage (Manager/Administrator) may write
# ======================================================================
def test_resident_cannot_create_bill(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["resident"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "other", "description": "hack",
        "amount": 10, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    assert resp.status_code == 403


def test_unit_owner_cannot_create_bill(db_setup):
    """Unit Owner gets billing.view/payment.record, never billing.manage — owning a
    unit does not grant the ability to bill oneself or anyone else."""
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "other", "description": "hack",
        "amount": 10, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    assert resp.status_code == 403


def test_staff_cannot_create_bill(db_setup):
    """Staff has billing.view + payment.record (can record a payment) but not
    billing.manage — matches RBAC_MATRIX.md."""
    org_a = db_setup["org_a"]
    token = _login(org_a["staff"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "other", "description": "hack",
        "amount": 10, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    assert resp.status_code == 403


def test_manager_can_create_and_void_bill(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["manager"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "utility", "description": "Water bill",
        "amount": 300, "billing_cycle": "one_time", "due_date": str(date.today() + timedelta(days=7)),
    })
    assert resp.status_code == 201
    bill_id = resp.json()["data"]["id"]

    resp = client.patch(f"/api/condo/bills/{bill_id}", headers=_auth_headers(token), json={"status": "void"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "void"


def test_manager_cannot_create_bill_for_other_orgs_unit(db_setup):
    """Cross-tenant isolation for bills: a Manager in Org A must not be able to bill
    a unit that belongs to Org B, even by guessing/reusing a valid unit id."""
    org_a = db_setup["org_a"]
    org_b = db_setup["org_b"]
    token = _login(org_a["manager"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(token), json={
        "unit_id": str(org_b["unit"].id), "bill_type": "other", "description": "cross-tenant attempt",
        "amount": 10, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    assert resp.status_code == 404


# ======================================================================
# Cross-tenant isolation for bills/payments (mandatory-style test, new resource)
# ======================================================================
def test_org_b_cannot_view_org_a_bill(db_setup):
    org_a = db_setup["org_a"]
    org_b = db_setup["org_b"]
    token = _login(org_b["admin"].email)

    resp = client.get("/api/condo/bills", headers=_auth_headers(token))
    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()["data"]}
    assert str(org_a["bill"].id) not in ids


def test_org_b_unit_owner_cannot_pay_org_a_bill(db_setup):
    org_a = db_setup["org_a"]
    org_b = db_setup["org_b"]
    token = _login(org_b["unit_owner"].email)

    resp = client.post("/api/condo/payments", headers=_auth_headers(token), json={
        "bill_id": str(org_a["bill"].id), "amount": 2500, "method": "online",
    })
    assert resp.status_code == 404


# ======================================================================
# Payments: self-pay mass-assignment guard, record-on-behalf, status transitions
# ======================================================================
def test_unit_owner_can_pay_own_bill_and_status_flips_to_paid(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)

    resp = client.post("/api/condo/payments", headers=_auth_headers(token), json={
        "bill_id": str(org_a["bill"].id), "amount": 2500.00, "method": "online",
    })
    assert resp.status_code == 201
    payment = resp.json()["data"]
    # Mass-assignment guard: paid_by is forced to the caller, not trusted from the body.
    assert payment["paid_by"] == str(org_a["unit_owner"].id)

    resp = client.get("/api/condo/bills/mine", headers=_auth_headers(token))
    updated = [b for b in resp.json()["data"] if b["id"] == str(org_a["bill"].id)][0]
    assert updated["status"] == "paid"


def test_cannot_pay_an_already_paid_bill_again(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)

    resp = client.post("/api/condo/payments", headers=_auth_headers(token), json={
        "bill_id": str(org_a["bill"].id), "amount": 1, "method": "cash",
    })
    assert resp.status_code == 409


def test_resident_cannot_record_payment_on_behalf_of_another_user(db_setup):
    """A Resident/Unit Owner's own id always wins for paid_by, even if they try to
    set someone else's id in the request body (mirrors MaintenanceRequestCreate)."""
    org_a = db_setup["org_a"]
    manager_token = _login(org_a["manager"].email)
    resident_token = _login(org_a["resident"].email)

    # Fresh bill so it isn't already paid/void from a prior test.
    resp = client.post("/api/condo/bills", headers=_auth_headers(manager_token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "other", "description": "Spoof-target bill",
        "amount": 100, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    bill_id = resp.json()["data"]["id"]

    resp = client.post("/api/condo/payments", headers=_auth_headers(resident_token), json={
        "bill_id": bill_id, "amount": 100, "method": "cash",
        "paid_by": str(org_a["admin"].id),  # attempted spoof
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["paid_by"] == str(org_a["resident"].id)


def test_staff_can_record_payment_on_behalf_of_resident(db_setup):
    org_a = db_setup["org_a"]
    manager_token = _login(org_a["manager"].email)
    staff_token = _login(org_a["staff"].email)

    resp = client.post("/api/condo/bills", headers=_auth_headers(manager_token), json={
        "unit_id": str(org_a["unit"].id), "bill_type": "utility", "description": "Cash-at-front-desk bill",
        "amount": 500, "billing_cycle": "one_time", "due_date": str(date.today()),
    })
    bill_id = resp.json()["data"]["id"]

    resp = client.post("/api/condo/payments", headers=_auth_headers(staff_token), json={
        "bill_id": bill_id, "amount": 200, "method": "cash", "paid_by": str(org_a["resident"].id),
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["paid_by"] == str(org_a["resident"].id)

    resp = client.get(f"/api/condo/bills?unit_id={org_a['unit'].id}", headers=_auth_headers(manager_token))
    updated = [b for b in resp.json()["data"] if b["id"] == bill_id][0]
    assert updated["status"] == "partially_paid"
    assert updated["amount_paid"] == 200.0


# ======================================================================
# Superadmin Portal: superadmin.access is Administrator-only
# ======================================================================
def test_manager_cannot_access_superadmin(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["manager"].email)
    resp = client.get("/api/superadmin/overview", headers=_auth_headers(token))
    assert resp.status_code == 403


def test_unit_owner_cannot_access_superadmin(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["unit_owner"].email)
    resp = client.get("/api/superadmin/overview", headers=_auth_headers(token))
    assert resp.status_code == 403


def test_admin_can_view_and_update_organization(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["admin"].email)

    resp = client.get("/api/superadmin/organization", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == str(org_a["org"].id)

    new_name = f"Renamed {uuid.uuid4()}"
    resp = client.patch("/api/superadmin/organization", headers=_auth_headers(token), json={"name": new_name})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == new_name


def test_admin_cannot_update_other_orgs_settings(db_setup):
    """An Administrator's token only ever carries their own org id — there is no
    org_id parameter anywhere on this endpoint for them to override."""
    org_a = db_setup["org_a"]
    org_b = db_setup["org_b"]
    token_a = _login(org_a["admin"].email)

    original_b_name = org_b["org"].name
    client.patch("/api/superadmin/organization", headers=_auth_headers(token_a), json={"name": "Hijacked"})

    token_b = _login(org_b["admin"].email)
    resp = client.get("/api/superadmin/organization", headers=_auth_headers(token_b))
    assert resp.json()["data"]["name"] == original_b_name


def test_portal_config_defaults_then_override(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["admin"].email)

    resp = client.get("/api/superadmin/portal-config", headers=_auth_headers(token))
    assert resp.status_code == 200
    keys = {row["setting_key"] for row in resp.json()["data"]}
    assert "currency" in keys and "enable_online_payments" in keys

    resp = client.put("/api/superadmin/portal-config/late_fee_percent",
                       headers=_auth_headers(token), json={"setting_value": "3.5"})
    assert resp.status_code == 200
    assert resp.json()["data"]["setting_value"] == "3.5"

    resp = client.get("/api/superadmin/portal-config", headers=_auth_headers(token))
    row = [r for r in resp.json()["data"] if r["setting_key"] == "late_fee_percent"][0]
    assert row["setting_value"] == "3.5"


def test_staff_cannot_write_portal_config(db_setup):
    org_a = db_setup["org_a"]
    token = _login(org_a["staff"].email)
    resp = client.put("/api/superadmin/portal-config/late_fee_percent",
                       headers=_auth_headers(token), json={"setting_value": "99"})
    assert resp.status_code == 403
