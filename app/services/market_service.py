import yfinance as yf


MAG7_TICKERS = ["GOOGL", "NVDA", "AMZN", "AAPL", "MSFT", "META", "TSLA"]


def get_stock_history(ticker: str, period: str = "1y"):
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
        "price": info.get("currentPrice") or 0,
        "target": info.get("targetMeanPrice") or 0,

        # CAN SLIM용
        "roe": float(info.get("returnOnEquity") or 0),
        "earnings_growth": float(info.get("earningsGrowth") or 0),
    }