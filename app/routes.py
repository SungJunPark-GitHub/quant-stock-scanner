from flask import Blueprint, render_template

from app.services.market_service import MAG7_TICKERS, get_stock_history, get_stock_info
from app.services.indicator_service import calculate_rsi, calculate_ma, calculate_atr
from app.services.score_service import calculate_score, get_signal
from app.services.canslim_service import build_canslim

main = Blueprint("main", __name__)


def build_chart_data(history):
    def make_chart(days):
        chart_history = history.tail(days)

        labels = [
            index.strftime("%m-%d")
            for index in chart_history.index
        ]

        prices = [
            round(float(price), 2)
            for price in chart_history["Close"].tolist()
        ]

        ma20 = [
            None if value != value else round(float(value), 2)
            for value in chart_history["Close"].rolling(window=20).mean().tolist()
        ]

        ma50 = [
            None if value != value else round(float(value), 2)
            for value in chart_history["Close"].rolling(window=50).mean().tolist()
        ]

        return {
            "labels": labels,
            "prices": prices,
            "ma20": ma20,
            "ma50": ma50,
        }

    return {
        "1M": make_chart(22),
        "3M": make_chart(66),
        "6M": make_chart(120),
        "1Y": make_chart(252),
    }


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

        canslim = build_canslim(
            history=history,
            info=info,
            rsi=rsi,
            price=price,
            ma50=ma50,
            ma200=ma200,
        )

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
            "canslim": canslim,
            "chart": build_chart_data(history),
            "reason": [
                f"RSI {rsi}",
                f"MA20 {ma20}",
                f"ATR {atr}",
                f"CAN {canslim['passed_count']}/7",
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