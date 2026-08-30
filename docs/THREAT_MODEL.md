# Threat Model — Condominium Management Module

| Threat | Attack Scenario | Impact | Mitigation | Required Test |
|---|---|---|---|---|
| **Cross-tenant access / IDOR** | A user from Condo B requests Condo A's maintenance ticket by ID | High | Every query filters by `organization_id` from the verified JWT — never from the URL, body, or query string | Confirm Condo B receives 404, not the record |
| **Broken authorization** | A Resident-level account attempts to assign a ticket (requires Staff+) | High | `require_permission()` checked before any write | Confirm 403 returned |
| **Mass assignment / over-posting** | Client sends `organization_id`, `requested_by`, `created_by`, or `status` in the create request body | High | Strict input whitelist — only `unit_id` / `category` / `description` / `priority` are read from the create body; everything else is stamped server-side from the JWT or rejected | Confirm forged fields have no effect on the created record |
| **SQL injection** | Malicious string in `description` or `category` | High | 100% parameterized queries via SQLAlchemy ORM — no raw string-built SQL anywhere in the module | Confirm malicious input is treated as literal data, not executed |
| **Invalid/malicious input** | Non-UUID `unit_id`, oversized `description` | Medium | Explicit Pydantic validation (UUID typing, 10–2000 char length) before any DB call | Confirm 422 returned for malformed input |
| **Cross-tenant FK reference** | Condo A staff supplies a `unit_id` that actually belongs to Condo B | High | Request creation re-checks that `unit_id` belongs to the caller's own organization, not just that it exists | Confirm 404 returned when referencing another org's unit |
| **Race condition on assign/status** | Two simultaneous requests assign and cancel the same ticket | Medium | Guard conditions checked at write time (`status != target-incompatible state`) reduce but do not fully eliminate the window; a stricter fix would use a DB-level optimistic lock (`WHERE status = :expected_status`) — documented trade-off, not implemented in V1 | Confirm a cancel following an assign (or vice versa) still leaves the record in a single consistent state, not corrupted |
| **Personal data exposure** | Resident contact info returned to a role that shouldn't see it, or a Resident's list returns another unit's tickets | High | List/detail endpoints require `maintenance.view` plus unit-ownership scoping for Residents | Confirm no endpoint returns another unit's requests without the correct scope |
| **Unauthorized status changes** | A Resident attempts to move their own ticket to `completed` or `rejected` instead of only `cancelled` | High | Resident's allowed target state is hardcoded to `cancelled` only, checked server-side regardless of what the client sends | Confirm 403 when a Resident submits any status other than `cancelled` |
| **Terminal-state tampering** | Client attempts to change a `completed`/`cancelled`/`rejected` ticket back to an active state | Medium | State-transition table has no allowed next state for terminal statuses; the check runs before any field is written | Confirm 409 returned, no fields changed |
| **Assignee impersonation on transitions** | A staff member who is *not* the assignee tries to mark someone else's assigned ticket `in_progress`/`completed` | Medium | Guard condition requires caller to be the assignee **or** hold `maintenance.assign` (covers Manager/Admin oversight) | Confirm 403 for a staff member who is neither the assignee nor holds the override permission |

## Module-Specific Considerations (Condominium Management)

- **Resident contact/PII exposure across units:** a resident list or detail view must never
  leak another unit's resident info — enforced by the same ownership-scoping check used for
  maintenance requests, applied identically to `condo_unit_residents` queries.
- **Move-in/move-out history tampering:** only `unit.manage` (Manager/Admin) can edit
  `condo_unit_residents` rows; Residents can view but not edit their own linkage record,
  preventing a resident from falsely extending their own occupancy record or removing another
  resident's history.
- **Primary-contact conflicts:** the partial unique index
  (`is_primary_contact = true AND moved_out_at IS NULL`) prevents two residents from both being
  flagged the active primary contact for the same unit — a data-integrity issue that would
  otherwise cause ambiguous notification/escalation routing.
