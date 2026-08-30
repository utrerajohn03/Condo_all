# Module Page and Dashboard Structure — Condominium Management Module

Follows the required sidebar blueprint format from the Pre-Development Assessment (Deliverable
8) and the Argo UI Reference (flat sidebar, sub-sections as in-page tabs, KPI row, modal-based
add/edit). Permission names match `docs/RBAC_MATRIX.md` exactly.

**Implementation status (updated):** All five sidebar items are now implemented end-to-end
(backend + frontend). `Manage Users` and `Resident Assignments` were originally out of scope for
the vertical slice (see prior revision of this doc) but were added per the panel's role-spec
update — see `docs/ASSUMPTIONS_AND_TRADEOFFS.md` for the trade-off this required (local-only
account management standing in for what is platform-owned in real ARGO).

---

## Sidebar Item: Dashboard

**Purpose:** Give any authenticated module user a one-glance summary of unit occupancy and
maintenance workload for their organization.

**Tabs:** None — single overview page.

**KPIs:**
- Total Units – count of `condo_units` where `deleted_at IS NULL`, scoped to `organization_id`
- Occupied / Vacant / Under Maintenance – count of `condo_units` grouped by `status`
- Open Maintenance Requests – count of `condo_maintenance_requests` where `status` is not in
  `(completed, cancelled, rejected)`

**Charts:**
- Maintenance Status Breakdown – donut/bar chart (recharts), one segment per
  `condo_maintenance_requests.status` value, filtered to the last 30/90 days, no interactivity
  beyond hover tooltip. Purpose: show staff where the current workload sits in the lifecycle at
  a glance.

**Tables:** None — this page is KPI + chart only, per the Argo UI "Dashboard/overview" pattern.

**Search / Filters / Sorting:** N/A (no table on this page).

**Row actions / Bulk actions:** N/A.

**Forms and Actions:** None — read-only page.

**Access and Permissions:**
- Visible to all authenticated roles (Resident, Staff, Manager, Administrator)
- KPI numbers are always scoped to the caller's `organization_id` from the JWT — a Resident
  sees org-wide unit/request counts (not filtered to their own unit) since occupancy is not
  sensitive per-resident data; the Maintenance Requests *list* page is what applies the
  per-resident ownership scope

---

## Sidebar Item: Maintenance Requests

**Purpose:** Create, track, assign, and resolve unit maintenance tickets through their full
lifecycle.

**Tabs:**
- All Requests
- Completed *(client-side filter shortcut over the same table, not a separate query — mirrors
  the "Completed" tab shown in the Utrera mockup)*

**KPIs:**
- New Requests – count where `status = 'submitted'`
- In Progress – count where `status = 'in_progress'`
- Overdue – count where `status IN ('submitted','assigned')` and `created_at` older than the
  module's SLA threshold (configurable; not yet enforced server-side — see Known Limitations)
- Resolved – count where `status = 'completed'`

**Charts:** None on this page (the status-breakdown chart lives on Dashboard, not duplicated
here, to avoid two sources of truth for the same number).

**Tables:**
- **Table name:** Maintenance Requests
- **Columns:** Reference/ID (short), Unit, Category, Priority, Status (badge), Assigned To,
  Created At, Actions
- **Search:** free-text over `category` / `description`
- **Filters:** Status (dropdown, matches the 6 lifecycle values), Priority, Unit
- **Sorting:** Created At (default: newest first), Priority
- **Row actions:** View detail, Assign (Staff+), Update Status (per allowed transition), Cancel
  (Resident: own request only)
- **Bulk actions:** None in V1 (single-record actions only — see `ASSUMPTIONS_AND_TRADEOFFS.md`
  on why bulk status changes were explicitly excluded from scope)

**Forms and Actions:**
- **New Request** (modal, not a full page, per Argo UI pattern) — fields: Unit (dropdown,
  scoped to caller's linked units if Resident), Category, Description, Priority. Action:
  Submit → `POST /api/condo/maintenance-requests`
- **Assign** (modal) — field: Assignee (staff user id). Action: Assign →
  `POST /api/condo/maintenance-requests/assign`
- **Update Status** (modal) — field: Target status (constrained to allowed transitions per
  `docs/WORKFLOW.md`), optional reason (required when rejecting). Action: `POST
  /api/condo/maintenance-requests/status`

**Access and Permissions:**
- **View page:** all roles (`maintenance.view`); Resident's table is pre-filtered server-side to
  their own linked unit(s)
- **New Request button:** `maintenance.create`
- **Assign row action:** `maintenance.assign` (Staff, Manager, Administrator only)
- **Update Status row action:** `maintenance.update_status`, plus the guard that a Resident may
  only move their own request to `cancelled`
- **Delete:** `maintenance.delete` (Manager, Administrator only) — not yet wired to a UI button
  in the vertical slice; endpoint scaffolding reserved for the next iteration

---

## Sidebar Item: Units

**Purpose:** Maintain the condo's physical unit inventory (number, building, floor, status).

**Tabs:**
- All Units
- Occupied
- Vacant
- Maintenance *(status filter shortcuts, mirrors the Utrera mockup's Units tabs)*

**KPIs:**
- Total Units Managed
- Current Occupancy Rate – `occupied / (total - deleted)`, computed at query time, never stored
  (see `ASSUMPTIONS_AND_TRADEOFFS.md` §6, "don't store what you can calculate")
- Vacant Units Available
- Under Maintenance

**Charts:** None — a unit inventory table is the primary artifact of this page; occupancy trend
over time is out of scope for V1.

**Tables:**
- **Table name:** Units
- **Columns:** Unit Number, Building / Floor, Status (badge), Linked Resident (primary contact,
  if any), Actions
- **Search:** unit number / building
- **Filters:** Building, Status
- **Sorting:** Unit Number, Building
- **Row actions:** View detail, Edit (Manager+)
- **Bulk actions:** None in V1

**Forms and Actions:**
- **New Unit Record** (modal) — fields: Unit Number, Building, Floor, Status. Action:
  `POST /api/condo/units`
- **Edit Unit** (modal) — same fields, pre-filled

**Access and Permissions:**
- **View page:** all roles (`unit.view`); Resident's table is scoped to their own linked unit(s)
  only
- **New Unit Record / Edit:** `unit.manage` (Manager, Administrator only)

---

## Sidebar Item: Resident Assignments

**Purpose:** Manage which platform users are linked to which unit, and their relationship type
(owner / tenant / co-resident), including move-in/move-out history.

**Tabs:**
- All Assignments
- Permanent *(relationship_type = owner)*
- Temporary *(relationship_type = tenant)*
- History *(moved_out_at IS NOT NULL)*

**KPIs:**
- Total Assignments (currently active — `moved_out_at IS NULL`)
- Pending Move-Ins (`moved_in_at` in the future)
- Recent Move-Outs (`moved_out_at` in the last 30 days)
- Total History (all-time row count, including moved-out)

**Charts:** None.

**Tables:**
- **Table name:** Resident-Unit Assignments
- **Columns:** Resident Name, Unit, Relationship, Date/Duration (moved-in → moved-out), Status,
  Actions
- **Search:** resident name / unit number
- **Filters:** Type (owner/tenant/co-resident), Status (active/upcoming/completed)
- **Sorting:** Move-in date
- **Row actions:** View, End Assignment (sets `moved_out_at`), Set as Primary Contact
- **Bulk actions:** None

**Forms and Actions:**
- **Assign Resident** (modal) — fields: Resident (user id, looked up by email), Unit,
  Relationship Type, Is Primary Contact, Move-in Date. Enforces the partial-unique constraint
  (`uq_condo_unit_residents_primary_contact`) — only one active primary contact per unit.

**Access and Permissions:**
- **View page:** Staff, Manager, Administrator (`assignment.view`)
- **Assign Resident / End Assignment:** Manager, Administrator only (`assignment.manage`)

---

## Sidebar Item: Manage Users

**Purpose:** Local sandbox stand-in for platform user management — see
`docs/ASSUMPTIONS_AND_TRADEOFFS.md`. In real ARGO, `users`/`organizations` are platform-owned and
this page would not exist inside the condo_ module; it was implemented here per the panel's
explicit instruction so "Administrator manages users" is demonstrable standalone.

**Tabs:** All Users, Manager, Staff, Residents *(role filter, matches the mockup)*

**KPIs:** Active Users, Total Users, Staff/Manager/Admin count, Residents count.

**Tables:**
- **Table name:** Users
- **Columns:** Name, Email, Role, Status (Active/Inactive), Actions
- **Search:** name / email
- **Filters:** role tabs (above)
- **Row actions:** Activate/Deactivate, Delete — **Administrator only**; Staff/Manager see the
  same table read-only ("View residents" / "View users")

**Forms and Actions:**
- **Add User** (modal, Administrator only) — fields: Email, Full Name, Password, Role

**Access and Permissions:**
- **View page:** Staff, Manager, Administrator (`user.view`) — Resident cannot reach this page
  at all (not in their sidebar; also blocked at the route and API level)
- **Add / Activate / Deactivate / Delete:** Administrator only (`user.manage`)
