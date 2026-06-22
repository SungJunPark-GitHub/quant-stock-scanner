import math


def safe_number(value, default=0.0):
    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number
    except Exception:
        return default


def calculate_score(
    rsi: float,
    price: float,
    ma20: float,
    ma50: float,
    ma200: float,
    macd_status: str,
    canslim_score: int,
    high_52w: float,
    volume_ratio: float,
    atr: float,
    momentum_3m: float = 0.0,
    momentum_6m: float = 0.0,
    moat_bonus: float = 0.0,
) -> int:
    price = safe_number(price)
    canslim_score = safe_number(canslim_score)
    moat_bonus = safe_number(moat_bonus)

    if price <= 0:
        return 0

    canslim_base = max(0, min(90, canslim_score * 0.9))
    moat_bonus = max(0, min(10, moat_bonus))
    score = canslim_base + moat_bonus

    return max(0, min(100, int(round(score))))


def get_signal(score: int):
    if score >= 82:
        return "매수관심", "green"

    if score >= 64:
        return "관망우세", "blue"

    if score >= 40:
        return "중립", "yellow"

    return "주의", "red"
