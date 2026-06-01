from __future__ import annotations
import unittest
from analytics.forecast.moving_average import MovingAverageForecaster
from analytics.forecast.linear_regression import LinearRegressionForecaster
from analytics.forecast.exp_smoothing import ExponentialSmoothingForecaster

class TestForecasters(unittest.TestCase):

    def test_ma_flat_series(self):
        r = MovingAverageForecaster(window=3).fit_predict([10]*10, 5)
        self.assertAlmostEqual(r.predictions[0], 10.0)
        self.assertEqual(r.mae, 0.0)

    def test_linreg_perfect_trend(self):
        r = LinearRegressionForecaster().fit_predict([1,2,3,4,5,6,7], 3)
        self.assertAlmostEqual(r.predictions[0], 8.0)
        self.assertAlmostEqual(r.predictions[2], 10.0)
        self.assertAlmostEqual(r.mae, 0.0)

    def test_exp_smoothing_alpha_bounds(self):
        with self.assertRaises(ValueError):
            ExponentialSmoothingForecaster(alpha=0)
        with self.assertRaises(ValueError):
            ExponentialSmoothingForecaster(alpha=1)

    def test_ma_too_short_raises(self):
        with self.assertRaises(ValueError):
            MovingAverageForecaster(window=7).fit_predict([1,2,3], 2)

    def test_linreg_mae_nonnegative(self):
        r = LinearRegressionForecaster().fit_predict([3,1,4,1,5,9,2,6,5], 2)
        self.assertGreaterEqual(r.mae, 0)

    def test_ci_band_width(self):
        r = MovingAverageForecaster(window=5).fit_predict([10,12,11,9,13,11,12], 3)
        for lo, hi in zip(r.confidence_low, r.confidence_high):
            self.assertLess(lo, hi)

    def test_mae_lower_for_better_fit(self):
        series = list(range(1, 21))
        ma = MovingAverageForecaster(window=5).fit_predict(series, 3).mae
        lr = LinearRegressionForecaster().fit_predict(series, 3).mae
        self.assertLess(lr, ma)

    def test_horizon_respected(self):
        for cls, kw in [(MovingAverageForecaster, {"window": 3}),
                        (LinearRegressionForecaster, {}),
                        (ExponentialSmoothingForecaster, {})]:
            r = cls(**kw).fit_predict([1,2,3,4,5,6,7,8], 4)
            self.assertEqual(len(r.predictions), 4)

if __name__ == "__main__":
    unittest.main()
