import yfinance as yf


POSITIVE_KEYWORDS = [
    "growth", "beat", "beats", "record", "strong", "surge", "surges",
    "rally", "rallies", "gain", "gains", "jump", "jumps", "soar", "soars",
    "expands", "launch", "launches", "raises", "upgrade", "upgraded",
    "outperform", "profit", "ai", "demand", "bullish", "buy", "tops",
    "higher", "optimistic", "boost",
]

NEGATIVE_KEYWORDS = [
    "miss", "misses", "decline", "declines", "lawsuit", "risk", "risks",
    "cut", "cuts", "drop", "drops", "fall", "falls", "weak",
    "downgrade", "downgraded", "underperform", "loss", "probe",
    "slump", "slumps", "bearish", "sell", "lower", "concern",
    "concerns", "warning", "pressure",
]


def analyze_text_sentiment(text: str):
    if not text:
        return "Neutral", "yellow", 0

    lower_text = text.lower()

    positive_score = sum(
        1 for word in POSITIVE_KEYWORDS
        if word in lower_text
    )

    negative_score = sum(
        1 for word in NEGATIVE_KEYWORDS
        if word in lower_text
    )

    score = positive_score - negative_score

    if score > 0:
        return "Bullish", "green", score

    if score < 0:
        return "Bearish", "red", score

    return "Neutral", "yellow", score


def extract_news_item(news_item):
    content = news_item.get("content") or {}

    if isinstance(content, dict):
        title = content.get("title") or news_item.get("title") or ""
        summary = content.get("summary") or ""
        publisher = content.get("provider", {}).get("displayName", "Yahoo Finance")
        link = content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url") or ""
    else:
        title = news_item.get("title") or ""
        summary = ""
        publisher = news_item.get("publisher") or "Yahoo Finance"
        link = news_item.get("link") or ""

    return {
        "title": title,
        "summary": summary,
        "publisher": publisher,
        "link": link,
    }


def get_news_sentiment(ticker: str):
    if ticker.endswith(".KS"):
        return {
            "headline": "한국 주식 뉴스 연동은 추후 DART/네이버 뉴스 API로 확장 예정",
            "sentiment": "Neutral",
            "sentiment_type": "yellow",
            "score": 0,
            "items": [],
        }

    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []
    except Exception as error:
        print(f"[NEWS ERROR] {ticker}: {error}")
        raw_news = []

    news_items = []

    for item in raw_news[:5]:
        parsed = extract_news_item(item)

        if parsed["title"]:
            sentiment, sentiment_type, score = analyze_text_sentiment(
                f"{parsed['title']} {parsed['summary']}"
            )

            parsed["sentiment"] = sentiment
            parsed["sentiment_type"] = sentiment_type
            parsed["score"] = score

            news_items.append(parsed)

    if not news_items:
        return {
            "headline": "최근 뉴스 없음",
            "sentiment": "Neutral",
            "sentiment_type": "yellow",
            "score": 0,
            "items": [],
        }

    combined_text = " ".join(
        [item["title"] for item in news_items]
    )

    sentiment, sentiment_type, score = analyze_text_sentiment(combined_text)

    return {
        "headline": news_items[0]["title"],
        "sentiment": sentiment,
        "sentiment_type": sentiment_type,
        "score": score,
        "items": news_items,
    }