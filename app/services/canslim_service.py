def build_canslim(history, info, rsi, price, ma50, ma200):
    latest_high_52w = float(history["High"].rolling(window=252).max().iloc[-1])
    latest_volume = float(history["Volume"].iloc[-1])
    avg_volume_20 = float(history["Volume"].rolling(window=20).mean().iloc[-1])

    roe = float(info.get("roe", 0) or 0)
    earnings_growth = float(info.get("earnings_growth", 0) or 0)

    near_high = bool(price >= latest_high_52w * 0.9)
    volume_breakout = bool(latest_volume > avg_volume_20 * 1.3)
    uptrend = bool(price > ma50 > ma200)

    items = [
        {
            "key": "C",
            "title": "Current Earnings",
            "label": "분기 실적 성장",
            "passed": bool(earnings_growth > 0.25),
            "description": "최근 이익 성장률이 25% 이상이면 긍정적으로 봅니다.",
        },
        {
            "key": "A",
            "title": "Annual Earnings",
            "label": "ROE 수익성",
            "passed": bool(roe > 0.17),
            "description": "ROE가 17% 이상이면 우수한 수익성으로 판단합니다.",
        },
        {
            "key": "N",
            "title": "New High",
            "label": "52주 신고가 근접",
            "passed": near_high,
            "description": "현재가가 52주 고점의 90% 이상이면 주도주 가능성이 있습니다.",
        },
        {
            "key": "S",
            "title": "Supply Demand",
            "label": "거래량 돌파",
            "passed": volume_breakout,
            "description": "최근 거래량이 20일 평균보다 30% 이상 높으면 수급 유입으로 봅니다.",
        },
        {
            "key": "L",
            "title": "Leader",
            "label": "시장 주도주",
            "passed": bool(rsi >= 50 and uptrend),
            "description": "RSI 50 이상이고 중장기 상승 추세면 상대적 강세로 봅니다.",
        },
        {
            "key": "I",
            "title": "Institutional",
            "label": "기관 수급",
            "passed": bool(volume_breakout or uptrend),
            "description": "기관 수급 데이터는 추후 연동 예정이며 현재는 거래량과 추세로 대체합니다.",
        },
        {
            "key": "M",
            "title": "Market",
            "label": "시장 방향",
            "passed": uptrend,
            "description": "현재가가 MA50과 MA200 위에 있으면 시장 방향을 긍정적으로 봅니다.",
        },
    ]

    passed_count = int(sum(1 for item in items if item["passed"]))
    total_count = int(len(items))
    score = int(round((passed_count / total_count) * 100))

    return {
        "score": score,
        "passed_count": passed_count,
        "total_count": total_count,
        "items": items,
    }