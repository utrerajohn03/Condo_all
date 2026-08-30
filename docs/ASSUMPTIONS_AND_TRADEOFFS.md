# Assumptions and Trade-offs — Condominium Management Module

This document exists so I can defend *why* the module looks the way it does, not just *what*
it does. Each entry states the decision, the alternative I rejected, and why.

## 1. `organizations` and `users` are stub tables in my sandbox, never in the deliverable

**Decision:** create a throwaway local migration (`condo_zzz_local_stub`) with a minimal
`organizations` and `users` table, insert one fake org + one fake user, and point my module's
foreign keys at them.

**Alternative rejected:** designing my own richer user/org model "just in case."

**Why:** the platform contract is explicit that these tables already exist in ARGO. Building my
own would create a second source of truth that has to be reconciled at integration — exactly
the kind of merge conflict the contract's "single import line" rule is designed to prevent.

## 2. No FK from module tables to `users` — loose UUID only

**Decision:** `created_by`, `updated_by`, `requested_by`, `assigned_to` are all plain UUID
columns with no foreign-key constraint.

**Alternative rejected:** a real FK to `users.id`, which would give referential integrity "for
free."

**Why:** users get deactivated or reassigned in the real platform, and a hard FK would either
block those operations or require cascading logic this module has no business owning. The
contract states this explicitly — I'm following it, not improvising it — but I'd defend it the
same way even without the contract: a module shouldn't be able to prevent a platform-level user
action just because it once referenced that user.

## 3. Table prefix (`condo_`) on every module table, no exceptions

**Decision:** `condo_units`, `condo_unit_residents`, `condo_maintenance_requests` — every table
I own carries the prefix, including in Alembic migration table names and SQLAlchemy
`__tablename__` values.

**Why:** with 25 interns building modules that merge into one platform, an unprefixed
`units` or `requests` table would collide with someone else's. The prefix is the entire
mechanism that makes 25 independently-developed schemas mergeable without a rename pass.

## 4. Soft-delete everywhere, no hard `DELETE` in application code

**Decision:** every business table has `deleted_at`; the `DELETE` endpoint sets it instead of
removing the row; all reads filter `WHERE deleted_at IS NULL`.

**Alternative rejected:** hard delete for simplicity.

**Why:** maintenance history has audit value even after a ticket is "removed" — a Manager
deleting a mistakenly-created ticket shouldn't erase the fact that it existed if a dispute comes
up later. Soft-delete is one extra `WHERE` clause; hard-delete is unrecoverable data loss.

## 5. Optimistic locking NOT implemented for assign/status races

**Decision:** the race-condition guard is a simple "check current status, then write" at the
application layer — not a DB-level `WHERE status = :expected_status` compare-and-swap.

**Why this is a deliberate trade-off, not an oversight:** a true fix needs either a DB-level
conditional update or a transaction-level lock, both of which add complexity disproportionate
to this module's actual concurrency profile (a handful of staff acting on a given ticket, not a
high-throughput booking system). I'm documenting this explicitly in `THREAT_MODEL.md` rather
than silently shipping the gap, and I can implement the stricter version if the defense
determines the risk warrants it.

## 6. Resident's "cancel own request" is enforced as two separate checks, not one

**Decision:** a Resident cancelling their own request passes through (a) the general
permission check (`maintenance.update_status`, which Residents do hold) and (b) an
ownership + fixed-target-state check (must be their own `requested_by`, target must be exactly
`cancelled`).

**Alternative rejected:** a separate `maintenance.cancel_own` permission.

**Why:** I considered a dedicated permission name, but the ownership check already has to exist
regardless (a Resident's `maintenance.view` is also ownership-scoped), so adding a second
permission name would duplicate logic without adding real access control — the ownership check
*is* the boundary here, not the permission name.

## 7. Dues billing, amenity booking, and announcements are scoped out, not stubbed

**Decision:** these are mentioned in the Scoping Brief for completeness but have zero schema,
zero endpoints, and zero UI in this vertical slice.

**Alternative rejected:** adding placeholder tables/routes to "show the shape" of future work.

**Why:** the assessment instructions are explicit that a focused, complete slice beats several
unfinished pages. A stub table for dues billing would need its own tenant isolation, audit
fields, and RBAC to be honest about its incompleteness — better to not ship it than to ship it
half-secured.

## 8. API routes are namespaced under `/api/condo/...`

**Decision:** every module endpoint lives under a module-specific path prefix, matching the
table-prefix convention.

**Why:** the assessment's own example (`POST /api/bookings`) doesn't show a module prefix, but
with 25 modules sharing one ARGO domain, an unprefixed `/api/maintenance-requests` risks the
same collision problem the table-prefix rule solves for the database. I chose to apply the same
discipline to the API surface even though it wasn't spelled out, and I'd defend this as
consistent with the platform's stated multi-tenant, multi-module design intent.

## 9. "Manage Users" was added as a local-only endpoint set, against the Onboarding Contract's own boundary rule

**Decision:** implemented full user CRUD (`/api/condo/users` — add/edit/delete/activate/
deactivate) inside this module, gated to Administrator, per an explicit panel instruction.

**Why this is a tension, not a clean fit:** the Onboarding Contract (Part B §4) is explicit —
*"FK to users — never... those already exist in Argo"* — this module was designed to never own
account data. The panel's later role-spec update asks for "Administrator: Add/Edit/Delete/
Activate/Deactivate users" as a concrete module capability, which only makes sense if this
module *does* own that data, at least in the local sandbox. I resolved this the same way the
`condo_zzz_local_stub` migration already resolves the equivalent problem for `organizations`/
`users` existing at all: everything under `/api/condo/users` is explicitly documented as a
**local sandbox stand-in**, not something handed over at integration — in real ARGO, account
management stays on the platform side, and this router would be deleted, the same way
`condo_zzz_local_stub.py` is deleted. I added an `is_active` column to the local stub `users`
table (not a `condo_` table, so this doesn't touch the table-prefix or migration-handover rules)
specifically to support activate/deactivate.

## 10. Manager's "manage residents and users within scope" was interpreted as assignment management, not account management

**Decision:** Manager gets `assignment.manage` (create/end resident-to-unit links) but not
`user.manage` (account CRUD, role changes, delete) — that stays Administrator-only.

**Why:** the panel's spec is explicit and itemized for Administrator ("Add users. Edit users.
Delete users. Activate or deactivate users.") but vaguer for Manager ("manage residents and
users within their permitted management scope"). Reading "manage residents" as *managing which
residents are linked to which unit* keeps Manager's added power scoped to data this module
actually owns (`condo_unit_residents`), rather than raw platform accounts, which is more
consistent with rule #9 above. If the panel meant for Manager to also hold full `user.manage`,
that's a one-line change in `app/core/permissions.py` (documented there too).

## 11. `GET /api/condo/units` was tightened to scope Residents to their own unit(s) only

**Decision:** the existing units-list endpoint, which previously returned every unit in the
organization to any role holding `unit.view` (including Resident), now filters to the caller's
own linked unit(s) when the caller is a Resident — matching the same pattern already used for
`GET /api/condo/maintenance-requests`.

**Why:** this was a pre-existing gap against the panel's explicit new rule — *"Residents must
NOT be able to: View other units."* The endpoint's original behavior (Resident sees all org
units) predates that rule and was never exercised by a Resident-facing page, so tightening it
now doesn't remove functionality anyone was using — it closes a real over-exposure. A new
`GET /api/condo/units/mine` endpoint covers the resident-facing "view my unit" flow explicitly,
separately from the still-org-wide list Staff/Manager/Administrator continue to get.
