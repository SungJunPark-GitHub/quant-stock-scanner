import yfinance as yf

from app.services.cache_service import get_cached_history, save_history_cache


US_TICKERS = [
    "GOOGL",
    "NVDA",
    "AMZN",
    "AAPL",
    "MSFT",
    "META",
    "TSLA",
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

US_DESCRIPTION_MAP = {
    "GOOGL": "검색 광고 · 유튜브 · 제미나이",
    "GOOG": "검색 광고 · 유튜브 · 제미나이",
    "META": "페북 · 인스타 · 광고 플랫폼",
    "NVDA": "AI GPU · 블랙웰 · HBM",
    "AAPL": "아이폰 · 맥 · 애플 실리콘",
    "AMZN": "AWS · 이커머스 · 광고",
    "MSFT": "애저 클라우드 · 코파일럿",
    "TSLA": "전기차 · FSD · 에너지",

    "AVGO": "AI 네트워크 · 반도체",
    "AMD": "CPU · GPU · AI 가속기",
    "TSM": "파운드리 · 첨단 공정",
    "ASML": "EUV 노광장비",
    "NFLX": "스트리밍 플랫폼",
    "CRM": "기업용 SaaS · CRM",
    "ADBE": "크리에이티브 소프트웨어 · AI",
    "QCOM": "모바일 칩 · 통신 반도체",
    "INTU": "세무 · 회계 · 금융 소프트웨어",
    "NOW": "기업 자동화 · 워크플로우",

    "LLY": "비만치료제 · 당뇨 치료제",
    "UNH": "건강보험 · 헬스케어 서비스",
    "JNJ": "제약 · 의료기기 · 소비자 헬스",
    "ABBV": "면역질환 · 바이오 의약품",
    "MRK": "항암제 · 백신 · 제약",
    "TMO": "생명과학 장비 · 진단",
    "ABT": "의료기기 · 진단 · 헬스케어",
    "AMGN": "바이오 의약품 · 항암제",
    "ISRG": "수술 로봇 · 의료기기",

    "BRK-B": "보험 · 철도 · 투자 지주회사",
    "JPM": "대형은행 · 투자은행",
    "V": "글로벌 결제 네트워크",
    "MA": "글로벌 결제 네트워크",
    "BAC": "대형은행 · 금융 서비스",

    "XOM": "석유 · 가스 · 에너지",
    "CVX": "석유 · 가스 · 에너지",

    "PG": "생활용품 · 필수소비재",
    "COST": "회원제 창고형 리테일",
    "HD": "주택개선 · 건자재 리테일",
    "KO": "음료 · 브랜드 소비재",
    "PEP": "음료 · 스낵 · 식품",
    "WMT": "대형마트 · 리테일",
    "MCD": "글로벌 외식 프랜차이즈",
    "PM": "담배 · 니코틴 제품",

    "CSCO": "네트워크 장비 · 보안",
    "IBM": "하이브리드 클라우드 · AI",
    "TXN": "아날로그 반도체",
    "GE": "항공엔진 · 산업재",
    "CAT": "건설장비 · 산업재",
    "DHR": "생명과학 · 진단장비",
    "LIN": "산업용 가스 · 화학",
    "ACN": "컨설팅 · IT 서비스",
    "DIS": "콘텐츠 · 테마파크",
    "VZ": "통신 대형주 · 5G",
    "NEE": "전력 · 신재생 에너지",
}

US_SECTOR_MAP = {
    "Technology": "기술",
    "Communication Services": "커뮤니케이션",
    "Consumer Cyclical": "경기소비재",
    "Consumer Defensive": "필수소비재",
    "Financial Services": "금융",
    "Healthcare": "헬스케어",
    "Energy": "에너지",
    "Industrials": "산업재",
    "Basic Materials": "소재",
    "Utilities": "유틸리티",
    "Real Estate": "부동산",
}

US_INDUSTRY_MAP = {
    "Internet Content & Information": "인터넷 플랫폼",
    "Semiconductors": "반도체",
    "Consumer Electronics": "소비자 전자기기",
    "Software - Infrastructure": "클라우드 소프트웨어",
    "Software - Application": "응용 소프트웨어",
    "Internet Retail": "전자상거래",
    "Auto Manufacturers": "자동차 제조",
    "Entertainment": "콘텐츠 · 엔터",
    "Banks - Diversified": "대형은행",
    "Credit Services": "결제 · 신용서비스",
    "Drug Manufacturers - General": "대형 제약",
    "Healthcare Plans": "건강보험",
    "Medical Devices": "의료기기",
    "Oil & Gas Integrated": "석유 · 가스",
    "Discount Stores": "대형 리테일",
    "Beverages - Non-Alcoholic": "음료",
}

KR_SECTOR_MAP = {
    "Technology": "기술",
    "Semiconductor": "반도체",
    "Internet": "인터넷 플랫폼",
    "Automotive": "자동차",
    "Materials": "소재",
    "Healthcare": "헬스케어",
}

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
        sector = KR_SECTOR_MAP.get(info["sector"], info["sector"])

        return {
            "ticker": ticker,
            "name": info["name"],
            "sector": sector,
            "description": info["description"],
            "price": 0,
            "target": 0,
            "roe": 0,
            "earnings_growth": 0,
            "market_cap": 0,
            "average_volume": 0,
        }

    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception as error:
        print(f"[INFO ERROR] {ticker}: {error}")
        info = {}

    raw_sector = info.get("sector", "기타")
    raw_industry = info.get("industry", "기타")

    sector = US_INDUSTRY_MAP.get(
        raw_industry,
        US_SECTOR_MAP.get(raw_sector, raw_sector)
    )

    description = US_DESCRIPTION_MAP.get(
        ticker,
        US_INDUSTRY_MAP.get(raw_industry, raw_industry)
    )

    return {
        "ticker": ticker,
        "name": info.get("shortName", ticker),
        "sector": sector,
        "description": description,
        "price": info.get("currentPrice") or 0,
        "target": info.get("targetMeanPrice") or 0,
        "roe": float(info.get("returnOnEquity") or 0),
        "earnings_growth": float(info.get("earningsGrowth") or 0),
        "market_cap": info.get("marketCap") or 0,
        "average_volume": info.get("averageVolume") or 0,
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