from __future__ import annotations
from config import MAX_LOGIN_DURATION_SEC, MIN_OCCUPANCY, MAX_AUX_RATIO
from domain.exceptions.custom_exceptions import BusinessRuleError

STATE_FIELDS = ('aux_duration', 'break_1', 'break_2', 'break_3',
                'email_duration', 'lunch_duration', 'meeting_duration',
                'tech_issue_duration', 'personal_duration', 'task_duration',
                'training_duration', 'busy_duration', 'available_duration')

def assert_state_sum(record: dict):
    total = sum(record[f] for f in STATE_FIELDS)
    if total > record['login_duration']:
        raise BusinessRuleError('BR-07',
            f'states sum {total}s > login {record["login_duration"]}s')

def assert_login_duration(login_seconds):
    if login_seconds > MAX_LOGIN_DURATION_SEC:
        raise BusinessRuleError('BR-09',
            f'login {login_seconds}s exceeds max {MAX_LOGIN_DURATION_SEC}s')

def flag_for_review(record) -> list:
    flags = []
    if record['occupancy'] < MIN_OCCUPANCY:
        flags.append(f"LOW_OCCUPANCY ({record['occupancy']:.0%})")
    if record['aux_ratio'] > MAX_AUX_RATIO:
        flags.append(f"HIGH_AUX ({record['aux_ratio']:.0%})")
    return flags