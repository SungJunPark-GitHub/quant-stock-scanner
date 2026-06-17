import yfinance as yf

from app.services.cache_service import get_cached_history, save_history_cache


MAG7_TICKERS = ["GOOGL", "NVDA", "AMZN", "AAPL", "MSFT", "META", "TSLA"]


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


def get_stock_info(ticker: str):
    stock = yf.Ticker(ticker)
    info = stock.info

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