import json
import math
import time
from datetime import date, datetime
from pathlib import Path

import yfinance as yf


MARKET_SYMBOLS = [
    {"name": "VIX", "symbol": "^VIX"},
    {"name": "S&P500", "symbol": "^GSPC"},
    {"name": "나스닥", "symbol": "^IXIC"},
    {"name": "KOSPI", "symbol": "^KS11"},
    {"name": "원/달러", "symbol": "KRW=X"},
    {"name": "DXY", "symbol": "DX-Y.NYB"},
    {"name": "美10Y", "symbol": "^TNX"},
    {"name": "금", "symbol": "GC=F"},
    {"name": "WTI", "symbol": "CL=F"},
    {"name": "BTC", "symbol": "BTC-USD"},
]

MACRO_EVENTS = [
    {"date": date(2026, 6, 18), "type": "FOMC", "label": "FOMC 회의·SEP", "tone": "red"},
    {"date": date(2026, 7, 3), "type": "고용", "label": "고용보고서 (6월)", "tone": "blue"},
    {"date": date(2026, 7, 15), "type": "CPI", "label": "CPI (6월)", "tone": "orange"},
    {"date": date(2026, 7, 30), "type": "FOMC", "label": "FOMC 회의", "tone": "red"},
    {"date": date(2026, 8, 7), "type": "고용", "label": "고용보고서 (7월)", "tone": "blue"},
    {"date": date(2026, 8, 12), "type": "CPI", "label": "CPI (7월)", "tone": "orange"},
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MARKET_INDEX_GROUPS_FILE = DATA_DIR / "market_index_groups.json"


def safe_number(value, default=0):
    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return round(number, 2)
    except Exception:
        return default


def is_valid_number(value):
    try:
        number = float(value)
        return math.isfinite(number)
    except Exception:
        return False


def get_quote(symbol):
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")

        if history.empty or "Close" not in history:
            return {
                "price": 0,
                "change": 0,
                "change_type": "neutral",
                "valid": False,
            }

        closes = history["Close"].dropna()

        if len(closes) < 2:
            return {
                "price": 0,
                "change": 0,
                "change_type": "neutral",
                "valid": False,
            }

        current = safe_number(closes.iloc[-1])
        previous = safe_number(closes.iloc[-2])

        if not is_valid_number(current) or not is_valid_number(previous) or current <= 0:
            return {
                "price": 0,
                "change": 0,
                "change_type": "neutral",
                "valid": False,
            }

        change = 0
        if previous > 0:
            change = round(((current - previous) / previous) * 100, 2)

        if change > 0:
            change_type = "up"
        elif change < 0:
            change_type = "down"
        else:
            change_type = "neutral"

        return {
            "price": current,
            "change": change,
            "change_type": change_type,
            "valid": True,
        }

    except Exception as error:
        print(f"[MACRO ERROR] {symbol}: {error}")

        return {
            "price": 0,
            "change": 0,
            "change_type": "neutral",
            "valid": False,
        }


def read_json_file(path, default):
    try:
        if not path.exists():
            return default

        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"[JSON READ ERROR] {path}: {error}")
        return default


def extract_ticker(item):
    if isinstance(item, str):
        return item.strip().upper()

    if isinstance(item, dict):
        return str(item.get("ticker") or item.get("symbol") or "").strip().upper()

    return ""


def count_source_tickers(source_file):
    if not source_file:
        return 0

    data = read_json_file(DATA_DIR / source_file, [])
    tickers = []

    if isinstance(data, list):
        tickers = [extract_ticker(item) for item in data]

    return len({ticker for ticker in tickers if ticker})


def read_source_tickers(source_file):
    if not source_file:
        return []

    data = read_json_file(DATA_DIR / source_file, [])

    if not isinstance(data, list):
        return []

    tickers = []
    seen = set()

    for item in data:
        ticker = extract_ticker(item)

        if not ticker or ticker in seen:
            continue

        seen.add(ticker)
        tickers.append(ticker)

    return tickers


def get_index_group_updated_at(groups):
    timestamps = []

    for path in [MARKET_INDEX_GROUPS_FILE]:
        if path.exists():
            timestamps.append(path.stat().st_mtime)

    for group in groups:
        source_file = group.get("source_file")

        if not source_file:
            continue

        source_path = DATA_DIR / source_file

        if source_path.exists():
            timestamps.append(source_path.stat().st_mtime)

    if not timestamps:
        return time.time()

    return max(timestamps)


def get_index_group_payload(market="US"):
    market = (market or "US").upper()
    group_settings = read_json_file(MARKET_INDEX_GROUPS_FILE, {})

    if not isinstance(group_settings, dict):
        group_settings = {}

    configs = group_settings.get(market) or group_settings.get("US") or []
    groups = []
    members = {}

    for index, config in enumerate(configs):
        key = config.get("key") or f"group-{index}"
        source_file = config.get("source_file")
        tickers = read_source_tickers(source_file)
        count = config.get("count")

        if count is None:
            count = len(tickers) or count_source_tickers(source_file)

        groups.append({
            "key": key,
            "name": config.get("name") or key,
            "count": count,
            "active": index == 0,
            "source_file": source_file,
        })
        members[key] = tickers

    return {
        "created_at": get_index_group_updated_at(configs),
        "groups": groups,
        "members": members,
    }


def format_elapsed_from_timestamp(timestamp):
    if not timestamp:
        return "업데이트 필요"

    elapsed_seconds = max(0, time.time() - float(timestamp))

    if elapsed_seconds < 60:
        return "방금 전"

    elapsed_minutes = int(elapsed_seconds // 60)

    if elapsed_minutes < 60:
        return f"{elapsed_minutes}분 전"

    elapsed_hours = int(elapsed_minutes // 60)

    if elapsed_hours < 24:
        return f"{elapsed_hours}시간 전"

    elapsed_days = elapsed_hours // 24
    return f"{elapsed_days}일 전"


def get_market_overview(market="US", stocks=None, snapshot_updated_at=None):
    items = []
    updated_at = datetime.now()
    index_payload = get_index_group_payload(market)

    for market_symbol in MARKET_SYMBOLS:
        quote = get_quote(market_symbol["symbol"])
        price = quote["price"]

        if market_symbol["name"] == "美10Y":
            price = round(price / 10, 2)

        valid = bool(quote.get("valid")) and is_valid_number(price)

        items.append({
            "name": market_symbol["name"],
            "symbol": market_symbol["symbol"],
            "price": price,
            "change": quote["change"],
            "change_type": quote["change_type"],
            "valid": valid,
        })

    return {
        "risk_label": get_risk_label(items),
        "risk_chips": get_risk_chips(items),
        "macro_events": get_macro_events(),
        "notice": "여기 나오는 점수·등급·신호는 알고리즘 스크리닝 결과일 뿐임. 판단과 손익은 본인 책임임.",
        "items": items,
        "policy_rates": [
            {"name": "美기준금리", "value": "—"},
            {"name": "韓기준금리", "value": "2.50%"},
        ],
        "scanner_summary": {
            "total": 345,
            "top_grade": 10,
            "sector": "전체",
            "reliability": "IC +0.19 · 검증 중",
        },
        "index_groups": index_payload["groups"],
        "index_members": index_payload.get("members", {}),
        "list_updated_at": datetime.fromtimestamp(
            index_payload.get("created_at", time.time())
        ).strftime("%Y-%m-%d"),
        "quote_lag": format_elapsed_from_timestamp(snapshot_updated_at),
        "updated_at": updated_at.isoformat(),
    }


def get_macro_events():
    today = date.today()
    events = []

    for event in sorted(MACRO_EVENTS, key=lambda item: item["date"]):
        days = (event["date"] - today).days

        if days < 0:
            continue

        d_label = "D-day" if days == 0 else f"D-{days}"

        events.append({
            "d_label": d_label,
            "type": event["type"],
            "label": event["label"],
            "tone": event["tone"],
        })

    return events[:6]


def get_risk_chips(items):
    vix = next((item for item in items if item["name"] == "VIX"), None)
    chips = []

    if vix and vix["price"] >= 18:
        chips.append({
            "text": "위험 과열",
            "type": "danger",
        })

    if vix and vix["change"] > 0:
        chips.append({
            "text": "증가베팅 주의",
            "type": "warning",
        })

    if not chips:
        chips.append({
            "text": "시장 안정",
            "type": "safe",
        })

    return chips


def get_risk_label(items):
    vix = next((item for item in items if item["name"] == "VIX"), None)

    if not vix:
        return {
            "text": "중립",
            "type": "neutral",
        }

    value = vix["price"]

    if value >= 25:
        return {
            "text": "위험",
            "type": "danger",
        }

    if value >= 18:
        return {
            "text": "주의",
            "type": "warning",
        }

    return {
        "text": "안정",
        "type": "safe",
    }
