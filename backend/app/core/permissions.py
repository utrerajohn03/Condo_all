"""
Role -> permission map. Mirrors docs/RBAC_MATRIX.md exactly.

Five platform user types (per the panel's spec):
  1. Resident (tenant)  — rents/occupies a unit, does not hold title to it
  2. Unit Owner         — holds title to a unit; gets the dedicated Owner Portal,
                           can view/pay bills for unit(s) they own, and can see who
                           is currently linked to their own unit(s)
  3. Front Desk Staff
  4. Property Manager
  5. Administrator      — also the sole holder of `superadmin.access`, i.e. the
                           Superadmin Portal (condo-wide settings, users, billing
                           configuration, portal configuration)
"""

ROLE_PERMISSIONS = {
    'resident': {'maintenance.view', 'maintenance.create', 'maintenance.update_status', 'unit.view',
                 'billing.view', 'payment.view', 'payment.record'},
    'unit_owner': {'maintenance.view', 'maintenance.create', 'maintenance.update_status', 'unit.view',
                   'billing.view', 'payment.view', 'payment.record', 'assignment.view'},
    'staff':    {'maintenance.view', 'maintenance.create', 'maintenance.assign',
                 'maintenance.update_status', 'unit.view',
                 'user.view', 'assignment.view',
                 'billing.view', 'payment.view', 'payment.record'},
    'manager':  {'maintenance.view', 'maintenance.create', 'maintenance.assign',
                 'maintenance.update_status', 'maintenance.delete', 'unit.view', 'unit.manage',
                 'user.view', 'assignment.view', 'assignment.manage',
                 'billing.view', 'billing.manage', 'payment.view', 'payment.record'},
    'admin':    {'maintenance.view', 'maintenance.create', 'maintenance.assign',
                 'maintenance.update_status', 'maintenance.delete', 'unit.view', 'unit.manage',
                 'user.view', 'user.manage', 'assignment.view', 'assignment.manage',
                 'billing.view', 'billing.manage', 'payment.view', 'payment.record',
                 'superadmin.access'},
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
