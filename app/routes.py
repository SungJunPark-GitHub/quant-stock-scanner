from flask import Blueprint, render_template, Response, request
import csv
import io

from app.services.backtest_service import run_simple_backtest
from app.services.market_service import (
    get_market_tickers,
    get_stock_history,
    get_stock_info,
    get_extended_market_info,
)
from app.services.indicator_service import (
    calculate_rsi,
    calculate_ma,
    calculate_atr,
    calculate_macd,
    calculate_52w_high,
    calculate_volume_ratio,
)
from app.services.score_service import calculate_score, get_signal
from app.services.canslim_service import build_canslim
from app.services.news_service import get_news_sentiment

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


def build_stock_data(market="US"):
    stocks = []
    tickers = get_market_tickers(market)

    for index, ticker in enumerate(tickers, start=1):
        history = get_stock_history(ticker)
        info = get_stock_info(ticker, market)
        extended = get_extended_market_info(ticker)
        news = get_news_sentiment(ticker)

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
        backtest = run_simple_backtest(history, atr)
        macd = calculate_macd(history)
        high_52w = calculate_52w_high(history)
        volume_ratio = calculate_volume_ratio(history)

        canslim = build_canslim(
            history=history,
            info=info,
            rsi=rsi,
            price=price,
            ma50=ma50,
            ma200=ma200,
        )

        target = info["target"] if info["target"] else round(price + atr * 3, 2)
        target_change = round(((target - price) / price) * 100, 2)

        score = calculate_score(
            rsi=rsi,
            price=price,
            ma20=ma20,
            ma50=ma50,
            ma200=ma200,
            macd_status=macd["status"],
            canslim_score=canslim["score"],
            high_52w=high_52w,
            volume_ratio=volume_ratio,
            atr=atr,
            target_change=target_change,
        )
        signal, signal_type = get_signal(score)

        stocks.append({
            "rank": index,
            "ticker": ticker,
            "name": info["name"],
            "description": info["description"],
            "sector": info["sector"] if market == "SP500" else "Korea" if market == "KR" else "Mag 7",
            "score": score,
            "signal": signal,
            "signal_type": signal_type,
            "price": price,
            "change": change,
            "rsi": rsi,
            "rsi_status": "과매수" if rsi >= 70 else "과매도" if rsi <= 30 else "중립",
            "rsi_status_type": "red" if rsi >= 70 else "green" if rsi <= 30 else "yellow",
            "target": round(float(target), 2),
            "target_change": target_change,
            "atr": atr,
            "backtest": backtest,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "ma_status": "정배열" if ma20 > ma50 > ma200 else "비정배열",
            "ma_status_type": "green" if ma20 > ma50 > ma200 else "red",
            "macd": macd,
            "premarket_price": extended["premarket_price"],
            "premarket_change": extended["premarket_change"],
            "aftermarket_price": extended["aftermarket_price"],
            "aftermarket_change": extended["aftermarket_change"],
            "news": news,
            "high_52w": high_52w,
            "volume_ratio": volume_ratio,
            "canslim": canslim,
            "chart": build_chart_data(history),
            "reason": [
                f"RSI {rsi}",
                f"MACD {macd['status']}",
                f"거래량 {volume_ratio}x",
                f"CAN {canslim['passed_count']}/7",
                f"News {news['sentiment']}",
            ],
        })

    stocks.sort(key=lambda x: x["score"], reverse=True)

    for index, stock in enumerate(stocks, start=1):
        stock["rank"] = index

    return stocks


@main.route("/")
def index():
    market = request.args.get("market", "US")
    stocks = build_stock_data(market)
    return render_template("index.html", stocks=stocks, market=market)


@main.route("/export/csv")
def export_csv():
    market = request.args.get("market", "US")
    stocks = build_stock_data(market)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "순위",
        "티커",
        "종목명",
        "설명",
        "섹터",
        "점수",
        "시그널",
        "현재가",
        "등락률",
        "RSI",
        "RSI상태",
        "ATR",
        "MA20",
        "MA50",
        "MA200",
        "MA상태",
        "MACD",
        "MACD상태",
        "52주고가",
        "거래량비율",
        "목표가",
        "목표가괴리율",
        "CAN_SLIM",
    ])

    for stock in stocks:
        writer.writerow([
            stock["rank"],
            stock["ticker"],
            stock["name"],
            stock["description"],
            stock["sector"],
            stock["score"],
            stock["signal"],
            stock["price"],
            stock["change"],
            stock["rsi"],
            stock["rsi_status"],
            stock["atr"],
            stock["ma20"],
            stock["ma50"],
            stock["ma200"],
            stock["ma_status"],
            stock["macd"]["macd"],
            stock["macd"]["status"],
            stock["high_52w"],
            stock["volume_ratio"],
            stock["target"],
            stock["target_change"],
            f"{stock['canslim']['passed_count']}/{stock['canslim']['total_count']}",
        ])

    csv_data = "\ufeff" + output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=quant_stock_scanner.csv"
        },
    )