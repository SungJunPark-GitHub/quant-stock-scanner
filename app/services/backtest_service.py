def run_simple_backtest(history, atr):
    """
    단순 백테스트 v1
    - 최근 1년 데이터 사용
    - 20일 이동평균이 50일 이동평균 위에 있으면 매수 후보
    - 진입 후 ATR 기준 손절/익절 확인
    """

    df = history.copy()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()

    trades = []

    for i in range(60, len(df) - 10):
        row = df.iloc[i]

        if row["MA20"] <= row["MA50"]:
            continue

        entry_price = float(row["Close"])
        stop_price = entry_price - atr * 1.5
        take_profit = entry_price + atr * 2

        exit_price = None
        result = None

        future = df.iloc[i + 1:i + 11]

        for _, future_row in future.iterrows():
            low = float(future_row["Low"])
            high = float(future_row["High"])
            close = float(future_row["Close"])

            if low <= stop_price:
                exit_price = stop_price
                result = "LOSS"
                break

            if high >= take_profit:
                exit_price = take_profit
                result = "WIN"
                break

            exit_price = close
            result = "HOLD"

        if exit_price is None:
            continue

        profit_rate = ((exit_price - entry_price) / entry_price) * 100

        trades.append({
            "entry": round(entry_price, 2),
            "exit": round(exit_price, 2),
            "profit_rate": round(profit_rate, 2),
            "result": result,
        })

    if not trades:
        return {
            "trade_count": 0,
            "win_rate": 0,
            "avg_return": 0,
            "total_return": 0,
            "mdd": 0,
        }

    wins = [trade for trade in trades if trade["profit_rate"] > 0]
    returns = [trade["profit_rate"] for trade in trades]

    equity = 100
    peak = 100
    mdd = 0

    for r in returns:
        equity *= (1 + r / 100)
        peak = max(peak, equity)
        drawdown = ((equity - peak) / peak) * 100
        mdd = min(mdd, drawdown)

    return {
        "trade_count": len(trades),
        "win_rate": round((len(wins) / len(trades)) * 100, 2),
        "avg_return": round(sum(returns) / len(returns), 2),
        "total_return": round(equity - 100, 2),
        "mdd": round(mdd, 2),
    }