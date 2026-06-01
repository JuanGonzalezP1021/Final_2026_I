from __future__ import annotations
from statistics import mean
from math import sqrt
from .base import Forecaster, ForecastResult

class LinearRegressionForecaster(Forecaster):
    def fit_predict(self, series, horizon):
        n = len(series)
        if n < 3:
            raise ValueError('need at least 3 points')
        xs = list(range(n))
        x_mean = mean(xs)
        y_mean = mean(series)
        num = sum((xs[i] - x_mean) * (series[i] - y_mean) for i in range(n))
        den = sum((x - x_mean) ** 2 for x in xs)
        slope = num / den if den else 0
        intercept = y_mean - slope * x_mean
        residuals = [series[i] - (intercept + slope * i) for i in range(n)]
        mae = mean(abs(r) for r in residuals)
        sse = sum(r**2 for r in residuals)
        see = sqrt(sse / (n - 2)) if n > 2 else 0
        preds = [intercept + slope * (n + h) for h in range(horizon)]
        low  = [p - 1.96 * see for p in preds]
        high = [p + 1.96 * see for p in preds]
        return ForecastResult('LinReg', horizon, preds, mae, low, high)
