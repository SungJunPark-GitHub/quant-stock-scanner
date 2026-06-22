import csv
import io
import json
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, Response, jsonify, request

from app.services.backtest_service import run_simple_backtest
from app.services.market_service import (
    get_market_tickers,
    get_stock_history,
    get_stock_info,
    get_us_display_description,
    get_us_display_name,
    get_extended_market_info,
    get_insider_transactions,
    get_stock_events,
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
from app.services.moat_service import build_moat

from app.utils.data_utils import (
    safe_float,
    safe_round,
    safe_price_from_history,
    safe_prev_price_from_history,
)

from app.utils.grade_utils import get_grade, get_grade_type
from app.services.macro_service import get_market_overview


main = Blueprint("main", __name__)
SNAPSHOT_DIR = Path(__file__).resolve().parent / "cache" / "scan_snapshots"
DATA_DIR = Path(__file__).resolve().parent / "data"
ETF_UNIVERSE_FILE = DATA_DIR / "etf_universe.json"
AUTO_UPDATE_MIN_INTERVAL_SECONDS = 60 * 15
AUTO_UPDATE_DEFAULT_INTERVAL_SECONDS = 60 * 30
AUTO_UPDATE_LOCK = threading.Lock()
AUTO_UPDATE_THREAD = None
AUTO_UPDATE_STATUS = {
    "enabled": False,
    "running": False,
    "task": "대기",
    "stage": "idle",
    "current": 0,
    "total": 0,
    "percent": 0,
    "item": "",
    "last_started_at": None,
    "last_finished_at": None,
    "last_error": None,
}


def get_auto_update_interval_seconds():
    raw_minutes = os.getenv("AUTO_UPDATE_INTERVAL_MINUTES", "").strip()

    try:
        interval = int(raw_minutes) * 60 if raw_minutes else AUTO_UPDATE_DEFAULT_INTERVAL_SECONDS
    except ValueError:
        interval = AUTO_UPDATE_DEFAULT_INTERVAL_SECONDS

    return max(AUTO_UPDATE_MIN_INTERVAL_SECONDS, interval)


def get_auto_update_initial_delay_seconds():
    raw_seconds = os.getenv("AUTO_UPDATE_INITIAL_DELAY_SECONDS", "10").strip()

    try:
        return max(0, int(raw_seconds))
    except ValueError:
        return 10


def is_auto_update_enabled():
    return os.getenv("AUTO_UPDATE_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def get_auto_update_status():
    status = dict(AUTO_UPDATE_STATUS)
    status["interval_seconds"] = get_auto_update_interval_seconds()
    status["last_finished_label"] = format_snapshot_time(status.get("last_finished_at"))
    return status


def reset_auto_update_progress(task="대기", stage="idle"):
    AUTO_UPDATE_STATUS.update({
        "task": task,
        "stage": stage,
        "current": 0,
        "total": 0,
        "percent": 0,
        "item": "",
    })


def set_auto_update_progress(task, current, total, item=""):
    total = max(0, int(total or 0))
    current = max(0, min(int(current or 0), total)) if total else 0
    percent = int(round((current / total) * 100)) if total else 0

    AUTO_UPDATE_STATUS.update({
        "task": task,
        "stage": "running",
        "current": current,
        "total": total,
        "percent": percent,
        "item": item,
    })


def is_snapshot_stale(snapshot, interval_seconds):
    updated_at = snapshot.get("updated_at")

    if not updated_at:
        return True

    try:
        return time.time() - float(updated_at) >= interval_seconds
    except Exception:
        return True


def empty_insider_transactions(ticker):
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        source = "SEC Form 4 (yfinance) · 한국 종목은 미지원"
    else:
        source = "상세보기에서 최신 SEC Form 4 데이터를 불러옵니다."

    return {
        "buy_total": "$0",
        "sell_total": "$0",
        "net_total": "$0",
        "net_label": "순매매",
        "net_type": "neutral",
        "count": 0,
        "items": [],
        "source": source,
    }


def empty_stock_events():
    return {
        "count": 0,
        "items": [],
        "source": "상세보기에서 yfinance 캘린더를 불러옵니다.",
    }


def empty_news_sentiment():
    return {
        "headline": "상세보기에서 최신 뉴스를 불러옵니다.",
        "sentiment": "Neutral",
        "sentiment_type": "yellow",
        "items": [],
    }


def get_snapshot_path(market):
    safe_market = "".join(
        char for char in market.upper()
        if char.isalnum() or char in ["-", "_"]
    ) or "US"

    return SNAPSHOT_DIR / f"{safe_market}.json"


def get_etf_snapshot_path():
    return SNAPSHOT_DIR / "ETF.json"


def format_snapshot_time(timestamp):
    if not timestamp:
        return "업데이트 필요"

    try:
        updated_at = datetime.fromtimestamp(float(timestamp))
        return updated_at.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "업데이트 필요"


def get_stock_logo_initial(name, ticker):
    label = str(name or ticker or "").strip()

    if not label:
        return "?"

    return label[0].upper()


def get_clean_stock_symbol(ticker):
    return str(ticker or "").strip().upper().replace(".KS", "").replace(".KQ", "")


STOCK_LOGO_OVERRIDES = {
    "ONDS": "https://logo.clearbit.com/ondas.com",
    "IREN": "https://logo.clearbit.com/iren.com",
    "QXO": "https://logo.clearbit.com/qxo.com",
    "RCAT": "https://logo.clearbit.com/redcat.red",
}


def get_toss_stock_logo_url(ticker):
    symbol = get_clean_stock_symbol(ticker).replace("-", ".")

    if not symbol:
        return ""

    return f"https://static.toss.im/png-icons/securities/icn-sec-fill-{symbol}.png"


def get_iex_stock_logo_url(ticker):
    symbol = get_clean_stock_symbol(ticker).replace("-", ".")

    if not symbol:
        return ""

    return f"https://storage.googleapis.com/iex/api/logos/{symbol}.png"


def is_generated_stock_logo_url(url):
    return (
        "static.toss.im/png-icons/securities/" in str(url or "") or
        "storage.googleapis.com/iex/api/logos/" in str(url or "")
    )


def get_stock_logo_url(ticker, stock=None):
    stock = stock or {}
    custom_logo_url = stock.get("logo_url")

    if custom_logo_url and not is_generated_stock_logo_url(custom_logo_url):
        return custom_logo_url

    ticker = str(ticker or "").strip().upper()

    if not ticker:
        return ""

    if ticker in STOCK_LOGO_OVERRIDES:
        return STOCK_LOGO_OVERRIDES[ticker]

    return get_toss_stock_logo_url(ticker)


def get_stock_logo_fallback_url(ticker):
    ticker = str(ticker or "").strip().upper()

    if not ticker:
        return ""

    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return ""

    return get_iex_stock_logo_url(ticker)


def apply_stock_logo_fields(stock):
    ticker = stock.get("ticker", "")
    name = stock.get("name", "")
    stock["logo_url"] = get_stock_logo_url(ticker, stock)
    stock["logo_fallback_url"] = get_stock_logo_fallback_url(ticker)
    stock["logo_initial"] = get_stock_logo_initial(name, ticker)
    return stock


def normalize_snapshot_stocks(market, stocks):
    normalized = []
    normalized_market = market.upper()

    for stock in stocks:
        if not isinstance(stock, dict):
            continue

        item = stock.copy()
        if normalized_market == "US":
            ticker = item.get("ticker", "")
            item["name"] = get_us_display_name(ticker, item.get("name", ""))
            item["description"] = get_us_display_description(
                ticker,
                item.get("description", ""),
                item.get("sector", ""),
            )
            item["sector"] = get_us_display_description(
                "",
                item.get("sector", ""),
                item.get("sector", ""),
            )

        refresh_snapshot_score(item)
        item.update(calculate_score_trend(item))
        item["average_volume"] = format_share_volume(item.get("average_volume_value"))
        item["market_cap"] = format_market_cap(item.get("market_cap_value"), normalized_market)
        apply_stock_logo_fields(item)
        normalized.append(item)

    return normalized


def calculate_snapshot_momentum(stock, days):
    prices = stock.get("chart", {}).get("1Y", {}).get("prices", [])

    if len(prices) <= days:
        return 0.0

    start_price = safe_float(prices[-days - 1])
    end_price = safe_float(prices[-1])

    if start_price <= 0:
        return 0.0

    return ((end_price - start_price) / start_price) * 100


def calculate_snapshot_high_52w(stock):
    high_52w = safe_float(stock.get("high_52w"))

    if high_52w > 0:
        return high_52w

    prices = [
        safe_float(price)
        for price in stock.get("chart", {}).get("1Y", {}).get("prices", [])
    ]
    clean_prices = [price for price in prices if price > 0]

    if not clean_prices:
        return 0.0

    return max(clean_prices[-252:])


def score_snapshot_canslim_item(stock, item):
    key = item.get("key")
    price = safe_float(stock.get("price"))
    ma50 = safe_float(stock.get("ma50"))
    ma200 = safe_float(stock.get("ma200"))
    rsi = safe_float(stock.get("rsi"))
    volume_ratio = safe_float(stock.get("volume_ratio"))
    high_52w = calculate_snapshot_high_52w(stock)
    high_gap = price / high_52w if high_52w > 0 and price > 0 else 0
    uptrend = bool(price > ma50 > ma200)

    if key in {"C", "A"}:
        return 82 if item.get("passed") else 45

    if key == "N":
        if high_gap >= 0.95:
            return 100
        if high_gap >= 0.90:
            return 82
        if high_gap >= 0.80:
            return 58
        if high_gap >= 0.65:
            return 38
        return 22

    if key == "S":
        if volume_ratio >= 1.5:
            return 100
        if volume_ratio >= 1.3:
            return 85
        if volume_ratio >= 1.1:
            return 68
        if volume_ratio >= 0.8:
            return 48
        return 28

    if key == "L":
        if uptrend and 50 <= rsi <= 70:
            return 92
        if uptrend:
            return 76
        if price > ma200 and rsi >= 45:
            return 62
        if price > ma50:
            return 50
        return 32

    if key == "I":
        if volume_ratio >= 1.3 and uptrend:
            return 92
        if volume_ratio >= 1.3:
            return 80
        if uptrend:
            return 66
        if volume_ratio >= 0.9:
            return 48
        return 30

    if key == "M":
        if uptrend:
            return 90
        if price > ma200:
            return 62
        if price > ma50:
            return 50
        return 30

    return 50


def upgrade_snapshot_canslim(stock):
    canslim = stock.get("canslim") or {}
    items = canslim.get("items") or []

    if not items:
        return canslim

    if all("score" in item for item in items):
        return canslim

    upgraded_items = []

    for item in items:
        upgraded = item.copy()
        upgraded["score"] = score_snapshot_canslim_item(stock, upgraded)
        upgraded["passed"] = upgraded["score"] >= 70
        upgraded_items.append(upgraded)

    passed_count = int(sum(1 for item in upgraded_items if item["passed"]))

    upgraded_canslim = {
        **canslim,
        "items": upgraded_items,
        "passed_count": passed_count,
        "total_count": len(upgraded_items),
        "score": int(round(sum(item["score"] for item in upgraded_items) / len(upgraded_items))),
    }
    stock["canslim"] = upgraded_canslim
    return upgraded_canslim


def refresh_snapshot_score(stock):
    canslim = upgrade_snapshot_canslim(stock)
    macd = stock.get("macd") or {}
    moat = stock.get("moat") or build_moat(
        ticker=stock.get("ticker", ""),
        name=stock.get("name", ""),
        sector=stock.get("sector", ""),
        description=stock.get("description", ""),
    )
    stock["moat"] = moat
    high_52w = calculate_snapshot_high_52w(stock)
    score = calculate_score(
        rsi=stock.get("rsi"),
        price=stock.get("price"),
        ma20=stock.get("ma20"),
        ma50=stock.get("ma50"),
        ma200=stock.get("ma200"),
        macd_status=macd.get("status", ""),
        canslim_score=canslim.get("score", 0),
        high_52w=high_52w,
        volume_ratio=stock.get("volume_ratio"),
        atr=stock.get("atr"),
        momentum_3m=calculate_snapshot_momentum(stock, 63),
        momentum_6m=calculate_snapshot_momentum(stock, 126),
        moat_bonus=moat.get("total", 0),
    )
    grade = get_grade(score)
    signal, signal_type = get_signal(score)

    stock["score"] = score
    stock["high_52w"] = high_52w
    stock["grade"] = grade
    stock["grade_type"] = get_grade_type(grade)
    stock["signal"] = signal
    stock["signal_type"] = signal_type

    if safe_float(moat.get("total")) >= 6:
        tags = list(stock.get("reason_tags") or [])
        moat_tag = f"🏰 해자 +{safe_float(moat.get('total')):g}"

        if not any("해자" in str(tag) for tag in tags):
            tags.append(moat_tag)

        stock["reason_tags"] = tags[:5]


def is_finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False

    return math.isfinite(number)


def rank_values(values):
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0

    while index < len(indexed):
        end = index

        while end + 1 < len(indexed) and indexed[end + 1][1] == indexed[index][1]:
            end += 1

        rank = (index + end + 2) / 2

        for position in range(index, end + 1):
            original_index = indexed[position][0]
            ranks[original_index] = rank

        index = end + 1

    return ranks


def pearson_correlation(left, right):
    if len(left) < 2 or len(left) != len(right):
        return 0.0

    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum(
        (left_item - left_mean) * (right_item - right_mean)
        for left_item, right_item in zip(left, right)
    )
    left_variance = sum((item - left_mean) ** 2 for item in left)
    right_variance = sum((item - right_mean) ** 2 for item in right)
    denominator = math.sqrt(left_variance * right_variance)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def spearman_correlation(left, right):
    return pearson_correlation(rank_values(left), rank_values(right))


def estimate_historical_score(prices, index):
    price = prices[index]

    if price <= 0 or index < 200:
        return None

    prev_63 = prices[index - 63]
    prev_126 = prices[index - 126]

    if prev_63 <= 0 or prev_126 <= 0:
        return None

    momentum_3m = ((price - prev_63) / prev_63) * 100
    momentum_6m = ((price - prev_126) / prev_126) * 100
    window = prices[index - 20:index + 1]
    returns = [
        (window[position] - window[position - 1]) / window[position - 1]
        for position in range(1, len(window))
        if window[position - 1] > 0
    ]
    volatility = 0.0

    if returns:
        returns_mean = sum(returns) / len(returns)
        volatility = math.sqrt(
            sum((item - returns_mean) ** 2 for item in returns) / len(returns)
        )

    ma20 = sum(prices[index - 19:index + 1]) / 20
    ma50 = sum(prices[index - 49:index + 1]) / 50
    ma200 = sum(prices[index - 199:index + 1]) / 200
    high_52w = max(prices[max(0, index - 251):index + 1])
    score = 0

    if price > ma20 > ma50 > ma200:
        score += 22
    elif price > ma50 > ma200:
        score += 16
    elif price > ma200:
        score += 9
    elif price > ma50:
        score += 5
    else:
        score -= 8

    if momentum_6m >= 25:
        score += 10
    elif momentum_6m >= 12:
        score += 7
    elif momentum_6m > 0:
        score += 3
    elif momentum_6m <= -20:
        score -= 6

    if momentum_3m >= 15:
        score += 8
    elif momentum_3m >= 6:
        score += 5
    elif momentum_3m > 0:
        score += 2
    elif momentum_3m <= -15:
        score -= 5

    if high_52w > 0:
        high_gap = price / high_52w

        if high_gap >= 0.95:
            score += 8
        elif high_gap >= 0.9:
            score += 5
        elif high_gap >= 0.8:
            score += 2
        elif high_gap < 0.65:
            score -= 8
        elif high_gap < 0.75:
            score -= 4

    score -= volatility * 2200

    return max(0, min(100, score))


def calculate_score_trend(stock, lookback=20):
    prices = stock.get("chart", {}).get("1Y", {}).get("prices", [])
    clean_prices = [
        float(price)
        for price in prices
        if is_finite_number(price) and float(price) > 0
    ]

    if len(clean_prices) <= lookback + 200:
        return {
            "score_delta": None,
            "score_trend": "데이터 부족",
            "score_trend_type": "flat",
        }

    current_score = estimate_historical_score(clean_prices, len(clean_prices) - 1)
    previous_score = estimate_historical_score(clean_prices, len(clean_prices) - lookback - 1)

    if current_score is None or previous_score is None:
        return {
            "score_delta": None,
            "score_trend": "데이터 부족",
            "score_trend_type": "flat",
        }

    delta = int(round(current_score - previous_score))

    if delta >= 8:
        trend = "강한 개선"
        trend_type = "up"
    elif delta >= 3:
        trend = "개선"
        trend_type = "up"
    elif delta <= -8:
        trend = "악화"
        trend_type = "down"
    elif delta <= -3:
        trend = "약화"
        trend_type = "down"
    else:
        trend = "유지"
        trend_type = "flat"

    return {
        "score_delta": delta,
        "score_trend": trend,
        "score_trend_type": trend_type,
    }


def calculate_score_reliability(stocks, horizon=20):
    scores = []
    future_returns = []

    for stock in stocks:
        prices = stock.get("chart", {}).get("1Y", {}).get("prices", [])
        clean_prices = [
            float(price)
            for price in prices
            if is_finite_number(price) and float(price) > 0
        ]

        if len(clean_prices) < 90 + horizon:
            continue

        evaluation_index = len(clean_prices) - horizon - 1
        historical_score = estimate_historical_score(clean_prices, evaluation_index)

        if historical_score is None:
            continue

        start_price = clean_prices[evaluation_index]
        end_price = clean_prices[-1]

        if start_price <= 0:
            continue

        scores.append(historical_score)
        future_returns.append((end_price - start_price) / start_price)

    sample_count = len(scores)

    if sample_count < 30:
        return {
            "ic": None,
            "sample_count": sample_count,
            "label": "검증 부족 · 표본 적음",
        }

    ic = spearman_correlation(scores, future_returns)
    if ic >= 0.25:
        strength = "잘 맞음"
    elif ic >= 0.10:
        strength = "조금 맞음"
    elif ic > -0.10:
        strength = "아직 약함"
    elif ic > -0.25:
        strength = "엇갈림"
    else:
        strength = "주의 필요"

    return {
        "ic": round(ic, 2),
        "sample_count": sample_count,
        "label": f"{strength} · {sample_count}개 검증",
        "detail": f"IC {ic:+.2f}",
        "strength": strength,
    }


def load_stock_snapshot(market):
    path = get_snapshot_path(market)

    try:
        if not path.exists():
            return {
                "stocks": [],
                "updated_at": None,
                "updated_label": "업데이트 필요",
            }

        payload = json.loads(path.read_text(encoding="utf-8"))
        updated_at = payload.get("updated_at")
        stocks = normalize_snapshot_stocks(market, payload.get("stocks") or [])

        return {
            "stocks": stocks,
            "updated_at": updated_at,
            "updated_label": format_snapshot_time(updated_at),
        }
    except Exception as error:
        print(f"[SNAPSHOT LOAD ERROR] {market}: {error}")
        return {
            "stocks": [],
            "updated_at": None,
            "updated_label": "업데이트 필요",
        }


def build_client_stock(stock):
    excluded_keys = {
        "chart",
        "insider_transactions",
        "stock_events",
        "news",
    }

    return {
        key: value
        for key, value in stock.items()
        if key not in excluded_keys
    }


def load_stock_detail(market, ticker):
    path = get_snapshot_path(market)
    ticker = (ticker or "").strip().upper()

    if not ticker or not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"[STOCK DETAIL LOAD ERROR] {error}")
        return None

    for stock in payload.get("stocks") or []:
        if str(stock.get("ticker", "")).upper() != ticker:
            continue

        normalized = normalize_snapshot_stocks(market, [stock])
        return normalized[0] if normalized else None

    return None


def load_etf_universe():
    try:
        if not ETF_UNIVERSE_FILE.exists():
            return []

        data = json.loads(ETF_UNIVERSE_FILE.read_text(encoding="utf-8"))

        if not isinstance(data, list):
            return []

        return [
            item for item in data
            if isinstance(item, dict) and item.get("ticker")
        ]
    except Exception as error:
        print(f"[ETF UNIVERSE LOAD ERROR] {error}")
        return []


def build_placeholder_etfs():
    etfs = []

    for index, item in enumerate(load_etf_universe(), start=1):
        ticker = item.get("ticker")
        etf_market = get_etf_market(ticker)

        etfs.append({
            "rank": index,
            "ticker": ticker,
            "name": item.get("name") or ticker,
            "category": item.get("category") or "기타",
            "theme": item.get("theme") or "기타",
            "market": etf_market,
            "price": 0,
            "price_display": "업데이트 필요",
            "change": 0,
            "rsi": "N/A",
            "score": 0,
            "signal": "수동 업데이트 필요",
            "signal_type": "yellow",
            "volume_ratio": 0,
            "average_volume": "N/A",
            "ma_status": "N/A",
        })

    return etfs


def get_etf_market(ticker):
    ticker = (ticker or "").upper()

    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return "KR"

    return "US"


def filter_etfs_by_market(etfs, market):
    market = (market or "US").upper()
    filtered = []

    for etf in etfs:
        etf_market = etf.get("market") or get_etf_market(etf.get("ticker"))

        if etf_market == market:
            filtered.append(etf)

    for index, etf in enumerate(filtered, start=1):
        etf["rank"] = index

    return filtered


def build_etf_overview(etfs):
    theme_counts = {}

    for etf in etfs:
        theme = etf.get("theme") or "기타"
        theme_counts[theme] = theme_counts.get(theme, 0) + 1

    return {
        "total": len(etfs),
        "strong": len([
            etf for etf in etfs
            if safe_float(etf.get("score")) >= 75
        ]),
        "category": "전체",
        "themes": [
            {
                "key": theme,
                "name": theme,
                "count": count,
            }
            for theme, count in sorted(
                theme_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    }


def load_etf_snapshot():
    path = get_etf_snapshot_path()

    try:
        if not path.exists():
            return {
                "etfs": build_placeholder_etfs(),
                "updated_at": None,
                "updated_label": "업데이트 필요",
            }

        payload = json.loads(path.read_text(encoding="utf-8"))
        updated_at = payload.get("updated_at")

        return {
            "etfs": payload.get("etfs") or build_placeholder_etfs(),
            "updated_at": updated_at,
            "updated_label": format_snapshot_time(updated_at),
        }
    except Exception as error:
        print(f"[ETF SNAPSHOT LOAD ERROR] {error}")
        return {
            "etfs": build_placeholder_etfs(),
            "updated_at": None,
            "updated_label": "업데이트 필요",
        }


def save_stock_snapshot(market, stocks):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "market": market,
        "updated_at": time.time(),
        "stocks": stocks,
    }
    get_snapshot_path(market).write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    return payload


def save_etf_snapshot(etfs):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "market": "ETF",
        "updated_at": time.time(),
        "etfs": etfs,
    }
    get_etf_snapshot_path().write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    return payload


def update_stock_snapshot(market):
    stocks = build_stock_data(market, progress_task=f"{market} 주식 갱신")
    snapshot = save_stock_snapshot(market, stocks)
    return snapshot, len(stocks)


def update_etf_snapshot():
    etfs = build_etf_data(progress_task="ETF 갱신")
    snapshot = save_etf_snapshot(etfs)
    return snapshot, len(etfs)


def run_auto_update_cycle(force=False):
    interval_seconds = get_auto_update_interval_seconds()

    if not AUTO_UPDATE_LOCK.acquire(blocking=False):
        return False

    AUTO_UPDATE_STATUS.update({
        "enabled": is_auto_update_enabled(),
        "running": True,
        "task": "시작",
        "stage": "starting",
        "current": 0,
        "total": 0,
        "percent": 0,
        "item": "",
        "last_started_at": time.time(),
        "last_error": None,
    })

    try:
        stock_tasks = [
            ("US", lambda: load_stock_snapshot("US"), lambda: update_stock_snapshot("US")),
            ("KR", lambda: load_stock_snapshot("KR"), lambda: update_stock_snapshot("KR")),
        ]

        for label, load_snapshot, update_snapshot in stock_tasks:
            if not force and not is_snapshot_stale(load_snapshot(), interval_seconds):
                continue

            AUTO_UPDATE_STATUS["task"] = f"{label} 주식 갱신"
            update_snapshot()

        if force or is_snapshot_stale(load_etf_snapshot(), interval_seconds):
            AUTO_UPDATE_STATUS["task"] = "ETF 갱신"
            update_etf_snapshot()

        AUTO_UPDATE_STATUS.update({
            "task": "대기",
            "stage": "done",
            "current": AUTO_UPDATE_STATUS.get("total", 0),
            "percent": 100,
            "item": "",
            "last_finished_at": time.time(),
        })
        return True
    except Exception as error:
        AUTO_UPDATE_STATUS.update({
            "task": "오류",
            "stage": "error",
            "last_error": str(error),
            "last_finished_at": time.time(),
        })
        print(f"[AUTO UPDATE ERROR] {error}")
        return False
    finally:
        AUTO_UPDATE_STATUS["running"] = False
        AUTO_UPDATE_LOCK.release()


def start_background_updates():
    global AUTO_UPDATE_THREAD

    if not is_auto_update_enabled():
        AUTO_UPDATE_STATUS["enabled"] = False
        return

    if AUTO_UPDATE_THREAD and AUTO_UPDATE_THREAD.is_alive():
        return

    AUTO_UPDATE_STATUS["enabled"] = True

    def worker():
        initial_delay = get_auto_update_initial_delay_seconds()

        if initial_delay:
            time.sleep(initial_delay)

        while is_auto_update_enabled():
            run_auto_update_cycle(force=False)
            time.sleep(get_auto_update_interval_seconds())

    AUTO_UPDATE_THREAD = threading.Thread(
        target=worker,
        name="quant-auto-updater",
        daemon=True,
    )
    AUTO_UPDATE_THREAD.start()


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


def format_korean_number(value, unit_name=""):
    value = safe_float(value)

    if value <= 0:
        return "N/A"

    if value >= 100_000_000:
        amount = value / 100_000_000
        return f"{amount:,.1f}억{unit_name}"

    if value >= 10_000:
        amount = value / 10_000
        return f"{amount:,.1f}만{unit_name}"

    return f"{value:,.0f}{unit_name}"


def format_share_volume(value):
    return format_korean_number(value, "주")


def format_market_cap(value, market="US"):
    value = safe_float(value)

    if value <= 0:
        return "N/A"

    suffix = "달러" if market == "US" else "원"

    if value >= 1_000_000_000_000:
        amount = value / 1_000_000_000_000
        return f"{amount:,.1f}조 {suffix}"

    if value >= 1_000_000_000:
        amount = value / 100_000_000
        return f"{amount:,.0f}억 {suffix}"

    return format_korean_number(value, suffix)


def format_price_value(value, market="US"):
    value = safe_float(value)

    if value <= 0:
        return "N/A"

    if market == "KR":
        return f"{round(value):,}"

    return f"{value:,.2f}"


def calculate_period_return(history, days):
    if history is None or "Close" not in history:
        return 0.0

    closes = history["Close"].dropna()

    if len(closes) <= days:
        return 0.0

    start_price = safe_float(closes.iloc[-days - 1])
    end_price = safe_float(closes.iloc[-1])

    if start_price <= 0:
        return 0.0

    return ((end_price - start_price) / start_price) * 100


def build_reason_tags(rsi, high_52w, price, volume_ratio, canslim, info, moat=None):
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

    if moat and safe_float(moat.get("total")) >= 6:
        tags.append(f"🏰 해자 +{safe_float(moat.get('total')):g}")

    roe = safe_float(info.get("roe")) * 100
    if roe >= 20:
        tags.append(f"💰 ROE{round(roe)}%")

    growth = safe_float(info.get("earnings_growth")) * 100
    if growth >= 10:
        tags.append("📊 EPS↑")

    return tags[:5]


def build_stock_data(market="US", progress_task=None):
    stocks = []
    tickers = get_market_tickers(market)
    total_tickers = len(tickers)

    for index, ticker in enumerate(tickers, start=1):
        if progress_task:
            set_auto_update_progress(progress_task, index, total_tickers, ticker)

        history = get_stock_history(ticker)

        if history is None:
            continue

        info = get_stock_info(ticker, market)
        extended = get_extended_market_info(ticker)
        insider_transactions = empty_insider_transactions(ticker)
        stock_events = empty_stock_events()
        news = empty_news_sentiment()

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
        momentum_3m = safe_round(calculate_period_return(history, 63), 2)
        momentum_6m = safe_round(calculate_period_return(history, 126), 2)

        canslim = build_canslim(
            history=history,
            info=info,
            rsi=rsi,
            price=price,
            ma50=ma50,
            ma200=ma200,
        )
        moat = build_moat(
            ticker=ticker,
            name=info.get("name", ""),
            sector=info.get("sector", ""),
            description=info.get("description", ""),
            info=info,
        )

        raw_target = safe_float(info.get("target"))
        has_analyst_target = raw_target > 0

        if has_analyst_target:
            target = safe_round(raw_target, 2)
        else:
            target = 0.0

        target_change = 0.0
        if has_analyst_target and price > 0:
            target_change = safe_round(((target - price) / price) * 100, 2)

        average_volume = info.get("average_volume")

        if safe_float(average_volume) <= 0 and "Volume" in history:
            average_volume = history["Volume"].tail(20).mean()

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
            momentum_3m=momentum_3m,
            momentum_6m=momentum_6m,
            moat_bonus=moat.get("total", 0),
        )

        grade = get_grade(score)
        grade_type = get_grade_type(grade)

        signal, signal_type = get_signal(score)

        ma_status = "정배열" if ma20 > ma50 > ma200 else "비정배열"
        ma_status_type = "green" if ma_status == "정배열" else "red"

        sector = info["sector"]

        stocks.append(apply_stock_logo_fields({
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
            "price_display": format_price_value(price, market),
            "change": safe_round(change, 2),
            "rsi": safe_round(rsi, 2),
            "rsi_status": "과매수" if rsi >= 70 else "과매도" if rsi <= 30 else "중립",
            "rsi_status_type": "red" if rsi >= 70 else "green" if rsi <= 30 else "yellow",
            "target": safe_round(target, 2),
            "target_display": format_price_value(target, market) if has_analyst_target else "N/A",
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
            "insider_transactions": insider_transactions,
            "stock_events": stock_events,
            "news": news,
            "high_52w": high_52w,
            "volume_ratio": volume_ratio,
            "momentum_3m": momentum_3m,
            "momentum_6m": momentum_6m,
            "average_volume_value": safe_float(average_volume),
            "average_volume": format_share_volume(average_volume),
            "market_cap_value": safe_float(info.get("market_cap")),
            "market_cap": format_market_cap(info.get("market_cap"), market),
            "canslim": canslim,
            "moat": moat,
            "chart": build_chart_data(history),
            "reason_tags": build_reason_tags(
                rsi=rsi,
                high_52w=high_52w,
                price=price,
                volume_ratio=volume_ratio,
                canslim=canslim,
                info=info,
                moat=moat,
            ),
            "reason": build_reason_text(
                rsi=rsi,
                macd_status=macd["status"],
                volume_ratio=volume_ratio,
                canslim=canslim,
                ma_status=ma_status,
            )
        }))

    stocks.sort(key=lambda x: x.get("market_cap_value", 0), reverse=True)

    for index, stock in enumerate(stocks, start=1):
        stock["rank"] = index

    return stocks


def calculate_etf_score(rsi, price, ma20, ma50, ma200, change, volume_ratio):
    score = 50

    if ma20 > ma50 > ma200:
        score += 22
    elif price > ma50 > ma200:
        score += 14
    elif price > ma200:
        score += 7
    else:
        score -= 10

    if 45 <= rsi <= 65:
        score += 14
    elif 35 <= rsi < 45 or 65 < rsi <= 72:
        score += 6
    elif rsi >= 78:
        score -= 8
    elif rsi <= 30:
        score -= 5

    if change > 0:
        score += min(8, safe_float(change) * 2)
    else:
        score += max(-8, safe_float(change) * 2)

    if volume_ratio >= 1.2:
        score += 6
    elif volume_ratio <= 0.7:
        score -= 4

    return int(max(0, min(100, round(score))))


def get_etf_signal(score, ma_status, rsi):
    if score >= 75:
        return "상승 추세 우위", "green"

    if score >= 60:
        return "관망 후 진입", "blue"

    if rsi <= 35:
        return "과매도 반등 후보", "yellow"

    if ma_status == "비정배열":
        return "추세 약세 주의", "red"

    return "중립 관망", "yellow"


def build_etf_data(progress_task=None):
    etfs = []
    universe = load_etf_universe()
    total_etfs = len(universe)

    for index, item in enumerate(universe, start=1):
        ticker = item.get("ticker", "").strip().upper()

        if not ticker:
            continue

        if progress_task:
            set_auto_update_progress(progress_task, index, total_etfs, ticker)

        history = get_stock_history(ticker)

        if history is None:
            continue

        price = safe_price_from_history(history)
        prev_price = safe_prev_price_from_history(history)

        change = 0.0
        if prev_price > 0:
            change = safe_round(((price - prev_price) / prev_price) * 100, 2)

        rsi = safe_round(calculate_rsi(history), 2)
        ma20 = safe_round(calculate_ma(history, 20), 2)
        ma50 = safe_round(calculate_ma(history, 50), 2)
        ma200 = safe_round(calculate_ma(history, 200), 2)
        volume_ratio = safe_round(calculate_volume_ratio(history), 2)
        average_volume = history["Volume"].tail(20).mean() if "Volume" in history else 0
        ma_status = "정배열" if ma20 > ma50 > ma200 else "비정배열"
        score = calculate_etf_score(
            rsi=rsi,
            price=price,
            ma20=ma20,
            ma50=ma50,
            ma200=ma200,
            change=change,
            volume_ratio=volume_ratio,
        )
        signal, signal_type = get_etf_signal(score, ma_status, rsi)
        market = get_etf_market(ticker)

        etfs.append({
            "rank": index,
            "ticker": ticker,
            "name": item.get("name") or ticker,
            "category": item.get("category") or "기타",
            "theme": item.get("theme") or "기타",
            "market": market,
            "price": safe_round(price, 2),
            "price_display": format_price_value(price, market),
            "change": safe_round(change, 2),
            "rsi": safe_round(rsi, 2),
            "score": score,
            "signal": signal,
            "signal_type": signal_type,
            "volume_ratio": volume_ratio,
            "average_volume": format_share_volume(average_volume),
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "ma_status": ma_status,
        })

    etfs.sort(key=lambda item: item["score"], reverse=True)

    for index, etf in enumerate(etfs, start=1):
        etf["rank"] = index

    return etfs


@main.route("/")
def index():
    market = request.args.get("market", "US")
    snapshot = load_stock_snapshot(market)
    etf_snapshot = load_etf_snapshot()
    stocks = snapshot["stocks"]
    etfs = filter_etfs_by_market(etf_snapshot["etfs"], market)
    market_overview = get_market_overview(
        market=market,
        stocks=stocks,
        snapshot_updated_at=snapshot["updated_at"],
    )
    market_overview["scanner_summary"]["total"] = len(stocks)
    market_overview["scanner_summary"]["top_grade"] = len([
        stock for stock in stocks
        if stock.get("grade") == "S"
    ])
    score_reliability = calculate_score_reliability(stocks)
    market_overview["scanner_summary"]["reliability"] = score_reliability["label"]
    market_overview["scanner_summary"]["reliability_detail"] = score_reliability.get("detail", "")

    return render_template(
        "index.html",
        stocks=stocks,
        client_stocks=[build_client_stock(stock) for stock in stocks],
        etfs=etfs,
        market=market,
        market_overview=market_overview,
        stock_snapshot=snapshot,
        etf_snapshot=etf_snapshot,
        etf_overview=build_etf_overview(etfs),
        auto_update_status=get_auto_update_status(),
    )


@main.route("/api/stocks/update", methods=["POST"])
def update_stocks():
    payload = request.get_json(silent=True) or {}
    market = request.form.get("market") or payload.get("market")
    market = (market or "US").strip().upper()

    if not AUTO_UPDATE_LOCK.acquire(blocking=False):
        return jsonify({
            "error": "update already running",
            "status": get_auto_update_status(),
        }), 409

    try:
        AUTO_UPDATE_STATUS.update({
            "running": True,
            "task": f"{market} API 갱신",
            "stage": "starting",
            "current": 0,
            "total": 0,
            "percent": 0,
            "item": "",
            "last_started_at": time.time(),
            "last_error": None,
        })
        snapshot, count = update_stock_snapshot(market)
        AUTO_UPDATE_STATUS.update({
            "running": False,
            "task": "대기",
            "stage": "done",
            "current": AUTO_UPDATE_STATUS.get("total", 0),
            "percent": 100,
            "item": "",
            "last_finished_at": time.time(),
        })
    except Exception as error:
        AUTO_UPDATE_STATUS.update({
            "running": False,
            "task": "오류",
            "stage": "error",
            "last_error": str(error),
            "last_finished_at": time.time(),
        })
        raise
    finally:
        AUTO_UPDATE_LOCK.release()

    return jsonify({
        "market": market,
        "count": count,
        "updated_at": snapshot["updated_at"],
        "updated_label": format_snapshot_time(snapshot["updated_at"]),
    })


@main.route("/api/etfs/update", methods=["POST"])
def update_etfs():
    if not AUTO_UPDATE_LOCK.acquire(blocking=False):
        return jsonify({
            "error": "update already running",
            "status": get_auto_update_status(),
        }), 409

    try:
        AUTO_UPDATE_STATUS.update({
            "running": True,
            "task": "ETF API 갱신",
            "stage": "starting",
            "current": 0,
            "total": 0,
            "percent": 0,
            "item": "",
            "last_started_at": time.time(),
            "last_error": None,
        })
        snapshot, count = update_etf_snapshot()
        AUTO_UPDATE_STATUS.update({
            "running": False,
            "task": "대기",
            "stage": "done",
            "current": AUTO_UPDATE_STATUS.get("total", 0),
            "percent": 100,
            "item": "",
            "last_finished_at": time.time(),
        })
    except Exception as error:
        AUTO_UPDATE_STATUS.update({
            "running": False,
            "task": "오류",
            "stage": "error",
            "last_error": str(error),
            "last_finished_at": time.time(),
        })
        raise
    finally:
        AUTO_UPDATE_LOCK.release()

    return jsonify({
        "market": "ETF",
        "count": count,
        "updated_at": snapshot["updated_at"],
        "updated_label": format_snapshot_time(snapshot["updated_at"]),
    })


@main.route("/api/update/status")
def update_status():
    return jsonify(get_auto_update_status())


@main.route("/api/client-error", methods=["POST"])
def client_error():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message") or "Client error")[:500]
    source = str(payload.get("source") or "")[:300]
    lineno = payload.get("lineno")
    colno = payload.get("colno")
    path = str(payload.get("path") or "")[:300]
    user_agent = request.headers.get("User-Agent", "")[:300]

    print(
        "[CLIENT ERROR]",
        json.dumps({
            "message": message,
            "source": source,
            "lineno": lineno,
            "colno": colno,
            "path": path,
            "user_agent": user_agent,
        }, ensure_ascii=False),
    )

    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("source", "browser")
            scope.set_extra("client_payload", payload)
            scope.set_extra("user_agent", user_agent)
            sentry_sdk.capture_message(message, level="error")
    except Exception:
        pass

    return jsonify({"ok": True})


@main.route("/api/stock/reference")
def stock_reference():
    ticker = request.args.get("ticker", "").strip().upper()

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    return jsonify({
        "ticker": ticker,
        "insider_transactions": get_insider_transactions(ticker),
        "stock_events": get_stock_events(ticker),
        "news": get_news_sentiment(ticker),
    })


@main.route("/api/stock/detail")
def stock_detail():
    market = request.args.get("market", "US")
    ticker = request.args.get("ticker", "")
    stock = load_stock_detail(market, ticker)

    if not stock:
        return jsonify({"error": "stock not found"}), 404

    return jsonify(stock)


@main.route("/export/csv")
def export_csv():
    market = request.args.get("market", "US")
    stocks = load_stock_snapshot(market)["stocks"]

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
