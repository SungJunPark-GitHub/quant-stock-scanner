import yfinance as yf


MAG7_TICKERS = ["GOOGL", "NVDA", "AMZN", "AAPL", "MSFT", "META", "TSLA"]


def get_stock_history(ticker: str, period: str = "6mo"):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty:
        return None

    return df


def get_stock_info(ticker: str):
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "ticker": ticker,
        "name": info.get("shortName", ticker),
        "sector": info.get("sector", "Unknown"),
        "description": info.get("industry", "Unknown"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
        "target": info.get("targetMeanPrice") or 0,
    }