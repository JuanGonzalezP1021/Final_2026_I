from domain.models.contact import Contact
from domain.rules.contact_rules import (
    assert_aht_in_range,
    assert_tx_volume,
    assert_missed_threshold
)
from infrastructure.persistence.contact_repository import ContactRepository
from infrastructure.persistence.agent_repository import AgentRepository
from infrastructure.services.notification import default_notifier
from domain.exceptions.custom_exceptions import (
    NotFoundError,
    IntegrityError
)
from analytics.kpis.contact_kpis import ContactKPICalculator
from analytics.forecast.moving_average import MovingAverageForecaster
from analytics.forecast.linear_regression import (
    LinearRegressionForecaster
)

class ContactController:
    def __init__(self):
        self.repo = ContactRepository()
        self.agents = AgentRepository()
        self.notifier = default_notifier()

    def create(self, data: dict) -> Contact:
        # FK / integrity
        if not self.agents.find_by_key(data['agent_id']):
            raise IntegrityError(f"agent {data['agent_id']} does not exist")

        # BR-05
        existing = [
            c for c in self.repo.find_all()
            if c['agent_id'] == data['agent_id']
            and c['date'] == data['date']
        ]
        daily_tx = sum(c['inbound_tx'] + c['outbound_tx'] for c in existing)
        assert_tx_volume(
            daily_tx,
            data['inbound_tx'] + data['outbound_tx']
        )

        # BR-06
        daily_missed = sum(c['missed_contacts'] for c in existing)
        assert_missed_threshold(
            daily_missed + data.get('missed_contacts', 0)
        )

        # Build entity
        contact = Contact(**data)

        # BR-04
        kpi = ContactKPICalculator(self.repo.find_all())
        threshold = kpi.aht_outlier_threshold(contact.channel)
        if contact.aht > threshold:
            from domain.exceptions.custom_exceptions import BusinessRuleError
            raise BusinessRuleError(
                'BR-04',
                f'AHT {contact.aht:.0f} > threshold {threshold:.0f}'
            )

        self.repo.insert(contact.to_dict())
        self.notifier.notify('CREATE', 'Contact', contact.to_dict())
        return contact

    # ... read / update / delete follow the same pattern ...

    def kpis(self) -> dict:
        k = ContactKPICalculator(self.repo.find_all())
        return {
            'aht_overall': round(k.aht(), 1),
            'aht_by_channel': {
                ch: round(v, 1) for ch, v in k.aht_by_channel().items()
            },
        }

    def forecast_volume(self, channel: str, horizon: int = 7) -> dict:
        """Daily contact volume per channel, next `horizon` days."""
        from collections import defaultdict
        per_day = defaultdict(int)
        for c in self.repo.find_all():
            if c['channel'] == channel:
                per_day[c['date']] += c['inbound_tx'] + c['outbound_tx']

        series = [per_day[d] for d in sorted(per_day)]
        ma = MovingAverageForecaster(window=7).fit_predict(series, horizon)
        lr = LinearRegressionForecaster().fit_predict(series, horizon)
        
        best = min((ma, lr), key=lambda r: r.mae)
        
        return {
            'channel': channel,
            'history': series,
            'best_method': best.method,
            'predictions': [round(p, 1) for p in best.predictions],
            'mae': round(best.mae, 2),
            'confidence_low': [round(x, 1) for x in best.confidence_low],
            'confidence_high': [round(x, 1) for x in best.confidence_high]
        }