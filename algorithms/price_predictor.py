"""
algorithms/price_predictor.py

Core Algorithm: Simple Linear Regression (Least Squares Method)
-----------------------------------------------------------------
Given a crop's recent daily mandi prices, this module fits a straight
line  y = m*x + c  through the data (x = day index, y = price) using
the closed-form least-squares solution, then uses that line to:

  1. Forecast tomorrow's expected price.
  2. Classify the trend as "rising", "falling", or "stable".
  3. Report a confidence measure (R-squared) so the farmer's answer
     can be caveated when the trend is noisy/unclear.

Why Linear Regression (and not a heavier model):
  - Mandi price series over a short window (7-14 days) is close to
    linear in the short term; a heavier model (ARIMA/LSTM) needs far
    more historical data and compute than a phone-IVR response budget
    (< 4 seconds) allows.
  - It is fully explainable: the slope directly answers "is the price
    going up or down, and by how much per day?" - which is exactly
    the question a farmer is asking.
  - It is cheap enough to compute per-call in milliseconds on a
    single CPU core, which matters because this runs synchronously
    inside a live phone call.

No external ML library is used for the core math - it is implemented
directly using the normal equations, so the algorithm itself is fully
visible and explainable in this file.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PricePrediction:
    slope: float                # price change per day (INR/quintal/day)
    intercept: float
    predicted_next_price: float
    r_squared: float            # goodness of fit, 0..1
    trend: str                  # "rising" | "falling" | "stable"
    confidence: str              # "high" | "medium" | "low"


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def fit_linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Fits y = m*x + c using the least-squares closed-form solution:

        m = sum((x_i - x_mean) * (y_i - y_mean)) / sum((x_i - x_mean)^2)
        c = y_mean - m * x_mean

    This minimizes the sum of squared vertical distances between the
    fitted line and the actual price points.
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points to fit a trend line")

    x_mean = _mean(x)
    y_mean = _mean(y)

    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        # all x identical - degenerate case, flat line at mean price
        return 0.0, y_mean

    m = numerator / denominator
    c = y_mean - m * x_mean
    return m, c


def r_squared(x: List[float], y: List[float], m: float, c: float) -> float:
    """
    Coefficient of determination: how much of the price variance is
    explained by the fitted trend line. 1.0 = perfect fit, 0 = no
    predictive value at all.
    """
    y_mean = _mean(y)
    ss_total = sum((yi - y_mean) ** 2 for yi in y)
    if ss_total == 0:
        return 1.0
    ss_residual = sum((y[i] - (m * x[i] + c)) ** 2 for i in range(len(x)))
    return max(0.0, 1 - (ss_residual / ss_total))


def classify_trend(slope: float, avg_price: float) -> str:
    """
    A slope is only meaningfully "rising" or "falling" if the daily
    change is non-trivial relative to the price itself. We use a
    0.15% of average-price-per-day threshold to avoid calling tiny
    noise a "trend".
    """
    threshold = 0.0015 * avg_price
    if slope > threshold:
        return "rising"
    elif slope < -threshold:
        return "falling"
    return "stable"


def confidence_label(r2: float) -> str:
    if r2 >= 0.6:
        return "high"
    elif r2 >= 0.3:
        return "medium"
    return "low"


def predict_price_trend(price_history: List[float]) -> PricePrediction:
    """
    Main entry point. price_history must be ordered oldest -> newest,
    e.g. the last 7-14 days of mandi prices for one crop at one market.
    """
    if len(price_history) < 3:
        raise ValueError("At least 3 days of price history are recommended for a reliable trend")

    x = list(range(len(price_history)))       # day indices: 0, 1, 2, ...
    y = price_history

    m, c = fit_linear_regression(x, y)
    r2 = r_squared(x, y, m, c)

    next_day_index = len(price_history)       # tomorrow
    predicted_next_price = m * next_day_index + c

    avg_price = _mean(y)
    trend = classify_trend(m, avg_price)
    confidence = confidence_label(r2)

    return PricePrediction(
        slope=round(m, 2),
        intercept=round(c, 2),
        predicted_next_price=round(predicted_next_price, 2),
        r_squared=round(r2, 3),
        trend=trend,
        confidence=confidence,
    )


if __name__ == "__main__":
    # quick manual sanity check
    sample = [1800, 1815, 1832, 1828, 1850, 1861, 1875]
    result = predict_price_trend(sample)
    print(result)
