from __future__ import annotations
import unittest
from domain.models.productivity import Productivity
from domain.exceptions.custom_exceptions import ValidationError

VALID = dict(agent_id='Agent0001', date='2025-05-01',
             aux_duration=4000, break_1=1800, break_2=0, break_3=0,
             email_duration=0, lunch_duration=2600, meeting_duration=0,
             tech_issue_duration=0, personal_duration=0, task_duration=0,
             training_duration=0, available_duration=16000,
             busy_duration=11000, login_duration=32400)

class TestProductivityModel(unittest.TestCase):

    def test_valid(self):
        p = Productivity(**VALID)
        self.assertEqual(p.agent_id, 'Agent0001')

    def test_negative_busy(self):
        with self.assertRaises(ValidationError):
            Productivity(**{**VALID, 'busy_duration': -1})

    def test_bad_date(self):
        with self.assertRaises(ValidationError):
            Productivity(**{**VALID, 'date': 'May 1 2025'})

    def test_occupancy_formula(self):
        p = Productivity(**VALID)
        self.assertAlmostEqual(p.occupancy, 11000/32400, places=4)

    def test_utilization_formula(self):
        p = Productivity(**VALID)
        self.assertAlmostEqual(p.utilization, 27000/32400, places=4)

    def test_aux_ratio_formula(self):
        p = Productivity(**VALID)
        self.assertAlmostEqual(p.aux_ratio, 4000/32400, places=4)

    def test_score_range(self):
        p = Productivity(**VALID)
        self.assertGreaterEqual(p.productivity_score(), 0)
        self.assertLessEqual(p.productivity_score(), 100)

    def test_zero_login_safe(self):
        p = Productivity(**{**VALID, 'busy_duration': 0,
                            'available_duration': 0,
                            'aux_duration': 0, 'login_duration': 0})
        self.assertEqual(p.occupancy, 0.0)
        self.assertEqual(p.utilization, 0.0)

    def test_roundtrip(self):
        p = Productivity(**VALID)
        self.assertAlmostEqual(
            Productivity.from_dict(p.to_dict()).occupancy, p.occupancy)

    def test_score_higher_for_better_metrics(self):
        good = Productivity(**{**VALID, 'busy_duration': 25000,
                               'available_duration': 5000,
                               'aux_duration': 1000})
        bad  = Productivity(**{**VALID, 'busy_duration': 5000,
                               'available_duration': 5000,
                               'aux_duration': 20000})
        self.assertGreater(good.productivity_score(),
                           bad.productivity_score())

if __name__ == '__main__':
    unittest.main()