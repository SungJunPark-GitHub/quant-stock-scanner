def calculate_score(rsi: float, price: float, ma20: float, ma50: float, ma200: float) -> int:
    score = 50

    if rsi < 30:
        score += 14
    elif rsi < 40:
        score += 8

    if ma20 > ma50 > ma200:
        score += 14

    if price > ma20:
        score += 6

    if rsi > 70:
        score -= 12

    return max(0, min(100, score))


def get_signal(score: int):
    if score >= 75:
        return "GREEN", "green"
    if score < 30:
        return "RED", "red"
    return "YELLOW", "yellow"