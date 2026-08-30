# Scoping Brief — Condominium Management Module

**Intern:** Utrera · **Assigned prefix:** `condo_` · **Platform:** ARGO (multi-tenant SaaS)

## The Problem This Module Solves

Condominium corporations operating on the multi-tenant ARGO platform currently track units,
residents, dues, maintenance tickets, and shared-amenity bookings across spreadsheets, paper
logs, and group chats. This causes missed dues follow-up, lost maintenance tickets,
double-booked amenities, and no audit trail for who approved what.

This module gives condo staff a system to manage the core **unit**, **maintenance-request**,
and **billing/payments** lifecycle inside ARGO's multi-tenant platform, plus a dedicated portal
for Unit Owners and a Superadmin Portal for condo-wide administration.

## Intended Users

Five user types, per the panel's spec — **Resident** and **Unit Owner** were originally combined
into one "Resident / Unit Owner" row; Unit Owner is now split out as its own role with its own
portal, since a title-holder's needs (billing, payments, seeing who's linked to their unit) are
distinct from a tenant's.

| Role | What they can do |
|---|---|
| Resident (Tenant) | View own unit, submit maintenance requests, cancel own requests, view/pay own bills |
| Unit Owner | Everything Resident (Tenant) can do, plus a dedicated Owner Portal, and can see who is currently linked to the unit(s) they own |
| Front Desk Staff | View all requests, create requests, assign requests, update status, view billing, record payments on behalf of a resident/owner |
| Property Manager | Everything Staff can do, plus delete requests, manage units, manage resident-to-unit assignments, create/edit/void bills |
| Administrator | Full access to all module actions, plus the Superadmin Portal (condo-wide settings, users, billing configuration, portal configuration) |

Roles, permissions, and the authenticated user's identity all come from the **ARGO platform
JWT** — this module does not define or store its own user accounts (see
`ASSUMPTIONS_AND_TRADEOFFS.md` and `RBAC_MATRIX.md`).

## Features Included (V1)

- **Unit records** (unit number, building, floor, status), scoped per organization
- **Unit-resident linkage** (owner / tenant / co-resident, move-in / move-out history)
- **Maintenance Requests** — the core entity: a resident-submitted issue tied to a unit,
  tracking lifecycle status (submitted → assigned → in progress → completed / cancelled /
  rejected), with assignment and guarded status transitions
- **Bill Management** — recurring or one-time charges billed to a unit (association dues,
  utilities, or other), created/edited/voided by Property Manager/Administrator
- **Payments** — a payment section for both Unit Owners and Residents (Tenants) to pay their
  own bills, or for Staff/Manager/Administrator to record a payment on their behalf; no live
  payment gateway is integrated (see Known Limitations)
- **Owner Portal** — a dedicated frontend surface for the Unit Owner role: their unit(s),
  who else is currently linked to them, outstanding bills, and payment history
- **Superadmin Portal** — an Administrator-only frontend surface aggregating organization
  identity settings, user management (reusing the existing Manage Users endpoints), billing
  configuration defaults, and portal configuration feature toggles

## Features Explicitly Excluded from V1

- Amenity booking / shared-facility reservations
- Announcements / resident notices
- A live payment gateway integration (Stripe/PayMongo/etc.) — payments are recorded as
  immediately settled once submitted through this module, with no external processor call
- An automated job to generate the next period's bill instance from a recurring bill template
  (the `billing_cycle` field models *that* a bill recurs; actually rolling it forward each
  period would be a scheduler, out of scope for this vertical slice)

These are described at a high level in `ASSUMPTIONS_AND_TRADEOFFS.md` so the design isn't
blocked by them later, but no schema or endpoint for them ships in this vertical slice.

## Module Tables (my prefix: `condo_`)

| Table | Purpose |
|---|---|
| `condo_units` | A condo's physical unit inventory |
| `condo_unit_residents` | Links a platform user to a unit as owner/tenant/co-resident |
| `condo_maintenance_requests` | Core entity — a resident-submitted work order tied to a unit |
| `condo_bills` | A charge billed to a unit — association dues, utility, or other; one-time or recurring |
| `condo_payments` | A payment applied against a `condo_bills` row |
| `condo_portal_settings` | Condo-wide key/value configuration, managed from the Superadmin Portal |

`organizations` and `users` are **platform tables owned by ARGO**, not part of this module's
deliverable. My sandbox includes a throwaway local stub of both (see `README.md` → "Local
sandbox setup") purely so foreign keys resolve while I develop standalone; that stub is
discarded at integration.

## Assumptions

- One `organization_id` = one condominium corporation (an ARGO tenant)
- A resident or unit owner is always an existing ARGO platform user; this module stores no
  separate identity records for people — only unit-linkage rows (`condo_unit_residents`)
- Each condo corporation is a separate `organization_id` tenant on the ARGO platform
- The ARGO platform JWT carries `sub` (user id), `org` (organization id), and enough role
  information to resolve permissions — see the open question below
- A unit can have at most one active primary contact at a time, but any number of owners/
  tenants/co-residents linked concurrently (unchanged by adding the Unit Owner role — it only
  changes which *auth role* a `condo_unit_residents.relationship_type = 'owner'` row's user
  account holds, not the linkage model itself)

## Open Questions

- Does ARGO's platform JWT include structured permission claims directly, or must this module
  call a centralized permissions service per request?
- Should a unit support multiple concurrent owners (co-ownership), or is a single primary
  owner sufficient for V1? (Current schema allows multiple `condo_unit_residents` rows per
  unit but only one active primary contact — see unique constraint in `ERD.md`.)
- Who can waive or void a bill — Property Manager only, or also Staff with a reason code?
  (Currently `billing.manage`/void is Manager+Administrator only; Staff can record payments
  but not waive/void a bill.)
- Should "Billing Configuration" (late fee %, due day of month) actually apply automatically
  when a Manager creates a new bill, or remain informational until a future recurring-billing
  scheduler is built? (Currently informational only — see Known Limitations.)

## Known Limitations

- No automated recurring dues billing engine — a recurring bill's next-period instance is not
  auto-generated; Manager/Administrator create each period's bill manually for now
- No pagination limit above 100 items per page on list endpoints
- No payment gateway — payments are recorded, not processed, by this module
- Single role per user; no multi-role support (matches ARGO platform's existing model)
- Race conditions on simultaneous assign/status-change (and simultaneous payments against the
  same bill) are guarded at the application layer, not with a DB-level optimistic lock —
  documented as a trade-off in `THREAT_MODEL.md`
