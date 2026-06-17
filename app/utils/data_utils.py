import math
import pandas as pd


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        number = float(value)

        if math.isnan(number) or math.isinf(number) or pd.isna(number):
            return default

        return number
    except Exception:
        return default


def safe_round(value, digits=2, default=0.0):
    return round(safe_float(value, default), digits)


def safe_percent(numerator, denominator, digits=2, default=0.0):
    numerator = safe_float(numerator)
    denominator = safe_float(denominator)

    if denominator == 0:
        return default

    return round((numerator / denominator) * 100, digits)


def safe_price_from_history(history, default=0.0):
    try:
        price = history["Close"].dropna().iloc[-1]
        return safe_round(price, 2, default)
    except Exception:
        return default


def safe_prev_price_from_history(history, default=0.0):
    try:
        price = history["Close"].dropna().iloc[-2]
        return safe_round(price, 2, default)
    except Exception:
        return default