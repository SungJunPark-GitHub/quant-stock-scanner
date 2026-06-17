import yfinance as yf


POSITIVE_KEYWORDS = [
    "growth",
    "beat",
    "beats",
    "record",
    "strong",
    "surge",
    "surges",
    "rally",
    "rallies",
    "gain",
    "gains",
    "jump",
    "jumps",
    "soar",
    "soars",
    "expands",
    "launch",
    "launches",
    "raises",
    "upgrade",
    "upgraded",
    "outperform",
    "profit",
    "ai",
    "demand",
    "bullish",
    "buy",
    "tops",
    "higher",
    "optimistic",
    "boost",
]

NEGATIVE_KEYWORDS = [
    "miss",
    "misses",
    "decline",
    "declines",
    "lawsuit",
    "risk",
    "risks",
    "cut",
    "cuts",
    "drop",
    "drops",
    "fall",
    "falls",
    "weak",
    "downgrade",
    "downgraded",
    "underperform",
    "loss",
    "probe",
    "slump",
    "slumps",
    "bearish",
    "sell",
    "lower",
    "concern",
    "concerns",
    "warning",
    "pressure",
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


def extract_title(news_item):
    if not news_item:
        return ""

    if "title" in news_item:
        return news_item.get("title") or ""

    content = news_item.get("content") or {}

    if isinstance(content, dict):
        return content.get("title") or content.get("summary") or ""

    return ""


def get_news_sentiment(ticker: str):
    if ticker.endswith(".KS"):
        return {
            "headline": "한국 주식 뉴스 연동은 추후 DART/네이버 뉴스 API로 확장 예정",
            "sentiment": "Neutral",
            "sentiment_type": "yellow",
            "score": 0,
        }

    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news or []
    except Exception as error:
        print(f"[NEWS ERROR] {ticker}: {error}")
        news_list = []

    if not news_list:
        return {
            "headline": "최근 뉴스 없음",
            "sentiment": "Neutral",
            "sentiment_type": "yellow",
            "score": 0,
        }

    headlines = []

    for item in news_list[:5]:
        title = extract_title(item)

        if title:
            headlines.append(title)

    if not headlines:
        return {
            "headline": "최근 뉴스 제목을 가져오지 못했습니다",
            "sentiment": "Neutral",
            "sentiment_type": "yellow",
            "score": 0,
        }

    combined_text = " ".join(headlines)
    sentiment, sentiment_type, score = analyze_text_sentiment(combined_text)

    return {
        "headline": headlines[0],
        "sentiment": sentiment,
        "sentiment_type": sentiment_type,
        "score": score,
    }