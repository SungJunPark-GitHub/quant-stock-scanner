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

from app.utils.data_utils import (
    safe_float,
    safe_round,
    safe_price_from_history,
    safe_prev_price_from_history,
)

from app.utils.grade_utils import get_grade, get_grade_type
from app.services.macro_service import get_market_overview


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


def build_reason_text(rsi, macd_status, volume_ratio, canslim, ma_status):
    reasons = []

    if ma_status == "정배열":
        reasons.append("추세 정배열")
    else:
        reasons.append("추세 확인 필요")

    if rsi >= 70:
        reasons.append("RSI 과열 주의")
    elif rsi <= 30:
        reasons.append("과매도 반등 후보")
    else:
        reasons.append("RSI 중립권")

    if "골든" in macd_status or "상승" in macd_status:
        reasons.append("MACD 상승 우위")
    else:
        reasons.append("MACD 약세")

    if volume_ratio >= 1.2:
        reasons.append("거래량 증가")
    else:
        reasons.append("거래량 보통")

    if canslim and canslim.get("passed_count", 0) >= 5:
        reasons.append("CAN SLIM 양호")
    else:
        reasons.append("성장 조건 확인")

    return reasons[:4]


def format_large_number(value):
    value = safe_float(value)

    if value >= 1_000_000_000_000:
        return f"${round(value / 1_000_000_000_000, 2)}T"

    if value >= 1_000_000_000:
        return f"${round(value / 1_000_000_000, 2)}B"

    if value >= 1_000_000:
        return f"{round(value / 1_000_000, 2)}M"

    if value >= 1_000:
        return f"{round(value / 1_000, 2)}K"

    return "N/A"


def build_reason_tags(rsi, high_52w, price, volume_ratio, canslim, target_change, info):
    tags = []

    if high_52w > 0 and price / high_52w >= 0.95:
        tags.append("📈 신고가")

    if volume_ratio >= 1.2:
        tags.append(f"🐳 {round(volume_ratio, 1)}x")

    if rsi >= 70:
        tags.append(f"RSI {round(rsi)} 과열")
    elif rsi <= 35:
        tags.append(f"RSI {round(rsi)} 저점")
    else:
        tags.append(f"RSI {round(rsi)}")

    if canslim and canslim.get("passed_count", 0) >= 5:
        tags.append("🏆 RS 우수")

    if target_change >= 10:
        tags.append(f"목표가 +{round(target_change)}%")

    roe = safe_float(info.get("roe")) * 100
    if roe >= 20:
        tags.append(f"💰 ROE{round(roe)}%")

    growth = safe_float(info.get("earnings_growth")) * 100
    if growth >= 10:
        tags.append("📊 EPS↑")

    return tags[:5]


def build_stock_data(market="US"):
    stocks = []
    tickers = get_market_tickers(market)

    for index, ticker in enumerate(tickers, start=1):
        history = get_stock_history(ticker)

        if history is None:
            continue

        info = get_stock_info(ticker, market)
        extended = get_extended_market_info(ticker)
        news = get_news_sentiment(ticker)

        price = safe_price_from_history(history)
        prev_price = safe_prev_price_from_history(history)

        change = 0.0
        if prev_price > 0:
            change = safe_round(((price - prev_price) / prev_price) * 100, 2)

        rsi = safe_round(calculate_rsi(history), 2)
        ma20 = safe_round(calculate_ma(history, 20), 2)
        ma50 = safe_round(calculate_ma(history, 50), 2)
        ma200 = safe_round(calculate_ma(history, 200), 2)
        atr = safe_round(calculate_atr(history), 2)
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

        raw_target = safe_float(info.get("target"))

        if raw_target > 0:
            target = safe_round(raw_target, 2)
        else:
            target = safe_round(price + atr * 3, 2)

        target_change = 0.0
        if price > 0:
            target_change = safe_round(((target - price) / price) * 100, 2)

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

        grade = get_grade(score)
        grade_type = get_grade_type(grade)

        signal, signal_type = get_signal(score)

        ma_status = "정배열" if ma20 > ma50 > ma200 else "비정배열"
        ma_status_type = "green" if ma_status == "정배열" else "red"

        if market == "SP500":
            sector = info["sector"]
        elif market == "KR":
            sector = "Korea"
        else:
            sector = "Mag 7"

        stocks.append({
            "rank": index,
            "ticker": ticker,
            "name": info["name"],
            "description": info["description"],
            "sector": sector,
            "score": score,
            "grade": grade,
            "grade_type": grade_type,
            "signal": signal,
            "signal_type": signal_type,
            "price": safe_round(price, 2),
            "change": safe_round(change, 2),
            "rsi": safe_round(rsi, 2),
            "rsi_status": "과매수" if rsi >= 70 else "과매도" if rsi <= 30 else "중립",
            "rsi_status_type": "red" if rsi >= 70 else "green" if rsi <= 30 else "yellow",
            "target": safe_round(target, 2),
            "target_change": safe_round(target_change, 2),
            "atr": safe_round(atr, 2),
            "backtest": backtest,
            "ma20": safe_round(ma20, 2),
            "ma50": safe_round(ma50, 2),
            "ma200": safe_round(ma200, 2),
            "ma_status": ma_status,
            "ma_status_type": ma_status_type,
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
            "reason": build_reason_text(
                rsi=rsi,
                macd_status=macd["status"],
                volume_ratio=volume_ratio,
                canslim=canslim,
                ma_status=ma_status,
            )
        })

    stocks.sort(key=lambda x: x["score"], reverse=True)

    for index, stock in enumerate(stocks, start=1):
        stock["rank"] = index

    return stocks


def build_etf_data():
    return [
        {
            "ticker": "SPY",
            "name": "SPDR S&P 500 ETF",
            "category": "미국 대형주",
            "price": 575.21,
            "change": 0.42,
            "rsi": 58.2,
            "score": 82,
            "signal": "상승 추세 유지",
        },
        {
            "ticker": "QQQ",
            "name": "Invesco QQQ Trust",
            "category": "나스닥 기술주",
            "price": 498.34,
            "change": 0.87,
            "rsi": 61.5,
            "score": 85,
            "signal": "기술주 강세",
        },
        {
            "ticker": "SOXX",
            "name": "iShares Semiconductor ETF",
            "category": "반도체",
            "price": 243.12,
            "change": 1.24,
            "rsi": 67.1,
            "score": 88,
            "signal": "AI 반도체 수급 양호",
        },
        {
            "ticker": "XLE",
            "name": "Energy Select Sector SPDR",
            "category": "에너지",
            "price": 91.45,
            "change": -0.31,
            "rsi": 48.6,
            "score": 61,
            "signal": "유가 변동성 관망",
        },
    ]


@main.route("/")
def index():
    market = request.args.get("market", "US")
    stocks = build_stock_data(market)
    etfs = build_etf_data()
    market_overview = get_market_overview()

    return render_template(
        "index.html",
        stocks=stocks,
        etfs=etfs,
        market=market,
        market_overview=market_overview,
    )


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
        "등급",
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
            stock["grade"],
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