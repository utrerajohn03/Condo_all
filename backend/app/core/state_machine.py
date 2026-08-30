"""
State-transition table for condo_maintenance_requests.status, mirroring docs/WORKFLOW.md.
"""

ALLOWED_TRANSITIONS = {
    'submitted': {'assigned', 'rejected', 'cancelled'},
    'assigned': {'in_progress', 'cancelled'},
    'in_progress': {'completed', 'cancelled'},
    'completed': set(),
    'cancelled': set(),
    'rejected': set(),
}

TERMINAL_STATES = {'completed', 'cancelled', 'rejected'}
ASSIGNEE_RESTRICTED_TRANSITIONS = {'in_progress', 'completed'}


def is_transition_allowed(current_status: str, target_status: str) -> bool:
    return target_status in ALLOWED_TRANSITIONS.get(current_status, set())
