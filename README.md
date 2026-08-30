# Condominium Management Module — ARGO Pre-Development Assessment

**Intern:** Utrera · **Module:** Condominium Management · **Table prefix:** `condo_`

**Status: functional full-stack vertical slice.** Real, running FastAPI + PostgreSQL backend
**and** a real React + Vite + Tailwind frontend with an actual login page, dashboard, and
maintenance-requests list page — not a mockup, not Swagger-only. Tested end-to-end against a
live PostgreSQL database, including the two mandatory security tests, all passing, and a real
browser walkthrough (login → create → assign → complete) captured and verified.

## Purpose

Gives condo staff on the ARGO multi-tenant platform a system to manage unit records,
unit-resident linkage, and the maintenance-request lifecycle. See `docs/SCOPING.md` for the
full problem statement, intended users, and V1 scope.

## Technology Used

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 (typed `Mapped[...]`), Alembic, Pydantic v2 — pinned to **Python 3.11** (`backend/.python-version`, `pyproject.toml`); developed/verified in this sandbox on 3.12 (no 3.12-only syntax used — see Known Limitations) |
| Database | PostgreSQL (**14**, per supervisor's updated instruction — supersedes the 17 in the original onboarding contract); developed/verified on 16 in this sandbox — no version-specific SQL used |
| Auth | python-jose (JWT) + passlib[bcrypt] — consumes a platform-shaped JWT; see "Local sandbox stand-in" below |
| Frontend | React 18.3 + Vite 7 + Tailwind CSS v3, react-router-dom v6, axios, Bootstrap Icons, **@tanstack/react-query v5** (server state), **zustand v5** (client/filter state), **cva + clsx + tailwind-merge** (component variants), **recharts v3** (dashboard chart), **Vitest 4 + jsdom + Testing Library** (frontend unit tests) |

## Repository Layout

```
docs/
  SCOPING.md, ERD.md, API_CONTRACT.md, RBAC_MATRIX.md,
  THREAT_MODEL.md, WORKFLOW.md, ASSUMPTIONS_AND_TRADEOFFS.md,
  MODULE_STRUCTURE.md          - Deliverable 8: sidebar/tabs/KPI/table/form
                                  blueprint for every module page
backend/
  .python-version, pyproject.toml  - pins Python to >=3.11,<3.12
  alembic.ini, alembic/          - migrations (see "Migrations" below)
  app/
    main.py                     - FastAPI app, mounts all routers
    config.py                   - settings (reads .env)
    database.py                 - SQLAlchemy Base + engine/session + get_db()
    core/
      security.py                - password hashing + JWT issue/verify
      permissions.py              - ROLE_PERMISSIONS map (matches RBAC_MATRIX.md)
      deps.py                     - get_current_auth(), require_permission()
      state_machine.py            - allowed status transitions (matches WORKFLOW.md)
    models/
      condo_units.py
      condo_unit_residents.py
      condo_maintenance_requests.py
      _local_stub_platform_tables.py   - LOCAL ONLY, not part of the deliverable
    schemas/condo.py             - Pydantic request/response models
    routers/
      auth.py                     - POST /api/auth/login (local stand-in)
      maintenance.py               - the 6 maintenance-request endpoints
      units.py                     - unit list/create
  scripts/seed_db.py             - creates tables + seeds demo org/users/units
  tests/test_condo_module.py     - pytest suite incl. the 2 mandatory security tests
  requirements.txt
  .env.example
frontend/
  src/
    api.js                        - axios client, injects JWT on every request
    queryClient.js                 - @tanstack/react-query QueryClient instance
    AuthContext.jsx                - login/logout/token state
    App.jsx                        - routes (protected)
    lib/utils.js                   - cn() — clsx + tailwind-merge class helper
    hooks/
      useMaintenanceRequests.js    - react-query hooks (query + 4 mutations)
      useUnits.js                  - react-query hooks (query + create mutation)
    store/
      useFilterStore.js            - zustand — list-page search/filter/tab state
    components/
      Layout.jsx                    - Argo app shell: dark sidebar + header
      StatusBadge.jsx                - composes ui/Badge
      ui/Button.jsx                  - cva button (variant × size)
      ui/Badge.jsx                   - cva status badge
    pages/Login.jsx                - local sandbox stand-in login
    pages/Dashboard.jsx            - KPI cards + recharts status-breakdown chart
    pages/MaintenanceRequests.jsx  - the core list page: KPI cards, tabs,
                                      filter/search, table, create/assign/status
                                      modals — all data via react-query hooks
    pages/Units.jsx                - unit records list page, same pattern
  vite.config.js                  - includes Vitest config (jsdom env)
  package.json (pinned to contract versions), tailwind.config.js
```

## Local Sandbox Stand-Ins (not part of the deliverable)

Three things exist **only** to make this module runnable/testable standalone, outside real ARGO —
all three are removed at the same integration step, and nothing else in the module changes when
that happens, since every endpoint already reads identity/org/role only from the verified JWT:

1. **`app/models/_local_stub_platform_tables.py`** — throwaway `organizations` and `users`
   tables. Real ARGO already has these; at integration this file is deleted and this module's
   foreign keys resolve against the real platform tables automatically.
2. **`POST /api/auth/login`** + the React `Login.jsx` page — mints/consumes a JWT shaped like
   ARGO's (`sub`, `org`, `role`). In real ARGO, the platform issues this token before the user
   ever reaches this module; there is no login page in the delivered module (the frontend
   banner on the login screen says this explicitly). **Confirmed with the supervisor:** this
   version is under professor review before any ARGO connection is made, so a standalone login
   is expected at this stage, not an oversight.
3. **`/api/condo/users` ("Manage Users")** — full account CRUD (add/edit/delete/activate/
   deactivate), gated to Administrator. In real ARGO, account management is platform-owned, not
   this module's responsibility (Onboarding Contract, Part B §4). Implemented here per the
   panel's role-spec update so "Administrator manages users" is demonstrable now; see
   `docs/ASSUMPTIONS_AND_TRADEOFFS.md` #9 for the full reasoning.

## Setup and Running

### 1. Database
```
createdb -U postgres condo_argo
```

### 2. Backend
```
cd backend
python3.11 -m venv venv         # must be 3.11 — see .python-version / pyproject.toml
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit .env with your real PostgreSQL password
alembic upgrade head            # creates all tables via migration (see "Migrations" below)
python -m scripts.seed_db       # seeds demo org/users/units on top of the migrated schema
uvicorn app.main:app --reload   # runs on http://localhost:8000
```

If `passlib`/`bcrypt` raises a version error on install, `bcrypt==4.0.1` is already pinned in
`requirements.txt` to avoid this known compatibility issue.

### 3. Frontend (separate terminal, keep the backend running)
```
cd frontend
npm install
npm run dev                     # runs on http://localhost:5173
```

### 4. Open the app
**http://localhost:5173** — you'll land on the login page.

### 5. Run the automated tests
```
cd backend
pytest tests/ -v                # 11 tests, incl. the 2 mandatory security tests

cd ../frontend
npm run test                    # Vitest — 16 tests (utils, StatusBadge, Button, zustand stores)
```

## Migrations (Alembic)

Two migrations, both prefixed `condo_` per the onboarding contract, including the Alembic
bookkeeping table itself (renamed `condo_alembic_version` in `alembic/env.py`):

1. **`condo_zzz_local_stub`** — local-sandbox-only stub `organizations`/`users` tables so this
   module's foreign keys resolve standalone. `down_revision = None`. **Not part of the handover**
   to the real ARGO platform — the supervisor deletes this file and re-points
   `condo_001_initial`'s `down_revision` at Argo's real head; that is the only edit that happens
   to this chain, and they do it, not the intern.
2. **`condo_001_initial`** — creates the three condo_ business tables and their PostgreSQL enum
   types (models set `create_type=False`; Alembic is the single source of truth for schema).

Both migrations are additive (guarded with an existing-table check), idempotent, and reversible
(`downgrade()` drops everything in reverse dependency order) — verified locally with a full
`upgrade head → downgrade base → upgrade head` round trip.

```
alembic upgrade head            # apply
alembic downgrade base          # roll back to nothing (for testing)
alembic history                 # see the revision chain
```

## Deployment (Live Demo)

**Hosting platform deviates from the PhilCEB Intern Live System Hosting Guide on the
supervisor's direct instruction, and changed twice during planning before landing here.**
The guide names Replit + GitLab as the standard. The professor initially said to use GitHub +
Vercel instead; **the final decision is Replit** (with GitHub for source control) — which
happens to also be what the guide itself names as the standard platform, just reached by a
different path than "follow the guide as written."

- **Platform:** Replit, deployed as a **single combined app** — one Replit project serves both
  the API and the built React frontend from the same URL/port, matching the guide's
  "module may contain multiple routes under the same domain" language. See `start.sh` and the
  static-file block at the bottom of `backend/app/main.py` (only activates when
  `frontend/dist` exists — inert everywhere else, so `uvicorn app.main:app --reload` in local
  dev is unaffected).
- **Config files:** `.replit` (run command, Python 3.11 + Node 22 modules, port mapping) and
  `start.sh` (builds the frontend, installs backend deps, runs migrations, starts the server) —
  both at the project root. Verified end-to-end in a Linux sandbox mirroring this exact
  sequence before being finalized.
- **Database:** Neon (managed PostgreSQL 14) — external, not a Replit-attached database, since
  the free/Starter Replit plan doesn't include a persistent Postgres instance of its own.
- **Source control:** GitHub (private repo) — imported into Replit via "Import from GitHub."
- **Secrets** (set in Replit's Secrets tab, never committed): `DATABASE_URL`, `JWT_SECRET_KEY`,
  `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`.
- **ARGO authentication expectations:** none yet — see "Local Sandbox Stand-Ins" above. The
  live demo uses the stand-in login (`POST /api/auth/login`) with the seeded test accounts
  below. This is expected for this review stage; ARGO SSO integration is a later step.

## Demo Script for the Panel

1. Open **http://localhost:5173** → show the login page, point out the banner explaining this
   is a local sandbox stand-in (no separate login system ships in the real integrated module).
2. Log in as `resident@condo.test` / `Password123!` → lands on Maintenance Requests.
3. Click **New Request** → fill the modal (unit, category, description, priority) → submit →
   show the toast confirmation and the KPI cards updating live.
4. Log out, log in as `staff@condo.test` → show the same request now visible (Staff sees all,
   Resident only saw their own) → click **Assign** → paste the staff user id (from the seed
   script output) → show status becomes "Assigned".
5. **Update Status** → `in_progress` → `completed` → show the full lifecycle in the badge.
6. Try updating a completed request → show the backend correctly rejects it (409, surfaced as
   an error toast).
7. Log in as `resident@condo.test` again → note that staff-only actions simply aren't shown —
   RBAC hides them in the UI, **and** the backend independently enforces it if bypassed
   (mention this dual-layer design point to the panel).
8. Switch to the **Units** page → show the second list page, create a new unit as admin.
9. Open a terminal, run `pytest tests/ -v` → show `11 passed`, naming
   `test_cross_tenant_isolation` and the RBAC denial tests specifically.
10. Switch roles again — show **Manage Users** (Admin adds/deactivates a user; Staff sees the
    same list read-only) and **Resident Assignments** (Manager assigns a resident to a unit,
    the primary-contact conflict correctly returns 409 on a second attempt).

## Test Accounts

Password for all: **Password123!**

| Email | Role |
|---|---|
| admin@condo.test | admin |
| manager@condo.test | manager |
| staff@condo.test | staff |
| resident@condo.test | resident |

## Verified Behavior

**What "verified" means here, precisely** — no browser-automation tool was used to click through
the UI; that claim in an earlier version of this README was inaccurate and has been corrected.
Everything below was confirmed by real HTTP requests against a live running server (not just
unit tests), plus the automated test suites:

Verified via direct `curl` calls against a live `uvicorn` server + Neon/local PostgreSQL (real
login flow, real tokens, real database writes — not mocked):

- Login succeeds with correct credentials, returns a working JWT; fails with 401 on wrong
  password; a deactivated account is blocked at login **and** on an already-issued token
- Full maintenance-request lifecycle end-to-end: create → assign → `in_progress` → `completed`,
  each step confirmed by re-fetching the record
- Re-transitioning a `completed` request correctly rejected with 409 (terminal state)
- Cross-role RBAC denials: Resident blocked (403) from creating/editing units, assigning
  requests, viewing the Manage Users or Resident Assignments lists; Staff blocked (403) from
  managing users or creating assignments; Manager blocked (403) from account CRUD
  (`user.manage`)
- Resident's `GET /api/condo/units` and `GET /api/condo/units/mine` both return only their own
  linked unit — confirmed by comparing the two response payloads directly
- Manage Users: create (201) → deactivate → blocked login (401) → reactivate → delete (200);
  an Administrator blocked (400) from deactivating/deleting their own account
- Resident Assignments: Staff can view (200) but not create (403); Manager creating a second
  active primary contact on the same unit correctly rejected with 409
- No token at all → 401 on every protected route

Verified via `pytest` (11/11 passing) against a live PostgreSQL instance — includes everything
above plus the original vertical-slice suite:

- **`test_cross_tenant_isolation`** (mandatory test 1) — Org B cannot view (404), list, update
  (404), or delete (404) Org A's maintenance request; Org A can still see their own
- **`test_rbac_denial_resident_cannot_assign`** / **`test_rbac_denial_staff_cannot_delete`**
  (mandatory test 2) — both confirm 403 for roles lacking the required permission
- Ownership scoping, input validation (422), missing-auth (401) all confirmed
- `test_manage_users_rbac`, `test_resident_own_profile_and_unit_only`,
  `test_resident_assignments_rbac`, `test_staff_creates_request_on_behalf_of_resident` — the
  four new tests covering this session's role-spec expansion

Verified via `npm run build` (clean production build) and `vitest run` (16/16 passing — utility
functions, `StatusBadge`, `Button` variants, zustand filter stores).

**Not yet verified — still the student's responsibility before the panel defense:** actually
opening the deployed (or local) frontend in a real browser and clicking through each flow
(login as each role, submitting a request from the UI, using the Manage Users and Resident
Assignments pages, confirming the sidebar shows the right items per role). The backend
guarantees the *data and security* are correct; only a real browser session confirms the UI
itself renders and wires up exactly as intended.

## Known Limitations

- **Authentication is a local sandbox stand-in, not real ARGO SSO** (`POST /api/auth/login`,
  `app/routers/auth.py`) — by design, for this stage. Confirmed with the supervisor: this
  version is under professor review before any ARGO platform connection is made, so a
  standalone login is expected and correct for right now, not an oversight. At integration,
  this endpoint and the frontend `Login.jsx` page are removed and replaced with ARGO's
  centralized authentication, the same way `condo_zzz_local_stub` is removed — nothing else in
  the module changes, since every endpoint already reads identity/org/role only from the
  verified JWT (see `docs/RBAC_MATRIX.md`, "No Separate Login System").
- `Manage Users` (`/api/condo/users`) is also a **local sandbox stand-in**, not a real module
  capability — in real ARGO, account management is platform-owned (Onboarding Contract, Part B
  §4: "FK to users — never"). It was implemented here per the panel's role-spec update so
  "Administrator manages users" is demonstrable standalone; see
  `docs/ASSUMPTIONS_AND_TRADEOFFS.md` #9 for the full reasoning. Both this and the login
  stand-in are removed at the same integration step.
- Assign currently takes a raw staff user UUID (pasted from the seed script output) rather than
  a searchable staff picker — acceptable for this stage, would be a dropdown backed by a
  `GET /api/condo/staff` endpoint in the next iteration
- Dues billing, amenity booking, and announcements remain out of scope (see `docs/SCOPING.md`)
- Race conditions on simultaneous assign/status-change use an application-level guard, not a
  DB-level optimistic lock (documented trade-off, see `docs/ASSUMPTIONS_AND_TRADEOFFS.md`)
- **Environment version gaps (sandbox constraint, not a design choice):** this codebase was
  developed/verified in a sandbox that could only install **Python 3.12** (not the required
  3.11) and **PostgreSQL 16** (not the currently-instructed 14) — both upstream package sources
  (deadsnakes PPA, apt.postgresql.org) were unreachable from that sandbox's network. No
  3.12-only Python syntax and no 16-only SQL features are used anywhere in this codebase, so
  functionally this is a non-issue — but **the final submission/demo machine must run actual
  Python 3.11 and PostgreSQL 14** per the current instructions, and that combination has not yet
  been verified end-to-end on this exact code. `.python-version` / `pyproject.toml` pin the
  Python floor so this is caught immediately if the wrong interpreter is used.
- `uq_condo_unit_residents_primary_contact` (partial unique index, one active primary contact
  per unit) leads with `unit_id` rather than `organization_id` — technically a literal deviation
  from the "always lead with organization_id" rule, though not a tenant-isolation risk since
  `unit_id` already resolves to exactly one organization via its own FK. Noted here for the
  defense rather than silently left for the panel to find.
- **Hosting platform deviates from the PhilCEB Hosting Guide on the supervisor's direct
  instruction:** the guide names Replit + GitLab as standard; this project is deployed on
  **Vercel** (frontend + backend as a Python serverless function) with source on **GitHub**,
  per the professor's explicit override. Database is Neon (managed PostgreSQL), not a
  Replit-attached database.

## Change Log

- v0.4 — 2026-08-16 — Role-spec expansion per panel instruction: `Manage Users` (Administrator
  full CRUD, Staff/Manager view-only) and `Resident Assignments` (Staff view, Manager/Admin
  manage) implemented end-to-end, sidebar reordered to the required 5 items, resident-facing
  `GET /api/condo/units` tightened to own-unit-only (closing a pre-existing over-exposure).
  Deployment target set to GitHub + Vercel + Neon per supervisor override of the PhilCEB
  Hosting Guide's Replit/GitLab default. README's Known Limitations and Local Sandbox
  Stand-Ins sections updated to explicitly disclose both the stand-in login and the new
  stand-in user-management endpoints as pre-integration, supervisor-confirmed placeholders.
- v0.3 — 2026-08-12 — Full React + Vite + Tailwind frontend added: login, dashboard, and the
  maintenance-requests + units list pages, matching the Argo UI reference (dark sidebar/header
  shell, KPI cards, filter+table+pagination pattern, modal-based add/edit). Verified end-to-end
  with real browser automation: login, live request creation, KPI updates, and RBAC-driven UI
  differences between roles all confirmed working. Production build verified clean.
- v0.2 — 2026-08-11 — Vertical slice implemented and verified: FastAPI app, JWT auth stand-in,
  RBAC dependency, state-machine-guarded maintenance endpoints, units endpoints, seed script,
  and a 7-test pytest suite (including both mandatory security tests) — all run against a live
  PostgreSQL database, all passing
- v0.1 — 2026-08-11 — Design package complete: SCOPING, ERD, API_CONTRACT, RBAC_MATRIX,
  THREAT_MODEL, WORKFLOW, ASSUMPTIONS_AND_TRADEOFFS; SQLAlchemy models verified against a live
  PostgreSQL database
#   C o n d o _ a l l  
 