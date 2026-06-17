import yfinance as yf

from app.services.cache_service import get_cached_history, save_history_cache


US_TICKERS = ["GOOGL", "NVDA", "AMZN", "AAPL", "MSFT", "META", "TSLA"]

SP500_TOP50 = [
    "MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "BRK-B", "LLY", "AVGO",
    "JPM", "TSLA", "UNH", "V", "XOM", "MA", "JNJ", "PG", "HD", "COST",
    "ABBV", "MRK", "NFLX", "CRM", "AMD", "ADBE", "BAC", "KO", "PEP", "WMT",
    "TMO", "MCD", "CSCO", "ABT", "LIN", "ACN", "DIS", "INTU", "QCOM", "VZ",
    "IBM", "TXN", "AMGN", "GE", "NOW", "PM", "CAT", "DHR", "ISRG", "NEE",
]

KR_TICKERS = [
    "005930.KS",
    "000660.KS",
    "035420.KS",
    "005380.KS",
    "051910.KS",
    "035720.KS",
    "068270.KS",
]

KR_STOCK_INFO = {
    "005930.KS": {
        "name": "삼성전자",
        "sector": "Technology",
        "description": "반도체 · 스마트폰 · 가전",
    },
    "000660.KS": {
        "name": "SK하이닉스",
        "sector": "Semiconductor",
        "description": "메모리 반도체 · HBM",
    },
    "035420.KS": {
        "name": "NAVER",
        "sector": "Internet",
        "description": "검색 · 커머스 · 콘텐츠",
    },
    "005380.KS": {
        "name": "현대차",
        "sector": "Automotive",
        "description": "자동차 · 전기차 · 수소",
    },
    "051910.KS": {
        "name": "LG화학",
        "sector": "Materials",
        "description": "석유화학 · 첨단소재",
    },
    "035720.KS": {
        "name": "카카오",
        "sector": "Internet",
        "description": "메신저 · 플랫폼 · 콘텐츠",
    },
    "068270.KS": {
        "name": "셀트리온",
        "sector": "Healthcare",
        "description": "바이오시밀러 · 제약",
    },
}


def get_market_tickers(market: str):
    if market == "KR":
        return KR_TICKERS

    if market == "SP500":
        return SP500_TOP50

    return US_TICKERS


def get_stock_history(ticker: str, period: str = "1y"):
    cached_df = get_cached_history(ticker)

    if cached_df is not None and not cached_df.empty:
        print(f"[CACHE HIT] {ticker}")
        return cached_df

    print(f"[YFINANCE] Fetching {ticker}")

    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty:
        return None

    save_history_cache(ticker, df)

    return df


def get_stock_info(ticker: str, market: str = "US"):
    if ticker in KR_STOCK_INFO:
        info = KR_STOCK_INFO[ticker]

        return {
            "ticker": ticker,
            "name": info["name"],
            "sector": info["sector"],
            "description": info["description"],
            "price": 0,
            "target": 0,
            "roe": 0,
            "earnings_growth": 0,
        }

    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception as error:
        print(f"[INFO ERROR] {ticker}: {error}")
        info = {}

    return {
        "ticker": ticker,
        "name": info.get("shortName", ticker),
        "sector": info.get("sector", "Unknown"),
        "description": info.get("industry", "Unknown"),
        "price": info.get("currentPrice") or 0,
        "target": info.get("targetMeanPrice") or 0,
        "roe": float(info.get("returnOnEquity") or 0),
        "earnings_growth": float(info.get("earningsGrowth") or 0),
    }

def get_extended_market_info(ticker: str):
    if ticker.endswith(".KS"):
        return {
            "premarket_price": None,
            "premarket_change": None,
            "aftermarket_price": None,
            "aftermarket_change": None,
        }

    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception as error:
        print(f"[EXTENDED MARKET ERROR] {ticker}: {error}")
        info = {}

    regular_price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or 0
    )

    pre_price = info.get("preMarketPrice")
    post_price = info.get("postMarketPrice")

    def calc_change(price):
        if not price or not regular_price:
            return None
        return round(((price - regular_price) / regular_price) * 100, 2)

    return {
        "premarket_price": round(float(pre_price), 2) if pre_price else None,
        "premarket_change": calc_change(pre_price),
        "aftermarket_price": round(float(post_price), 2) if post_price else None,
        "aftermarket_change": calc_change(post_price),
    }