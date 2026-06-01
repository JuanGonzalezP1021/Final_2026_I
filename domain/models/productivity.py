from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid
from domain.exceptions.custom_exceptions import ValidationError

@dataclass
class Productivity:
    agent_id: str
    date: str
    aux_duration: int
    break_1: int
    break_2: int
    break_3: int
    email_duration: int
    lunch_duration: int
    meeting_duration: int
    tech_issue_duration: int
    personal_duration: int
    task_duration: int
    training_duration: int
    available_duration: int
    busy_duration: int
    login_duration: int
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self):
        self._validate()

    def _validate(self):
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("date", "expected YYYY-MM-DD")
        for f in ("aux_duration", "break_1", "break_2", "break_3",
                  "email_duration", "lunch_duration", "meeting_duration",
                  "tech_issue_duration", "personal_duration", "task_duration",
                  "training_duration", "available_duration",
                  "busy_duration", "login_duration"):
            if getattr(self, f) < 0:
                raise ValidationError(f, "must be >= 0")

    @property
    def occupancy(self) -> float:
        return (self.busy_duration / self.login_duration
                if self.login_duration else 0.0)

    @property
    def utilization(self) -> float:
        if not self.login_duration:
            return 0.0
        return ((self.busy_duration + self.available_duration)
                / self.login_duration)

    @property
    def aux_ratio(self) -> float:
        return (self.aux_duration / self.login_duration
                if self.login_duration else 0.0)

    def productivity_score(self) -> float:
        return round(
            (0.5 * self.occupancy
             + 0.3 * self.utilization
             + 0.2 * (1 - self.aux_ratio)) * 100, 1)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update({
            "occupancy":          round(self.occupancy, 3),
            "utilization":        round(self.utilization, 3),
            "aux_ratio":          round(self.aux_ratio, 3),
            "productivity_score": self.productivity_score(),
        })
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Productivity:
        clean = {k: v for k, v in data.items()
                 if k not in ("occupancy", "utilization",
                              "aux_ratio", "productivity_score")}
        return cls(**clean)
