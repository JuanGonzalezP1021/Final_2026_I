from __future__ import annotations
from collections import defaultdict
from statistics import mean
from domain.models.productivity import Productivity
from domain.rules.productivity_rules import (assert_state_sum,
    assert_login_duration, flag_for_review)
from infrastructure.persistence.productivity_repository import (
    ProductivityRepository)
from infrastructure.persistence.agent_repository import AgentRepository
from infrastructure.services.notification import default_notifier
from analytics.kpis.productivity_kpis import ProductivityKPI
from analytics.forecast.exp_smoothing import ExponentialSmoothingForecaster
from domain.exceptions.custom_exceptions import IntegrityError, NotFoundError

class ProductivityController:
    def __init__(self):
        self.repo     = ProductivityRepository()
        self.agents   = AgentRepository()
        self.notifier = default_notifier()

    def create(self, data: dict) -> Productivity:
        if not self.agents.find_by_key(data['agent_id']):
            raise IntegrityError(f"agent {data['agent_id']} does not exist")
        assert_login_duration(data['login_duration'])
        assert_state_sum(data)
        prod   = Productivity(**data)
        record = prod.to_dict()
        record['review_flags'] = flag_for_review(record)
        self.repo.insert(record)
        self.notifier.notify('CREATE', 'Productivity', record)
        return prod

    def read(self, record_id: str) -> Productivity:
        d = self.repo.find_by_key(record_id)
        if not d:
            raise NotFoundError('Productivity', record_id)
        return Productivity.from_dict(d)

    def update(self, record_id, patch: dict) -> Productivity:
        existing = self.read(record_id).to_dict()
        merged   = {**existing, **patch}
        assert_state_sum(merged)
        prod   = Productivity.from_dict(merged)
        record = prod.to_dict()
        record['review_flags'] = flag_for_review(record)
        self.repo.update(record_id, record)
        self.notifier.notify('UPDATE', 'Productivity', record)
        return prod

    def delete(self, record_id: str) -> None:
        self.read(record_id)
        self.repo.delete(record_id)
        self.notifier.notify('DELETE', 'Productivity',
                             {'record_id': record_id})

    def kpis(self) -> dict:
        k = ProductivityKPI(self.repo.find_all())
        return {
            'avg_occupancy': round(k.avg_occupancy(), 3),
            'distribution':  k.occupancy_distribution(),
        }

    def forecast_occupancy_for_tl(self, team_manager: str,
                                   horizon: int = 7) -> dict:
        agent_to_tl = {a['agent_id']: a['team_manager']
                       for a in self.agents.find_all()}
        daily = defaultdict(list)
        for r in self.repo.find_all():
            if agent_to_tl.get(r['agent_id']) == team_manager:
                daily[r['date']].append(r['occupancy'])
        if len(daily) < 5:
            return {'error': 'not enough history'}
        series = [mean(daily[d]) for d in sorted(daily)]
        result = ExponentialSmoothingForecaster(
            alpha=0.3).fit_predict(series, horizon)
        return {
            'tl':             team_manager,
            'method':         result.method,
            'predictions':    [round(p, 3) for p in result.predictions],
            'mae':            round(result.mae, 3),
            'history_points': len(series),
        }