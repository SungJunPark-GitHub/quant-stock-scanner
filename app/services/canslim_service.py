import math


def safe_float(value, default=0.0):
    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number
    except Exception:
        return default


def build_canslim(history, info, rsi, price, ma50, ma200):
    high_window = history["High"].tail(252).dropna() if "High" in history else []
    clean_volume = history["Volume"].dropna() if "Volume" in history else []
    volume_window = history["Volume"].tail(20).dropna() if "Volume" in history else []
    latest_high_52w = safe_float(high_window.max() if len(high_window) else 0)
    latest_volume = safe_float(clean_volume.iloc[-1] if len(clean_volume) else 0)
    avg_volume_20 = safe_float(volume_window.mean() if len(volume_window) else 0)

    roe = float(info.get("roe", 0) or 0)
    earnings_growth = float(info.get("earnings_growth", 0) or 0)

    near_high = bool(latest_high_52w > 0 and price >= latest_high_52w * 0.9)
    volume_breakout = bool(avg_volume_20 > 0 and latest_volume > avg_volume_20 * 1.3)
    volume_ratio = latest_volume / avg_volume_20 if avg_volume_20 > 0 else 0
    uptrend = bool(price > ma50 > ma200)
    high_gap = price / latest_high_52w if latest_high_52w > 0 and price > 0 else 0

    def growth_score(value):
        if value >= 0.25:
            return 100
        if value >= 0.10:
            return 78
        if value > 0:
            return 58
        if value == 0:
            return 45
        return 25

    def roe_score(value):
        if value >= 0.25:
            return 100
        if value >= 0.17:
            return 82
        if value >= 0.10:
            return 64
        if value > 0:
            return 48
        return 35

    def high_score(value):
        if value >= 0.95:
            return 100
        if value >= 0.90:
            return 82
        if value >= 0.80:
            return 58
        if value >= 0.65:
            return 38
        return 22

    def volume_score(value):
        if value >= 1.5:
            return 100
        if value >= 1.3:
            return 85
        if value >= 1.1:
            return 68
        if value >= 0.8:
            return 48
        return 28

    def leader_score():
        if uptrend and 50 <= rsi <= 70:
            return 92
        if uptrend:
            return 76
        if price > ma200 and rsi >= 45:
            return 62
        if price > ma50:
            return 50
        return 32

    def institution_score():
        if volume_breakout and uptrend:
            return 92
        if volume_breakout:
            return 80
        if uptrend:
            return 66
        if volume_ratio >= 0.9:
            return 48
        return 30

    def market_score():
        if uptrend:
            return 90
        if price > ma200:
            return 62
        if price > ma50:
            return 50
        return 30

    items = [
        {
            "key": "C",
            "title": "Current Earnings",
            "label": "분기 실적 성장",
            "score": growth_score(earnings_growth),
            "description": "최근 이익 성장률을 구간별로 채점합니다.",
        },
        {
            "key": "A",
            "title": "Annual Earnings",
            "label": "ROE 수익성",
            "score": roe_score(roe),
            "description": "ROE가 높을수록 꾸준히 돈 버는 힘으로 봅니다.",
        },
        {
            "key": "N",
            "title": "New High",
            "label": "52주 신고가 근접",
            "score": high_score(high_gap),
            "description": "52주 고점에 가까울수록 시장의 관심이 살아있다고 봅니다.",
        },
        {
            "key": "S",
            "title": "Supply Demand",
            "label": "거래량 돌파",
            "score": volume_score(volume_ratio),
            "description": "20일 평균 대비 거래량이 붙는지 봅니다.",
        },
        {
            "key": "L",
            "title": "Leader",
            "label": "시장 주도주",
            "score": leader_score(),
            "description": "추세와 RSI가 같이 받쳐주는지 봅니다.",
        },
        {
            "key": "I",
            "title": "Institutional",
            "label": "기관 수급",
            "score": institution_score(),
            "description": "기관 수급은 현재 거래량과 추세로 대체 계산합니다.",
        },
        {
            "key": "M",
            "title": "Market",
            "label": "시장 방향",
            "score": market_score(),
            "description": "MA50·MA200 대비 위치로 시장 방향을 봅니다.",
        },
    ]

    for item in items:
        item["passed"] = item["score"] >= 70

    passed_count = int(sum(1 for item in items if item["passed"]))
    total_count = int(len(items))
    score = int(round(sum(item["score"] for item in items) / total_count))

    return {
        "score": score,
        "passed_count": passed_count,
        "total_count": total_count,
        "items": items,
    }
