from dataclasses import dataclass, asdict
from datetime import date, datetime
from domain.exceptions.custom_exceptions import ValidationError

VALID_TENURITIES = ('New Hire', 'Early Tenure', 'Established', 'Experienced')
VALID_DAYS_RANGES = ('0-30', '31-89', '90-149', '150+')

@dataclass
class Agent:
    agent_id: str
    team_manager: str
    active_date: str  # ISO YYYY-MM-DD
    days_range: str
    tenurity: str

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not (self.agent_id.startswith('Agent') and self.agent_id[5:].isdigit()):
            raise ValidationError('agent_id', 'must match AgentNNNN pattern')
        
        if not self.team_manager.startswith('TL'):
            raise ValidationError('team_manager', 'must start with TL')
        
        try:
            datetime.strptime(self.active_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('active_date', 'expected YYYY-MM-DD')
        
        if self.tenurity not in VALID_TENURITIES:
            raise ValidationError('tenurity', f'must be one of {VALID_TENURITIES}')
        
        if self.days_range not in VALID_DAYS_RANGES:
            raise ValidationError('days_range', f'must be one of {VALID_DAYS_RANGES}')

    def days_in_company(self, reference: date = None) -> int:
        ref = reference or date.today()
        start = datetime.strptime(self.active_date, '%Y-%m-%d').date()
        return (ref - start).days

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Agent':
        return cls(**data)