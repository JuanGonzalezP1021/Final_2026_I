from __future__ import annotations
from statistics import mean, stdev
from .base import Forecaster, ForecastResult

class MovingAverageForecaster(Forecaster):
    def __init__(self, window: int = 7):
        self.window = window

    def fit_predict(self, series, horizon):
        if len(series) < self.window:
            raise ValueError('series too short for MA window')
        errors = []
        for i in range(self.window, len(series)):
            forecast = mean(series[i-self.window:i])
            errors.append(abs(series[i] - forecast))
        mae = mean(errors) if errors else 0.0
        last_mean = mean(series[-self.window:])
        sd = stdev(series[-self.window:]) if self.window > 1 else 0
        preds = [last_mean] * horizon
        low  = [p - 1.96*sd for p in preds]
        high = [p + 1.96*sd for p in preds]
        return ForecastResult(f'MA-{self.window}', horizon,
                              preds, mae, low, high)
