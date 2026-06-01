from __future__ import annotations
import unittest
from domain.rules.productivity_rules import (
    assert_state_sum, assert_login_duration, flag_for_review)
from domain.exceptions.custom_exceptions import BusinessRuleError

def state_dict(**over):
    base = {f: 0 for f in (
        'aux_duration', 'break_1', 'break_2', 'break_3',
        'email_duration', 'lunch_duration', 'meeting_duration',
        'tech_issue_duration', 'personal_duration', 'task_duration',
        'training_duration', 'busy_duration', 'available_duration')}
    base['login_duration'] = 28800
    base.update(over)
    return base

class TestProductivityRules(unittest.TestCase):

    def test_state_sum_ok(self):
        assert_state_sum(state_dict(busy_duration=20000,
                                    available_duration=8000))

    def test_state_sum_overflow(self):
        with self.assertRaises(BusinessRuleError) as cm:
            assert_state_sum(state_dict(busy_duration=30000,
                                        available_duration=5000))
        self.assertEqual(cm.exception.rule_id, 'BR-07')

    def test_login_cap_ok(self):
        assert_login_duration(36000)

    def test_login_cap_exceeded(self):
        with self.assertRaises(BusinessRuleError) as cm:
            assert_login_duration(50000)
        self.assertEqual(cm.exception.rule_id, 'BR-09')

    def test_flag_low_occupancy(self):
        flags = flag_for_review({'occupancy': 0.30, 'aux_ratio': 0.10})
        self.assertTrue(any('LOW_OCCUPANCY' in f for f in flags))

    def test_flag_high_aux(self):
        flags = flag_for_review({'occupancy': 0.60, 'aux_ratio': 0.40})
        self.assertTrue(any('HIGH_AUX' in f for f in flags))

if __name__ == '__main__':
    unittest.main()