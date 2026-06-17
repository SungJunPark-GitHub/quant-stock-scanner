import yfinance as yf
from datetime import datetime


MARKET_SYMBOLS = {
    "VIX": "^VIX",
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "KOSPI": "^KS11",
    "WTI": "CL=F",
    "BTC": "BTC-USD",
    "금": "GC=F",
}


def safe_number(value, default=0):
    try:
        return round(float(value), 2)
    except Exception:
        return default


def get_quote(symbol):
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")

        if history.empty or len(history) < 2:
            return {
                "price": 0,
                "change": 0,
                "change_type": "neutral",
            }

        current = safe_number(history["Close"].iloc[-1])
        previous = safe_number(history["Close"].iloc[-2])

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
        }

    except Exception as error:
        print(f"[MACRO ERROR] {symbol}: {error}")

        return {
            "price": 0,
            "change": 0,
            "change_type": "neutral",
        }


def get_market_overview():
    items = []

    for name, symbol in MARKET_SYMBOLS.items():
        quote = get_quote(symbol)

        items.append({
            "name": name,
            "symbol": symbol,
            "price": quote["price"],
            "change": quote["change"],
            "change_type": quote["change_type"],
        })

    return {
        "risk_label": get_risk_label(items),
        "items": items,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


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