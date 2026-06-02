import unittest
from datetime import date, timedelta
from domain.rules.agent_rules import (
    derive_tenurity,
    assert_tl_capacity,
    assert_can_deactivate
)
from domain.exceptions.custom_exceptions import BusinessRuleError

TODAY = date(2025, 6, 1)

def ago(days):
    return (TODAY - timedelta(days=days)).isoformat()

class TestAgentRules(unittest.TestCase):
    def test_tl_capacity_below_limit(self):
        assert_tl_capacity('TL1', 14)  # no raise

    def test_tl_capacity_at_limit_raises(self):
        with self.assertRaises(BusinessRuleError) as cm:
            assert_tl_capacity('TL1', 15)
        self.assertEqual(cm.exception.rule_id, 'BR-01')

    def test_tenurity_buckets(self):
        cases = [
            (0, 'New Hire'), (30, 'New Hire'),
            (31, 'Early Tenure'), (89, 'Early Tenure'),
            (90, 'Established'), (149, 'Established'),
            (150, 'Experienced')
        ]
        for days, expected in cases:
            t, _ = derive_tenurity(ago(days), ref=TODAY)
            self.assertEqual(t, expected, f'failed at day {days}')

    def test_can_deactivate_clean(self):
        assert_can_deactivate('Agent0001', False)  # no raise

    def test_can_deactivate_blocked(self):
        with self.assertRaises(BusinessRuleError) as cm:
            assert_can_deactivate('Agent0001', True)
        self.assertEqual(cm.exception.rule_id, 'BR-03')

    def test_tenurity_range_string(self):
        _, rng = derive_tenurity(ago(60), ref=TODAY)
        self.assertEqual(rng, '31-89')