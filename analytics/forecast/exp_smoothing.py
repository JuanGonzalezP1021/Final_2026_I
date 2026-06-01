from __future__ import annotations
from statistics import mean
from .base import Forecaster, ForecastResult

class ExponentialSmoothingForecaster(Forecaster):
    def __init__(self, alpha: float = 0.3):
        if not 0 < alpha < 1:
            raise ValueError('alpha must be in (0, 1)')
        self.alpha = alpha

    def fit_predict(self, series, horizon):
        s = [series[0]]
        for t in range(1, len(series)):
            s.append(self.alpha * series[t] + (1 - self.alpha) * s[-1])
        errors = [abs(series[i] - s[i-1]) for i in range(1, len(series))]
        mae  = mean(errors) if errors else 0
        last = s[-1]
        preds = [last] * horizon
        band  = 1.96 * mae
        low   = [p - band for p in preds]
        high  = [p + band for p in preds]
        return ForecastResult(f'ExpSmooth(a={self.alpha})',
                              horizon, preds, mae, low, high)
