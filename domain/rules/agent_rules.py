from datetime import date, datetime
from config import MAX_AGENTS_PER_TL
from domain.exceptions.custom_exceptions import BusinessRuleError

TENURITY_BUCKETS = [
    (0, 30, 'New Hire', '0-30'),
    (31, 89, 'Early Tenure', '31-89'),
    (90, 149, 'Established', '90-149'),
    (150, 10**6, 'Experienced', '150+'),
]

def derive_tenurity(active_date_iso: str, ref: date = None):
    """BR-02: returns (tenurity, days_range) from active_date."""
    ref = ref or date.today()
    start = datetime.strptime(active_date_iso, '%Y-%m-%d').date()
    days = (ref - start).days
    
    for lo, hi, ten, rng in TENURITY_BUCKETS:
        if lo <= days <= hi:
            return ten, rng
            
    raise BusinessRuleError(
        'BR-02', 
        f'cannot derive tenurity for {days} days'
    )

def assert_tl_capacity(team_manager, current_count):
    """BR-01: cap span of control at 15."""
    if current_count >= MAX_AGENTS_PER_TL:
        raise BusinessRuleError(
            'BR-01',
            f'TL {team_manager} already has {current_count} agents '
            f'(max {MAX_AGENTS_PER_TL})'
        )

def assert_can_deactivate(agent_id, has_recent_activity: bool):
    """BR-03: cannot deactivate an active agent."""
    if has_recent_activity:
        raise BusinessRuleError(
            'BR-03', 
            f'agent {agent_id} has activity in last 7 days'
        )