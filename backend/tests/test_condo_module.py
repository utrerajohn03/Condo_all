"""
Automated tests for the Condominium Management Module.

Includes the two MANDATORY security tests from the assessment:
  1. Cross-Tenant Isolation Test
  2. RBAC Denial Test

Run with: pytest tests/ -v
Requires a running PostgreSQL instance reachable via DATABASE_URL / .env — this suite creates
its own throwaway schema/data via the seed helpers below and does not depend on manual seeding.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models._local_stub_platform_tables import LocalStubOrganization, LocalStubUser
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture(scope="module")
def db_setup():
    """Creates two fully isolated organizations (A and B) each with their own admin,
    resident, staff, unit, and resident-unit link, for cross-tenant testing."""
    Base.metadata.create_all(engine)
    db = SessionLocal()

    def make_org(name):
        org = LocalStubOrganization(id=uuid.uuid4(), name=name)
        db.add(org)
        db.commit()

        admin = LocalStubUser(id=uuid.uuid4(), organization_id=org.id, full_name="Admin",
                               email=f"admin-{org.id}@test.local", password_hash=hash_password("Password123!"),
                               role="admin")
        resident = LocalStubUser(id=uuid.uuid4(), organization_id=org.id, full_name="Resident",
                                  email=f"resident-{org.id}@test.local", password_hash=hash_password("Password123!"),
                                  role="resident")
        staff = LocalStubUser(id=uuid.uuid4(), organization_id=org.id, full_name="Staff",
                               email=f"staff-{org.id}@test.local", password_hash=hash_password("Password123!"),
                               role="staff")
        manager = LocalStubUser(id=uuid.uuid4(), organization_id=org.id, full_name="Manager",
                                 email=f"manager-{org.id}@test.local", password_hash=hash_password("Password123!"),
                                 role="manager")
        db.add_all([admin, resident, staff, manager])
        db.commit()

        unit = CondoUnit(id=uuid.uuid4(), organization_id=org.id, unit_number="101",
                          building="Tower A", floor=1, status="occupied", created_by=admin.id)
        db.add(unit)
        db.commit()

        link = CondoUnitResident(id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                                  user_id=resident.id, relationship_type="owner",
                                  is_primary_contact=True, moved_in_at=__import__("datetime").datetime.utcnow())
        db.add(link)
        db.commit()

        return {"org": org, "admin": admin, "resident": resident, "staff": staff, "manager": manager, "unit": unit}

    org_a = make_org(f"Test Org A {uuid.uuid4()}")
    org_b = make_org(f"Test Org B {uuid.uuid4()}")

    yield {"org_a": org_a, "org_b": org_b}
    db.close()


def _login(email):
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200
    return resp.json()["token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# MANDATORY TEST 1: Cross-Tenant Isolation Test
# ======================================================================
def test_cross_tenant_isolation(db_setup):
    """
    Create data belonging to Organization A. Attempt to access it as a user from
    Organization B. Prove that Organization B cannot view, update, or delete
    Organization A's record.
    """
    org_a = db_setup["org_a"]
    org_b = db_setup["org_b"]

    token_a_resident = _login(org_a["resident"].email)
    token_b_admin = _login(org_b["admin"].email)

    # Org A resident creates a maintenance request
    create_resp = client.post(
        "/api/condo/maintenance-requests",
        headers=_auth_headers(token_a_resident),
        json={"unit_id": str(org_a["unit"].id), "category": "plumbing",
              "description": "Org A's private leaking faucet issue.", "priority": "medium"},
    )
    assert create_resp.status_code == 201
    request_id = create_resp.json()["data"]["id"]

    # Org B admin tries to VIEW it -> must be 404, not 200 and not 403 (existence never leaked)
    detail_resp = client.get(
        f"/api/condo/maintenance-requests/detail?id={request_id}",
        headers=_auth_headers(token_b_admin),
    )
    assert detail_resp.status_code == 404

    # Org B admin's list must NOT contain Org A's request
    list_resp = client.get("/api/condo/maintenance-requests", headers=_auth_headers(token_b_admin))
    assert list_resp.status_code == 200
    returned_ids = [item["id"] for item in list_resp.json()["data"]]
    assert request_id not in returned_ids

    # Org B admin tries to UPDATE Org A's request -> must be 404
    update_resp = client.post(
        f"/api/condo/maintenance-requests/status?id={request_id}",
        headers=_auth_headers(token_b_admin),
        json={"status": "cancelled"},
    )
    assert update_resp.status_code == 404

    # Org B admin tries to DELETE Org A's request -> must be 404
    delete_resp = client.delete(
        f"/api/condo/maintenance-requests/{request_id}",
        headers=_auth_headers(token_b_admin),
    )
    assert delete_resp.status_code == 404

    # Confirm Org A can still see their own request (isolation isn't accidentally blocking them too)
    own_detail_resp = client.get(
        f"/api/condo/maintenance-requests/detail?id={request_id}",
        headers=_auth_headers(_login(org_a["admin"].email)),
    )
    assert own_detail_resp.status_code == 200


# ======================================================================
# MANDATORY TEST 2: RBAC Denial Test
# ======================================================================
def test_rbac_denial_resident_cannot_assign(db_setup):
    """
    Attempt a write operation using a role that only has viewing permission.
    Prove that the endpoint returns 403 Forbidden.
    """
    org_a = db_setup["org_a"]
    token_resident = _login(org_a["resident"].email)

    # Residents do not hold maintenance.assign — this must return 403, not 200/404/500
    resp = client.post(
        f"/api/condo/maintenance-requests/assign?id={uuid.uuid4()}",
        headers=_auth_headers(token_resident),
        json={"assigned_to": str(uuid.uuid4())},
    )
    assert resp.status_code == 403
    assert "maintenance.assign" in resp.json()["detail"]


def test_rbac_denial_staff_cannot_delete(db_setup):
    """Staff role holds no maintenance.delete permission — must be 403."""
    org_a = db_setup["org_a"]
    token_staff = _login(org_a["staff"].email)

    resp = client.delete(
        f"/api/condo/maintenance-requests/{uuid.uuid4()}",
        headers=_auth_headers(token_staff),
    )
    assert resp.status_code == 403


# ======================================================================
# Core workflow tests
# ======================================================================
def test_resident_can_only_submit_for_own_linked_unit(db_setup):
    org_a = db_setup["org_a"]
    token_resident = _login(org_a["resident"].email)

    # Make an unlinked unit in the same org
    db = SessionLocal()
    other_unit = CondoUnit(id=uuid.uuid4(), organization_id=org_a["org"].id, unit_number="999",
                            building="Tower Z", floor=9, status="vacant")
    db.add(other_unit)
    db.commit()
    other_unit_id = other_unit.id
    db.close()

    resp = client.post(
        "/api/condo/maintenance-requests",
        headers=_auth_headers(token_resident),
        json={"unit_id": str(other_unit_id), "description": "Trying to submit for a unit I don't live in."},
    )
    assert resp.status_code == 403


def test_full_lifecycle_and_terminal_state_block(db_setup):
    org_a = db_setup["org_a"]
    token_resident = _login(org_a["resident"].email)
    token_staff = _login(org_a["staff"].email)

    create_resp = client.post(
        "/api/condo/maintenance-requests",
        headers=_auth_headers(token_resident),
        json={"unit_id": str(org_a["unit"].id), "description": "Lifecycle test issue description."},
    )
    request_id = create_resp.json()["data"]["id"]

    assign_resp = client.post(
        f"/api/condo/maintenance-requests/assign?id={request_id}",
        headers=_auth_headers(token_staff),
        json={"assigned_to": str(org_a["staff"].id)},
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["data"]["status"] == "assigned"

    # Double-assign should fail with 409 (not in submitted status anymore)
    double_assign = client.post(
        f"/api/condo/maintenance-requests/assign?id={request_id}",
        headers=_auth_headers(token_staff),
        json={"assigned_to": str(org_a["staff"].id)},
    )
    assert double_assign.status_code == 409

    complete_resp = client.post(
        f"/api/condo/maintenance-requests/status?id={request_id}",
        headers=_auth_headers(token_staff),
        json={"status": "in_progress"},
    )
    assert complete_resp.status_code == 200

    complete_resp2 = client.post(
        f"/api/condo/maintenance-requests/status?id={request_id}",
        headers=_auth_headers(token_staff),
        json={"status": "completed"},
    )
    assert complete_resp2.status_code == 200

    # Terminal state — any further transition must be blocked with 409
    blocked_resp = client.post(
        f"/api/condo/maintenance-requests/status?id={request_id}",
        headers=_auth_headers(token_staff),
        json={"status": "cancelled"},
    )
    assert blocked_resp.status_code == 409


def test_validation_description_too_short(db_setup):
    org_a = db_setup["org_a"]
    token_resident = _login(org_a["resident"].email)

    resp = client.post(
        "/api/condo/maintenance-requests",
        headers=_auth_headers(token_resident),
        json={"unit_id": str(org_a["unit"].id), "description": "short"},
    )
    assert resp.status_code == 422


def test_no_token_returns_401():
    resp = client.get("/api/condo/maintenance-requests")
    assert resp.status_code == 401


# ======================================================================
# Manage Users (Administrator) — added per the panel's role-spec update
# ======================================================================
def test_manage_users_rbac(db_setup):
    org_a = db_setup["org_a"]
    token_admin = _login(org_a["admin"].email)
    token_staff = _login(org_a["staff"].email)
    token_manager = _login(org_a["manager"].email)
    token_resident = _login(org_a["resident"].email)

    # Resident must NOT view other users at all.
    resp = client.get("/api/condo/users", headers=_auth_headers(token_resident))
    assert resp.status_code == 403

    # Staff/Manager CAN view users ("View residents") but cannot manage them.
    resp = client.get("/api/condo/users", headers=_auth_headers(token_staff))
    assert resp.status_code == 200

    resp = client.post(
        "/api/condo/users", headers=_auth_headers(token_manager),
        json={"email": f"blocked-{uuid.uuid4()}@test.local", "full_name": "X",
              "password": "password123", "role": "resident"},
    )
    assert resp.status_code == 403

    # Administrator: full CRUD works, including deactivate -> blocked login.
    create_resp = client.post(
        "/api/condo/users", headers=_auth_headers(token_admin),
        json={"email": f"newuser-{uuid.uuid4()}@test.local", "full_name": "New Staffer",
              "password": "password123", "role": "staff"},
    )
    assert create_resp.status_code == 201
    new_user = create_resp.json()["data"]

    deactivate_resp = client.post(
        f"/api/condo/users/{new_user['id']}/deactivate", headers=_auth_headers(token_admin)
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["data"]["is_active"] is False

    login_resp = client.post("/api/auth/login", json={"email": new_user["email"], "password": "password123"})
    assert login_resp.status_code == 401  # deactivated account cannot log in

    delete_resp = client.delete(f"/api/condo/users/{new_user['id']}", headers=_auth_headers(token_admin))
    assert delete_resp.status_code == 200

    # Administrator cannot delete their own account.
    my_id = client.get("/api/condo/users/me", headers=_auth_headers(token_admin)).json()["data"]["id"]
    self_delete_resp = client.delete(f"/api/condo/users/{my_id}", headers=_auth_headers(token_admin))
    assert self_delete_resp.status_code == 400


def test_resident_own_profile_and_unit_only(db_setup):
    """Resident: "View their own profile" / "View their assigned unit" — own data
    only, and the org-wide unit list must be scoped to just their own linkage."""
    org_a = db_setup["org_a"]
    token_resident = _login(org_a["resident"].email)

    profile_resp = client.get("/api/condo/users/me", headers=_auth_headers(token_resident))
    assert profile_resp.status_code == 200
    assert profile_resp.json()["data"]["email"] == org_a["resident"].email

    mine_resp = client.get("/api/condo/units/mine", headers=_auth_headers(token_resident))
    assert mine_resp.status_code == 200
    mine_ids = [u["id"] for u in mine_resp.json()["data"]]
    assert str(org_a["unit"].id) in mine_ids

    # GET /api/condo/units (the org-wide list) must ALSO be scoped for a Resident —
    # they may not see other units even via this endpoint.
    list_resp = client.get("/api/condo/units", headers=_auth_headers(token_resident))
    assert list_resp.status_code == 200
    listed_ids = [u["id"] for u in list_resp.json()["data"]]
    assert listed_ids == mine_ids


# ======================================================================
# Resident Assignments (Staff: view only; Manager/Administrator: manage)
# ======================================================================
def test_resident_assignments_rbac(db_setup):
    org_a = db_setup["org_a"]
    token_staff = _login(org_a["staff"].email)
    token_manager = _login(org_a["manager"].email)
    token_resident = _login(org_a["resident"].email)

    # Resident must not view assignments at all.
    resp = client.get("/api/condo/unit-residents", headers=_auth_headers(token_resident))
    assert resp.status_code == 403

    # Staff can VIEW but not MANAGE.
    resp = client.get("/api/condo/unit-residents", headers=_auth_headers(token_staff))
    assert resp.status_code == 200

    resp = client.post(
        "/api/condo/unit-residents", headers=_auth_headers(token_staff),
        json={"unit_id": str(org_a["unit"].id), "user_id": str(org_a["resident"].id),
              "relationship_type": "co_resident"},
    )
    assert resp.status_code == 403

    # Manager CAN manage — but a second primary contact on the same (already-primary)
    # unit must be rejected with 409.
    resp = client.post(
        "/api/condo/unit-residents", headers=_auth_headers(token_manager),
        json={"unit_id": str(org_a["unit"].id), "user_id": str(org_a["resident"].id),
              "relationship_type": "co_resident", "is_primary_contact": True},
    )
    assert resp.status_code == 409


# ======================================================================
# Front Desk Staff: "Create a maintenance request on behalf of a resident"
# ======================================================================
def test_staff_creates_request_on_behalf_of_resident(db_setup):
    org_a = db_setup["org_a"]
    token_staff = _login(org_a["staff"].email)

    resp = client.post(
        "/api/condo/maintenance-requests", headers=_auth_headers(token_staff),
        json={"unit_id": str(org_a["unit"].id), "description": "Reported at the front desk by the resident.",
              "priority": "low", "requested_by": str(org_a["resident"].id)},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["requested_by"] == str(org_a["resident"].id)
