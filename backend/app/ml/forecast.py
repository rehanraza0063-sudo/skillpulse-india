"""
Prototype demand forecasting.

Method: ordinary least squares linear regression of demand on year (scikit-learn LinearRegression),
with an 80% prediction interval from the residual standard error and Student's t distribution.

Why this model: with only four yearly demo observations (2023-2026) anything more complex would be
over-fitting and would manufacture false accuracy. The model is explainable and every number can be
reproduced by hand. It is NOT validated against real labour-market data.
"""
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

INTERVAL = 0.80          # prediction interval coverage
MAX_CONFIDENCE = 0.95    # never display more than this - 4 data points cannot justify certainty


@dataclass
class ForecastPoint:
    year: int
    value: float
    lower: float
    upper: float
    confidence: float          # 0..0.95, 1 - (half interval / forecast)

    def as_dict(self):
        return {"year": self.year, "value": self.value, "lower": self.lower, "upper": self.upper,
                "confidence": self.confidence, "confidence_label": confidence_label(self.confidence)}


def confidence_label(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    if score >= 0.55:
        return "MEDIUM"
    return "LOW"


def linear_forecast(years: Sequence[int], values: Sequence[float], target_years: Sequence[int]):
    """Returns (list[ForecastPoint], model_info dict)."""
    x = np.asarray(years, dtype=float).reshape(-1, 1)
    y = np.asarray(values, dtype=float)
    n = len(y)
    model = LinearRegression().fit(x, y)
    fitted = model.predict(x)
    resid = y - fitted
    dof = max(n - 2, 1)
    s = float(np.sqrt((resid ** 2).sum() / dof))
    xbar = float(x.mean())
    sxx = float(((x - xbar) ** 2).sum())
    tcrit = float(stats.t.ppf(1 - (1 - INTERVAL) / 2, dof))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float((resid ** 2).sum()) / ss_tot if ss_tot > 0 else 1.0

    points = []
    for ty in target_years:
        pred = max(float(model.predict([[float(ty)]])[0]), 0.0)
        se = s * np.sqrt(1 + 1 / n + (ty - xbar) ** 2 / sxx)
        half = tcrit * float(se)
        score = max(0.0, 1.0 - half / max(pred, 1.0))
        points.append(ForecastPoint(int(ty), pred, max(pred - half, 0.0), pred + half, min(score, MAX_CONFIDENCE)))

    info = {
        "method": "Linear regression (OLS) of demand on year",
        "library": "scikit-learn LinearRegression + scipy.stats.t",
        "n_observations": n,
        "slope_per_year": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r_squared": r2,
        "residual_std": s,
        "interval": f"{int(INTERVAL * 100)}% prediction interval",
        "label": "Prototype Forecast",
        "limitations": (
            "Only four demo observations; assumes the recent linear trend continues. "
            "Interval reflects fit scatter only, not structural change. Requires validation with official datasets."
        ),
    }
    return points, info
