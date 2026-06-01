from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ForecastResult:
    method: str
    horizon: int
    predictions: list[float]
    mae: float
    confidence_low: list[float]
    confidence_high: list[float]

class Forecaster(ABC):
    @abstractmethod
    def fit_predict(self, series: list[float], horizon: int) -> ForecastResult:
        ...
