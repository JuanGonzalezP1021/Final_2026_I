import unittest
from datetime import date
from domain.models.agent import Agent
from domain.exceptions.custom_exceptions import ValidationError

VALID = dict(
    agent_id='Agent0001',
    team_manager='TL1',
    active_date='2025-01-01',
    days_range='0-30',
    tenurity='New Hire'
)

class TestAgentModel(unittest.TestCase):
    def test_valid(self):
        a = Agent(**VALID)
        self.assertEqual(a.agent_id, 'Agent0001')

    def test_bad_id_prefix(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'agent_id': 'XYZ0001'})

    def test_bad_id_suffix(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'agent_id': 'AgentABCD'})

    def test_bad_tl_prefix(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'team_manager': 'Manager1'})

    def test_bad_date_format(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'active_date': '01-01-2025'})

    def test_bad_tenurity(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'tenurity': 'Senior'})

    def test_bad_days_range(self):
        with self.assertRaises(ValidationError):
            Agent(**{**VALID, 'days_range': '0-100'})

    def test_roundtrip(self):
        a = Agent(**VALID)
        self.assertEqual(Agent.from_dict(a.to_dict()).to_dict(), a.to_dict())

    def test_days_in_company(self):
        a = Agent(**VALID)
        self.assertGreaterEqual(
            a.days_in_company(reference=date(2025, 1, 31)), 30
        )

    def test_to_dict_keys(self):
        a = Agent(**VALID)
        self.assertEqual(set(a.to_dict()), set(VALID))