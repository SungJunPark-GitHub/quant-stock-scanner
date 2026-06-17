from flask import Blueprint, render_template

from app.services.market_service import MAG7_TICKERS, get_stock_history, get_stock_info
from app.services.indicator_service import calculate_rsi, calculate_ma, calculate_atr
from app.services.score_service import calculate_score, get_signal

main = Blueprint("main", __name__)


def build_stock_data():
    stocks = []

    for index, ticker in enumerate(MAG7_TICKERS, start=1):
        history = get_stock_history(ticker)
        info = get_stock_info(ticker)

        if history is None:
            continue

        price = round(float(history["Close"].iloc[-1]), 2)
        prev_price = round(float(history["Close"].iloc[-2]), 2)
        change = round(((price - prev_price) / prev_price) * 100, 2)

        rsi = calculate_rsi(history)
        ma20 = calculate_ma(history, 20)
        ma50 = calculate_ma(history, 50)
        ma200 = calculate_ma(history, 200)
        atr = calculate_atr(history)

        score = calculate_score(rsi, price, ma20, ma50, ma200)
        signal, signal_type = get_signal(score)

        target = info["target"] if info["target"] else round(price + atr * 3, 2)
        target_change = round(((target - price) / price) * 100, 2)

        stocks.append({
            "rank": index,
            "ticker": ticker,
            "name": info["name"],
            "description": info["description"],
            "sector": "Mag 7",
            "score": score,
            "signal": signal,
            "signal_type": signal_type,
            "price": price,
            "change": change,
            "rsi": rsi,
            "target": round(float(target), 2),
            "target_change": target_change,
            "atr": atr,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "reason": [
                f"RSI {rsi}",
                f"MA20 {ma20}",
                f"ATR {atr}",
            ],
        })

    stocks.sort(key=lambda x: x["score"], reverse=True)

    for index, stock in enumerate(stocks, start=1):
        stock["rank"] = index

    return stocks


@main.route("/")
def index():
    stocks = build_stock_data()
    return render_template("index.html", stocks=stocks)