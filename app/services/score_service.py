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
    if rsi < 30:
        score += 14
    elif rsi < 40:
        score += 8
    elif rsi > 75:
        score -= 14
    elif rsi > 70:
        score -= 8

    # MA trend
    if ma20 > ma50 > ma200:
        score += 14
    elif price < ma50:
        score -= 8

    if price > ma20:
        score += 5

    # MACD
    if macd_status == "골든크로스":
        score += 6
    elif macd_status == "상승 우위":
        score += 3
    elif macd_status == "데드크로스":
        score -= 6
    elif macd_status == "하락 우위":
        score -= 3

    # CAN SLIM
    if canslim_score >= 70:
        score += 10
    elif canslim_score >= 50:
        score += 5
    elif canslim_score <= 30:
        score -= 5

    # 52-week high proximity
    if high_52w > 0:
        high_gap = price / high_52w

        if high_gap >= 0.95:
            score += 8
        elif high_gap >= 0.9:
            score += 5
        elif high_gap < 0.75:
            score -= 5

    # Volume breakout
    if volume_ratio >= 1.5:
        score += 7
    elif volume_ratio >= 1.2:
        score += 4

    # ATR risk
    atr_ratio = atr / price if price else 0

    if atr_ratio >= 0.08:
        score -= 8
    elif atr_ratio >= 0.05:
        score -= 4
    elif atr_ratio <= 0.025:
        score += 3

    # Target upside
    if target_change >= 20:
        score += 5
    elif target_change >= 10:
        score += 3
    elif target_change < 0:
        score -= 6

    return max(0, min(100, int(score)))


def get_signal(score: int):
    if score >= 75:
        return "GREEN", "green"
    if score < 30:
        return "RED", "red"
    return "YELLOW", "yellow"