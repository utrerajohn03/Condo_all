# API Contract — Condominium Management Module

All module routes are namespaced under `/api/condo/...` so they never collide with another
intern's module when merged into ARGO. Every endpoint requires the ARGO platform JWT
(`Authorization: Bearer <token>`) **except** the local testing stand-in login.

## Quick Reference

| Method | URL | Purpose | Permission |
|---|---|---|---|
| POST | `/api/auth/login` | **Local testing stand-in only** — issues a JWT shaped like ARGO's, so this module is testable standalone | none (public, sandbox-only) |
| GET | `/api/condo/maintenance-requests` | List requests for caller's organization | `maintenance.view` |
| POST | `/api/condo/maintenance-requests` | Create a new maintenance request | `maintenance.create` |
| GET | `/api/condo/maintenance-requests/detail?id={id}` | Fetch one request's detail | `maintenance.view` |
| POST | `/api/condo/maintenance-requests/assign?id={id}` | Assign a request to staff | `maintenance.assign` |
| POST | `/api/condo/maintenance-requests/status?id={id}` | Change a request's status | `maintenance.update_status` |
| DELETE | `/api/condo/maintenance-requests/{id}` | Soft-delete a request | `maintenance.delete` |
| GET | `/api/condo/units` | List units for caller's organization | `unit.view` |
| POST | `/api/condo/units` | Create a unit | `unit.manage` |

> **On `POST /api/auth/login`:** in the real ARGO integration this endpoint does not exist —
> the platform issues the JWT before the user ever reaches this module. It exists solely in my
> sandbox so I can generate a token shaped like ARGO's (`sub`, `org`, role/permission claims)
> to test the module end-to-end without the real platform. It is explicitly **not** part of
> what gets handed over at integration (see `README.md` → Local sandbox setup).

## `POST /api/auth/login` *(sandbox stand-in — not delivered)*

- **Permission:** none (public)
- **Request body:** `{ "email": string, "password": string }`
- **Response:** `{ "token": string, "role": string }`

| Status | Meaning |
|---|---|
| 200 | Success |
| 401 | Invalid credentials |
| 422 | Missing fields |

## `GET /api/condo/maintenance-requests`

- **Purpose:** List all maintenance requests belonging to the caller's organization
  (Residents see only their own unit's requests)
- **Permission:** `maintenance.view`
- **Query parameters (all optional):** `status`, `unit_id`, `priority`
- **Response:** `{ "data": [ { id, status, priority, category, unit_number, assigned_to, created_at } ] }`

| Status | Meaning |
|---|---|
| 200 | Success |
| 401 | Missing/invalid token |
| 403 | Lacks `maintenance.view` |

## `POST /api/condo/maintenance-requests`

- **Purpose:** Submit a new maintenance request for a unit
- **Permission:** `maintenance.create`
- **Request body:** `{ "unit_id": UUID, "category": string, "description": string, "priority": string }`
  — any other field sent (e.g. `organization_id`, `status`, `requested_by`, `created_by`) is
  silently ignored, never trusted
- **Validation rules:** `unit_id` must be a valid UUID and must belong to the caller's
  organization; `description` must be 10–2000 characters; Residents may only submit for a unit
  they are linked to via `condo_unit_residents`
- **Response (201):** `{ "data": { id, status, requested_by, created_at } }`

| Status | Meaning |
|---|---|
| 201 | Created |
| 403 | Lacks `maintenance.create`, or unit is not caller's own |
| 404 | Unit not found in caller's org |
| 422 | Validation failed |

## `GET /api/condo/maintenance-requests/detail?id={id}`

- **Purpose:** Fetch one maintenance request's full detail
- **Permission:** `maintenance.view`

| Status | Meaning |
|---|---|
| 200 | Success |
| 404 | Not found — returned for both "doesn't exist" and "belongs to another org," so existence is never leaked |
| 422 | Invalid id format |

## `POST /api/condo/maintenance-requests/assign?id={id}`

- **Purpose:** Assign an outstanding request to a staff member
- **Permission:** `maintenance.assign`
- **Request body:** `{ "assigned_to": UUID }`
- **Guard condition:** request must currently be `status = submitted`
- **Response (200):** `{ "data": { id, status: "assigned", assigned_to } }`

| Status | Meaning |
|---|---|
| 200 | Assigned |
| 403 | Lacks permission |
| 404 | Not found in caller's org |
| 409 | Request is not in submitted status |
| 422 | `assigned_to` is not a valid staff user in the caller's org |

## `POST /api/condo/maintenance-requests/status?id={id}`

- **Purpose:** Advance a request's lifecycle (start, complete, cancel, reject)
- **Permission:** `maintenance.update_status`
- **Request body:** `{ "status": string, "reason": string (required only when status="rejected") }`
- **Guard condition:** target transition must appear in the state-transition table
  (`WORKFLOW.md`)
- **Response (200):** `{ "data": { id, status } }`

| Status | Meaning |
|---|---|
| 200 | Status updated |
| 403 | Lacks permission |
| 404 | Not found in caller's org |
| 409 | Invalid transition for current status |
| 422 | Rejecting without a reason |

## `DELETE /api/condo/maintenance-requests/{id}`

- **Purpose:** Soft-delete a request (sets `deleted_at`; row is preserved, hidden from normal
  queries) — added beyond the original quick-reference table because `maintenance.delete`
  exists in the RBAC matrix (Manager/Admin) but had no endpoint to use it
- **Permission:** `maintenance.delete`
- **Response (200):** `{ "data": { "id": UUID, "deleted": true } }`

| Status | Meaning |
|---|---|
| 200 | Deleted |
| 403 | Lacks `maintenance.delete` |
| 404 | Not found in caller's org |

## `GET /api/condo/units` and `POST /api/condo/units`

- **Purpose:** List / create unit records, scoped to the caller's organization
- **Permission:** `unit.view` (GET) / `unit.manage` (POST)
- **POST request body:** `{ "unit_number": string, "building": string, "floor": int, "status": string }`
- **Validation:** `unit_number` + `building` must be unique within the organization
  (`uq_condo_units_org_building_number`)

| Status | Meaning |
|---|---|
| 200 / 201 | Success |
| 403 | Lacks permission |
| 409 | Duplicate unit_number + building in this organization |
| 422 | Validation failed |

## `GET /api/condo/units/mine`

- **Purpose:** The caller's own currently-linked unit(s) — "View their assigned unit" (Resident).
  Available to every authenticated role (no permission gate beyond auth), since it only ever
  returns the caller's *own* linkage rows.

## `PATCH /api/condo/units/{id}`

- **Purpose:** Edit a unit's fields — Manager/Administrator "Manage units"
- **Permission:** `unit.manage`
- **Request body:** any subset of `{ unit_number, building, floor, status }` (partial update)

| Status | Meaning |
|---|---|
| 200 | Updated |
| 403 | Lacks `unit.manage` |
| 404 | Not found in caller's org |
| 422 | Validation failed |

## `GET /api/condo/users/me`

- **Purpose:** "View their own profile" — every authenticated role, own record only
- **Permission:** none beyond authentication

## `GET /api/condo/users`, `POST /api/condo/users`, `PATCH /api/condo/users/{id}`, `POST /api/condo/users/{id}/activate`, `POST /api/condo/users/{id}/deactivate`, `DELETE /api/condo/users/{id}`

**Local sandbox stand-in only** — see `docs/ASSUMPTIONS_AND_TRADEOFFS.md`. Not part of what's
handed over to real ARGO, same as `condo_zzz_local_stub` and `POST /api/auth/login`.

- **Purpose:** "Manage Users" — Administrator adds/edits/deletes/activates/deactivates
  accounts; Staff/Manager can list ("View residents" / "View users") but not write
- **Permission:** `user.view` (GET), `user.manage` (POST/PATCH/DELETE/activate/deactivate)
- **GET query params:** `role` (optional filter, e.g. `?role=resident`)
- **POST/PATCH body:** `{ email, full_name, password, role }` (POST) / any subset (PATCH)
- **Guards:** an Administrator cannot deactivate or delete their own account; a deactivated
  account is blocked at login and on every subsequent request with an already-issued token

| Status | Meaning |
|---|---|
| 200 / 201 | Success |
| 400 | Attempted to deactivate/delete your own account |
| 403 | Lacks permission |
| 404 | Not found in caller's org |
| 409 | Email already in use (create) |

## `GET /api/condo/unit-residents`, `POST /api/condo/unit-residents`, `POST /api/condo/unit-residents/end?id={id}`

- **Purpose:** "Resident Assignments" — links a platform user to a unit as
  owner/tenant/co-resident, with move-in/move-out history
- **Permission:** `assignment.view` (GET), `assignment.manage` (POST / end)
- **POST request body:** `{ unit_id, user_id, relationship_type, is_primary_contact, moved_in_at }`
- **Validation:** `unit_id` and `user_id` must belong to the caller's organization; only one
  active primary contact per unit at a time (`uq_condo_unit_residents_primary_contact`)

| Status | Meaning |
|---|---|
| 200 / 201 | Success |
| 403 | Lacks permission |
| 404 | Unit or user not found in caller's org |
| 409 | Unit already has an active primary contact / assignment already ended |
