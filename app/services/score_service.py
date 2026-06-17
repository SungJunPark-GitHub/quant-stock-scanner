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
    target_change: float,
) -> int:
    score = 50

    # RSI
    if 40 <= rsi <= 60:
        score += 8
    elif 30 <= rsi < 40:
        score += 5
    elif 60 < rsi <= 70:
        score += 3
    elif rsi < 30:
        score += 2
    elif rsi > 75:
        score -= 12
    elif rsi > 70:
        score -= 7

    # MA trend
    if ma20 > ma50 > ma200:
        score += 16
    elif ma20 > ma50:
        score += 8
    elif price < ma50:
        score -= 8

    if price > ma20:
        score += 5

    # MACD
    if macd_status == "골든크로스":
        score += 8
    elif macd_status == "상승 우위":
        score += 5
    elif macd_status == "데드크로스":
        score -= 8
    elif macd_status == "하락 우위":
        score -= 4

    # CAN SLIM
    if canslim_score >= 70:
        score += 10
    elif canslim_score >= 50:
        score += 6
    elif canslim_score <= 30:
        score -= 5

    # 52-week high proximity
    if high_52w > 0 and price > 0:
        high_gap = price / high_52w

        if high_gap >= 0.95:
            score += 8
        elif high_gap >= 0.9:
            score += 5
        elif high_gap < 0.75:
            score -= 5

    # Volume breakout
    if volume_ratio >= 1.5:
        score += 8
    elif volume_ratio >= 1.2:
        score += 5
    elif volume_ratio < 0.7:
        score -= 2

    # ATR risk
    atr_ratio = atr / price if price else 0

    if atr_ratio >= 0.08:
        score -= 8
    elif atr_ratio >= 0.05:
        score -= 4
    elif 0 < atr_ratio <= 0.025:
        score += 3

    # Target upside
    if target_change >= 30:
        score += 8
    elif target_change >= 20:
        score += 6
    elif target_change >= 10:
        score += 4
    elif target_change < 0:
        score -= 6

    return max(0, min(100, int(score)))


def get_signal(score: int):
    if score >= 75:
        return "GREEN", "green"

    if score >= 60:
        return "BLUE", "blue"

    if score >= 45:
        return "YELLOW", "yellow"

    return "RED", "red"