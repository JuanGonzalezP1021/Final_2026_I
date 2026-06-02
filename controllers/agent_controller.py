from datetime import date, datetime, timedelta

from domain.models.agent import Agent
from domain.rules.agent_rules import (
    assert_tl_capacity,
    assert_can_deactivate,
    derive_tenurity
)
from infrastructure.persistence.agent_repository import AgentRepository
from infrastructure.persistence.contact_repository import ContactRepository
from infrastructure.persistence.productivity_repository import (
    ProductivityRepository
)
from infrastructure.services.notification import default_notifier
from domain.exceptions.custom_exceptions import DuplicateError, NotFoundError
from analytics.kpis.agent_kpis import AgentKPI
from analytics.forecast.linear_regression import LinearRegressionForecaster


class AgentController:
    def __init__(self):
        self.repo = AgentRepository()
        self.contacts = ContactRepository()
        self.prod = ProductivityRepository()
        self.notifier = default_notifier()

    def create(self, data: dict) -> Agent:
        if self.repo.find_by_key(data['agent_id']):
            raise DuplicateError('Agent', data['agent_id'])

        ten, rng = derive_tenurity(data['active_date'])
        data['tenurity'] = ten
        data['days_range'] = rng

        current = sum(
            1 for a in self.repo.find_all()
            if a['team_manager'] == data['team_manager']
        )
        assert_tl_capacity(data['team_manager'], current)  # BR-01

        agent = Agent(**data)
        self.repo.insert(agent.to_dict())
        self.notifier.notify('CREATE', 'Agent', agent.to_dict())
        return agent

    def read(self, agent_id: str) -> Agent:
        data = self.repo.find_by_key(agent_id)
        if not data:
            raise NotFoundError('Agent', agent_id)
        return Agent.from_dict(data)

    def update(self, agent_id, patch: dict) -> Agent:
        existing = self.read(agent_id)
        merged = {**existing.to_dict(), **patch}
        if 'active_date' in patch:
            ten, rng = derive_tenurity(merged['active_date'])
            merged['tenurity'] = ten
            merged['days_range'] = rng
        else:
            merged['tenurity'] = existing.tenurity
            merged['days_range'] = existing.days_range

        agent = Agent(**merged)
        self.repo.update(agent_id, agent.to_dict())
        self.notifier.notify('UPDATE', 'Agent', agent.to_dict())
        return agent

    def delete(self, agent_id: str) -> None:
        self.read(agent_id)
        cutoff = (date.today() - timedelta(days=7)).isoformat()

        recent = (
            any(c['agent_id'] == agent_id and c['date'] >= cutoff
                for c in self.contacts.find_all()) or
            any(p['agent_id'] == agent_id and p['date'] >= cutoff
                for p in self.prod.find_all())
        )
        assert_can_deactivate(agent_id, recent)  # BR-03

        self.repo.delete(agent_id)
        self.notifier.notify('DELETE', 'Agent', {'agent_id': agent_id})

    def kpis(self) -> dict:
        k = AgentKPI(self.repo.find_all())
        return {
            'headcount': k.headcount(),
            'tenurity_mix': k.tenurity_mix(),
            'attrition_risk': k.attrition_risk(),
            'tls_over_capacity': k.tls_over_capacity(),
        }

    def forecast_established_next_month(self) -> dict:
        agents = self.repo.find_all()
        today = date.today()
        series = []

        for offset in range(60, 0, -1):
            ref = today - timedelta(days=offset)
            count = sum(
                1 for a in agents
                if (ref - datetime.strptime(a['active_date'], '%Y-%m-%d').date()).days == 90
            )
            series.append(count)

        result = LinearRegressionForecaster().fit_predict(series, horizon=30)
        return {
            'method': result.method,
            'mae': round(result.mae, 2),
            'total_predicted': round(sum(result.predictions), 1),
        }