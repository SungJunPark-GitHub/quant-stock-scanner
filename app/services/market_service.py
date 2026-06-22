import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from app.services.cache_service import get_cached_history, save_history_cache


FALLBACK_US_TICKERS = [
    "AAPL",
    "ABBV",
    "ABNB",
    "ABT",
    "ACN",
    "ADBE",
    "ADI",
    "ADP",
    "ADSK",
    "AEP",
    "AMAT",
    "AMD",
    "AMGN",
    "AMT",
    "AMZN",
    "ANET",
    "APP",
    "ARM",
    "ASML",
    "AVGO",
    "AXON",
    "BA",
    "BAC",
    "BKNG",
    "BRK-B",
    "BSX",
    "CAT",
    "CHTR",
    "CMCSA",
    "COST",
    "CRM",
    "CRWD",
    "CSCO",
    "CSX",
    "CVX",
    "DASH",
    "DDOG",
    "DIS",
    "DHR",
    "EQIX",
    "FTNT",
    "GE",
    "GILD",
    "GOOG",
    "GOOGL",
    "HD",
    "HON",
    "IBM",
    "INTC",
    "INTU",
    "ISRG",
    "JNJ",
    "JPM",
    "KO",
    "LIN",
    "LLY",
    "LRCX",
    "MA",
    "MCD",
    "META",
    "MRK",
    "MSFT",
    "MU",
    "NFLX",
    "NOW",
    "NVDA",
    "ORCL",
    "PANW",
    "PEP",
    "PG",
    "PLTR",
    "PM",
    "QCOM",
    "SBUX",
    "SNPS",
    "TMO",
    "TSLA",
    "TXN",
    "UNH",
    "V",
    "VZ",
    "WMT",
    "XOM",
]
US_TICKERS = FALLBACK_US_TICKERS
APP_CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
APP_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
US_UNIVERSE_CACHE = APP_CACHE_DIR / "us_universe.json"
KOSPI_LISTINGS_FILE = APP_DATA_DIR / "kospi_tickers.json"
KOSDAQ_LISTINGS_FILE = APP_DATA_DIR / "kosdaq_tickers.json"
US_INDEX_GROUPS_FILE = APP_DATA_DIR / "market_index_groups.json"
US_UNIVERSE_CACHE_TTL = 60 * 60 * 24 * 7
STOCK_INFO_CACHE_TTL = 60 * 60 * 24

FALLBACK_KOSPI_LISTINGS = [
    {"ticker": "005930.KS", "code": "005930", "name": "삼성전자", "sector": "반도체", "description": "반도체 · 스마트폰 · 가전"},
    {"ticker": "000660.KS", "code": "000660", "name": "SK하이닉스", "sector": "반도체", "description": "메모리 반도체 · HBM"},
    {"ticker": "373220.KS", "code": "373220", "name": "LG에너지솔루션", "sector": "이차전지", "description": "배터리 셀 · ESS"},
    {"ticker": "005380.KS", "code": "005380", "name": "현대차", "sector": "자동차", "description": "자동차 · 전기차 · 수소"},
    {"ticker": "000270.KS", "code": "000270", "name": "기아", "sector": "자동차", "description": "자동차 · 전기차"},
    {"ticker": "207940.KS", "code": "207940", "name": "삼성바이오로직스", "sector": "바이오 CDMO", "description": "바이오 의약품 · CDMO"},
    {"ticker": "068270.KS", "code": "068270", "name": "셀트리온", "sector": "바이오·헬스케어", "description": "바이오시밀러 · 제약"},
    {"ticker": "035420.KS", "code": "035420", "name": "NAVER", "sector": "인터넷 플랫폼", "description": "검색 · 커머스 · 콘텐츠"},
    {"ticker": "035720.KS", "code": "035720", "name": "카카오", "sector": "인터넷 플랫폼", "description": "메신저 · 플랫폼 · 콘텐츠"},
    {"ticker": "005490.KS", "code": "005490", "name": "POSCO홀딩스", "sector": "철강·화학", "description": "철강 · 이차전지 소재"},
    {"ticker": "051910.KS", "code": "051910", "name": "LG화학", "sector": "철강·화학", "description": "석유화학 · 첨단소재"},
    {"ticker": "006400.KS", "code": "006400", "name": "삼성SDI", "sector": "이차전지", "description": "배터리 셀 · 전자재료"},
    {"ticker": "012330.KS", "code": "012330", "name": "현대모비스", "sector": "자동차", "description": "자동차 부품 · 전장"},
    {"ticker": "105560.KS", "code": "105560", "name": "KB금융", "sector": "금융", "description": "은행 · 금융지주"},
    {"ticker": "055550.KS", "code": "055550", "name": "신한지주", "sector": "금융", "description": "은행 · 금융지주"},
    {"ticker": "086790.KS", "code": "086790", "name": "하나금융지주", "sector": "금융", "description": "은행 · 금융지주"},
    {"ticker": "032830.KS", "code": "032830", "name": "삼성생명", "sector": "금융", "description": "보험 · 금융"},
    {"ticker": "028260.KS", "code": "028260", "name": "삼성물산", "sector": "지주사·종합상사", "description": "상사 · 건설 · 지주"},
    {"ticker": "003550.KS", "code": "003550", "name": "LG", "sector": "지주사·종합상사", "description": "지주회사 · 전자 · 화학"},
    {"ticker": "034730.KS", "code": "034730", "name": "SK", "sector": "지주사·종합상사", "description": "지주회사 · 에너지 · 반도체"},
    {"ticker": "015760.KS", "code": "015760", "name": "한국전력", "sector": "유틸리티·가스", "description": "전력 · 유틸리티"},
    {"ticker": "017670.KS", "code": "017670", "name": "SK텔레콤", "sector": "통신", "description": "통신 · AI 인프라"},
    {"ticker": "030200.KS", "code": "030200", "name": "KT", "sector": "통신", "description": "통신 · 데이터센터"},
    {"ticker": "010950.KS", "code": "010950", "name": "S-Oil", "sector": "정유·에너지", "description": "정유 · 석유화학"},
    {"ticker": "096770.KS", "code": "096770", "name": "SK이노베이션", "sector": "정유·에너지", "description": "정유 · 배터리"},
    {"ticker": "009540.KS", "code": "009540", "name": "HD한국조선해양", "sector": "조선·해운", "description": "조선 · 해양플랜트"},
    {"ticker": "329180.KS", "code": "329180", "name": "HD현대중공업", "sector": "조선·해운", "description": "대형 조선 · 방산"},
    {"ticker": "010140.KS", "code": "010140", "name": "삼성중공업", "sector": "조선·해운", "description": "조선 · 해양플랜트"},
    {"ticker": "042660.KS", "code": "042660", "name": "한화오션", "sector": "조선·해운", "description": "조선 · 방산"},
]
KR_TICKERS = [item["ticker"] for item in FALLBACK_KOSPI_LISTINGS]

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

US_KOREAN_NAME_MAP = {
    "AAPL": "애플",
    "ABBV": "애브비",
    "ABNB": "에어비앤비",
    "ABT": "애보트 래버러토리스",
    "ACN": "액센츄어",
    "ADBE": "어도비",
    "ADI": "아날로그 디바이시스",
    "ADP": "오토매틱 데이터 프로세싱",
    "ADSK": "오토데스크",
    "AEP": "아메리칸 일렉트릭 파워",
    "AMAT": "어플라이드 머티어리얼즈",
    "AMD": "AMD",
    "AMGN": "암젠",
    "AMT": "아메리칸 타워",
    "AMZN": "아마존",
    "ANET": "아리스타 네트웍스",
    "APP": "앱러빈",
    "ARM": "Arm 홀딩스",
    "ASML": "ASML",
    "AVGO": "브로드컴",
    "AXON": "액손 엔터프라이즈",
    "BA": "보잉",
    "BAC": "뱅크오브아메리카",
    "BKNG": "부킹 홀딩스",
    "BRK-B": "버크셔 해서웨이",
    "BSX": "보스턴 사이언티픽",
    "CAT": "캐터필러",
    "CHTR": "차터 커뮤니케이션스",
    "CMCSA": "컴캐스트",
    "COST": "코스트코",
    "CRM": "세일즈포스",
    "CRWD": "크라우드스트라이크",
    "CSCO": "시스코",
    "CSX": "CSX",
    "CVX": "셰브론",
    "DASH": "도어대시",
    "DDOG": "데이터독",
    "DIS": "월트 디즈니",
    "DHR": "다나허",
    "EQIX": "에퀴닉스",
    "FTNT": "포티넷",
    "GE": "GE 에어로스페이스",
    "GILD": "길리어드 사이언스",
    "GOOG": "알파벳",
    "GOOGL": "알파벳",
    "HD": "홈디포",
    "HON": "허니웰",
    "IBM": "IBM",
    "INTC": "인텔",
    "INTU": "인튜이트",
    "ISRG": "인튜이티브 서지컬",
    "JNJ": "존슨앤드존슨",
    "JPM": "JP모건 체이스",
    "KO": "코카콜라",
    "LIN": "린데",
    "LLY": "일라이 릴리",
    "LRCX": "램 리서치",
    "MA": "마스터카드",
    "MCD": "맥도날드",
    "META": "메타 플랫폼스",
    "MRK": "머크",
    "MSFT": "마이크로소프트",
    "MU": "마이크론 테크놀로지",
    "NFLX": "넷플릭스",
    "NOW": "서비스나우",
    "NVDA": "엔비디아",
    "ORCL": "오라클",
    "PANW": "팔로알토 네트웍스",
    "PEP": "펩시코",
    "PG": "프록터앤드갬블",
    "PLTR": "팔란티어",
    "PM": "필립모리스",
    "QCOM": "퀄컴",
    "SBUX": "스타벅스",
    "SNPS": "시놉시스",
    "TMO": "써모 피셔 사이언티픽",
    "TSLA": "테슬라",
    "TXN": "텍사스 인스트루먼트",
    "UNH": "유나이티드헬스",
    "V": "비자",
    "VZ": "버라이즌",
    "WMT": "월마트",
    "XOM": "엑슨모빌",
    "ONDS": "온다스 홀딩스",
    "RCAT": "레드캣 홀딩스",
    "RDW": "레드와이어",
}

US_KOREAN_NAME_MAP.update({
    "MS": "모건스탠리",
    "GS": "골드만삭스",
    "KLAC": "KLA",
    "SNDK": "샌디스크",
    "GEV": "GE 버노바",
    "MRVL": "마벨 테크놀로지",
    "DELL": "델 테크놀로지스",
    "WDC": "웨스턴디지털",
    "WFC": "웰스파고",
    "RTX": "RTX",
    "C": "씨티그룹",
    "STX": "씨게이트",
    "AXP": "아메리칸 익스프레스",
    "APH": "암페놀",
    "TMUS": "T-모바일",
    "TJX": "TJX",
    "BLK": "블랙록",
    "GLW": "코닝",
    "ETN": "이튼",
    "IBKR": "인터랙티브 브로커스",
    "SCHW": "찰스슈왑",
    "DE": "디어",
    "T": "AT&T",
    "UNP": "유니언 퍼시픽",
    "BX": "블랙스톤",
    "WELL": "웰타워",
    "UBER": "우버",
    "PFE": "화이자",
    "SHOP": "쇼피파이",
    "BKNG": "부킹 홀딩스",
    "PLD": "프로로지스",
    "VRT": "버티브",
    "CVS": "CVS 헬스",
    "CB": "처브",
    "LOW": "로우스",
    "SPGI": "S&P 글로벌",
    "PH": "파커 하니핀",
    "PGR": "프로그레시브",
    "SYK": "스트라이커",
    "LMT": "록히드 마틴",
    "MO": "알트리아",
    "VRTX": "버텍스",
    "PDD": "핀둬둬",
    "HWM": "하우멧 에어로스페이스",
    "NEM": "뉴몬트",
    "BMY": "브리스톨마이어스스큅",
    "TT": "트레인 테크놀로지스",
    "CDNS": "케이던스 디자인",
    "PWR": "콴타 서비스",
    "SO": "서던 컴퍼니",
    "MAR": "메리어트",
    "CMI": "커민스",
    "FCX": "프리포트 맥모란",
    "BNY": "BNY 멜론",
    "CEG": "컨스텔레이션 에너지",
    "HOOD": "로빈후드",
    "DUK": "듀크 에너지",
    "GD": "제너럴 다이내믹스",
    "PNC": "PNC 파이낸셜",
    "USB": "U.S. 뱅코프",
    "KKR": "KKR",
    "WMB": "윌리엄스",
    "MNST": "몬스터 베버리지",
    "UPS": "UPS",
    "CME": "CME 그룹",
    "JCI": "존슨콘트롤즈",
    "MCK": "맥케슨",
    "WM": "웨이스트 매니지먼트",
    "EMR": "에머슨 일렉트릭",
    "ELV": "엘리번스 헬스",
    "RCL": "로열 캐리비안",
    "MMM": "3M",
    "HCA": "HCA 헬스케어",
    "MELI": "메르카도리브레",
    "SPG": "사이먼 프로퍼티",
    "HLT": "힐튼",
    "APO": "아폴로 글로벌",
    "SHW": "셔윈윌리엄스",
    "MCO": "무디스",
    "MRSH": "마시앤맥레넌",
    "FDX": "페덱스",
    "MDLZ": "몬델리즈",
    "MPWR": "모놀리식 파워",
    "COHR": "코히런트",
    "ITW": "일리노이 툴 웍스",
    "ECL": "이콜랩",
    "ICE": "인터컨티넨털 익스체인지",
    "ROST": "로스 스토어스",
    "CRH": "CRH",
    "TDG": "트랜스다임",
    "NOC": "노스럽 그러먼",
    "CI": "시그나",
    "CVNA": "카바나",
    "ORLY": "오라일리 오토모티브",
    "SLB": "SLB",
    "CL": "콜게이트 팜올리브",
    "GM": "제너럴모터스",
    "MPC": "마라톤 페트롤리엄",
    "KMI": "킨더 모건",
    "VLO": "발레로 에너지",
    "EOG": "EOG 리소시스",
    "FIX": "컴포트 시스템즈",
    "TER": "테라다인",
    "CTAS": "신타스",
    "AON": "에이온",
    "URI": "유나이티드 렌탈스",
    "NSC": "노퍽 서던",
    "DLR": "디지털 리얼티",
    "RKLB": "로켓랩",
    "NKE": "나이키",
    "ZS": "지스케일러",
    "WDAY": "워크데이",
    "VRSK": "베리스크",
    "REGN": "리제네론",
    "ROP": "로퍼 테크놀로지스",
    "FAST": "패스널",
    "ODFL": "올드 도미니언",
    "PCAR": "파카",
    "BKR": "베이커휴즈",
    "KDP": "큐리그 닥터페퍼",
    "KHC": "크래프트 하인즈",
    "PYPL": "페이팔",
    "VMC": "벌칸 머티리얼즈",
    "IRM": "아이언 마운틴",
    "EL": "에스티 로더",
    "CNP": "센터포인트 에너지",
    "ES": "에버소스 에너지",
    "STE": "스테리스",
    "KIM": "킴코 리얼티",
    "ALAB": "아스테라 랩스",
    "CRWV": "코어위브",
    "NBIS": "네비우스 그룹",
    "PL": "플래닛 랩스",
    "QXO": "QXO",
    "PGY": "파가야 테크놀로지스",
    "IONQ": "아이온큐",
    "IREN": "아이렌",
    "HUT": "허트8",
    "EOSE": "이오스 에너지",
    "BE": "블룸 에너지",
    "LPTH": "라이트패스 테크놀로지",
    "ASTS": "AST 스페이스모바일",
    "TSM": "TSMC",
    "SMR": "뉴스케일 파워",
    "OKLO": "오클로",
    "SEI": "솔라리스 에너지 인프라",
    "WTS": "와츠 워터 테크놀로지스",
    "RGTI": "리게티 컴퓨팅",
    "QBTS": "디웨이브 퀀텀",
    "TEM": "템퍼스 AI",
    "CRDO": "크레도 테크놀로지",
    "CLS": "셀레스티카",
    "ACHR": "아처 에비에이션",
    "JOBY": "조비 에비에이션",
    "SERV": "서브 로보틱스",
    "SPCX": "스페이스X",
    "GLXY": "갤럭시 디지털",
    "QUBT": "퀀텀 컴퓨팅",
    "TSEM": "타워 세미컨덕터",
    "MKSI": "MKS",
    "CIFR": "사이퍼 마이닝",
    "CORZ": "코어 사이언티픽",
    "CLSK": "클린스파크",
    "RDDT": "레딧",
    "BBAI": "빅베어 AI",
    "AI": "C3.ai",
    "CRCL": "서클 인터넷",
    "SOFI": "소파이",
    "UPST": "업스타트",
    "OPEN": "오픈도어",
    "NNE": "나노 뉴클리어 에너지",
    "LEU": "센트러스 에너지",
    "CCJ": "카메코",
    "LUNR": "인튜이티브 머신스",
    "KULR": "KULR 테크놀로지",
    "AEHR": "에어 테스트 시스템즈",
    "POET": "POET 테크놀로지스",
    "LAES": "실스크",
    "ARQQ": "아르킷 퀀텀",
})

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

US_DESCRIPTION_MAP.update({
    "AMAT": "반도체 장비 · 소재",
    "LRCX": "반도체 식각장비 · 웨이퍼 공정",
    "KLAC": "반도체 검사장비 · 수율 관리",
    "SNDK": "낸드 저장장치 · 데이터 스토리지",
    "MS": "투자은행 · 자산관리",
    "GS": "투자은행 · 자본시장",
    "GEV": "전력장비 · 에너지 인프라",
    "DELL": "PC · 서버 · 데이터센터",
    "WDC": "하드디스크 · 낸드 스토리지",
    "RTX": "항공우주 · 방산",
    "STX": "하드디스크 · 데이터 스토리지",
    "APH": "커넥터 · 전자부품",
    "TMUS": "무선통신 · 5G",
    "TJX": "오프프라이스 의류 리테일",
    "BLK": "자산운용 · ETF",
    "GLW": "디스플레이 유리 · 광섬유",
    "ETN": "전력관리 · 산업 전기장비",
    "IBKR": "온라인 브로커리지 · 거래 플랫폼",
    "SCHW": "증권 브로커리지 · 자산관리",
    "DE": "농기계 · 중장비",
    "T": "통신 · 5G · 미디어",
    "UNP": "철도 물류 · 화물 운송",
    "BX": "대체투자 · 사모펀드",
    "WELL": "헬스케어 리츠 · 시니어 주거",
    "APP": "모바일 광고 · 앱 수익화",
    "BKNG": "온라인 여행 · 숙박 예약",
    "PLD": "물류창고 리츠",
    "VRT": "데이터센터 전력 · 냉각",
    "CB": "손해보험 · 재보험",
    "LOW": "주택개선 · 건자재 리테일",
    "SPGI": "금융데이터 · 신용평가",
    "PH": "모션제어 · 산업부품",
    "PGR": "자동차보험 · 손해보험",
    "LMT": "방산 · 항공우주",
    "MO": "담배 · 니코틴 제품",
    "HWM": "항공우주 부품 · 경량 소재",
    "NEM": "금광 · 귀금속",
    "TT": "공조 · 빌딩 솔루션",
    "PWR": "전력망 공사 · 인프라",
    "SO": "전력 유틸리티",
    "MAR": "호텔 · 여행",
    "CMI": "엔진 · 전력시스템",
    "FCX": "구리 · 광산",
    "CEG": "원전 · 청정 전력",
    "DUK": "전력 유틸리티",
    "WMB": "천연가스 파이프라인",
    "UPS": "택배 · 종합물류",
    "JCI": "빌딩 자동화 · 공조",
    "WM": "폐기물 처리 · 환경 서비스",
    "RCL": "크루즈 · 여행",
    "HLT": "호텔 · 숙박",
    "SHW": "페인트 · 코팅",
    "FDX": "택배 · 항공 물류",
    "ROST": "할인 의류 리테일",
    "CRH": "건자재 · 인프라",
    "TDG": "항공부품 · 방산",
    "NOC": "방산 · 항공우주",
    "ORLY": "자동차 부품 리테일",
    "SLB": "유전 서비스 · 에너지 장비",
    "CL": "생활용품 · 구강케어",
    "GM": "자동차 · 전기차",
    "MPC": "정유 · 에너지",
    "KMI": "천연가스 파이프라인",
    "VLO": "정유 · 에너지",
    "EOG": "셰일오일 · 천연가스",
    "TER": "반도체 테스트 장비",
    "CTAS": "유니폼 · 기업 서비스",
    "URI": "장비 렌탈 · 건설 경기",
    "NSC": "철도 물류 · 화물 운송",
    "DLR": "데이터센터 리츠",
    "RKLB": "우주 발사체 · 위성",
    "NKE": "스포츠웨어 · 브랜드 소비재",
    "CRM": "기업용 세일즈 클라우드",
    "VMC": "골재 · 건자재",
    "IRM": "문서보관 · 데이터센터 리츠",
    "EL": "화장품 · 뷰티 브랜드",
    "CNP": "전력 · 가스 유틸리티",
    "ES": "전력 · 가스 유틸리티",
    "STE": "의료 멸균 · 감염관리",
    "KIM": "쇼핑센터 리츠",
    "ALAB": "AI 데이터센터 연결 반도체",
    "CRWV": "AI 클라우드 · GPU 인프라",
    "NBIS": "AI 클라우드 · 데이터센터",
    "PL": "위성 데이터 · 지구 관측",
    "QXO": "건자재 유통 · 산업 인프라",
    "PGY": "AI 신용평가 · 핀테크",
    "IONQ": "양자컴퓨팅 · 하드웨어",
    "IREN": "AI 데이터센터 · 비트코인 채굴",
    "HUT": "비트코인 채굴 · 데이터센터",
    "EOSE": "장주기 ESS · 아연 배터리",
    "BE": "연료전지 · 분산 전력",
    "LPTH": "광학 렌즈 · 포토닉스",
    "ASTS": "위성 통신 · 우주 인터넷",
    "TSM": "파운드리 · 첨단 공정",
    "SMR": "소형모듈원전 · 원전 기술",
    "OKLO": "차세대 원전 · 소형 원자로",
    "SEI": "데이터센터 전력 · 에너지 인프라",
    "WTS": "데이터센터 냉각 · 물 인프라",
    "RGTI": "양자컴퓨팅 · 초전도 큐비트",
    "QBTS": "양자컴퓨팅 · 어닐링 시스템",
    "TEM": "AI 의료 데이터 · 정밀의학",
    "CRDO": "AI 데이터센터 연결 반도체",
    "CLS": "AI 서버 제조 · 전자 제조서비스",
    "ACHR": "eVTOL · 도심항공교통",
    "JOBY": "eVTOL · 항공 모빌리티",
    "SERV": "자율주행 배달 로봇",
    "SPCX": "우주 발사체 · 위성 인터넷",
    "GLXY": "크립토 금융 · AI 데이터센터",
    "QUBT": "양자 소프트웨어 · 포토닉스",
    "TSEM": "아날로그 반도체 · 파운드리",
    "MKSI": "반도체 장비 · 포토닉스",
    "CIFR": "비트코인 채굴 · HPC 인프라",
    "CORZ": "AI 데이터센터 · 비트코인 채굴",
    "CLSK": "비트코인 채굴 · 전력 효율",
    "RDDT": "커뮤니티 플랫폼 · AI 데이터",
    "BBAI": "국방 AI · 데이터 분석",
    "AI": "기업용 AI 소프트웨어",
    "CRCL": "스테이블코인 · 결제 인프라",
    "SOFI": "디지털 금융 · 개인 대출",
    "UPST": "AI 신용평가 · 핀테크",
    "OPEN": "온라인 부동산 · 주택 거래",
    "NNE": "마이크로 원전 · 핵연료",
    "LEU": "우라늄 농축 · 원전 연료",
    "CCJ": "우라늄 채굴 · 원전 연료",
    "LUNR": "달 탐사 · 우주 인프라",
    "KULR": "배터리 안전 · 열관리",
    "AEHR": "반도체 테스트 · 실리콘카바이드",
    "POET": "광인터커넥트 · AI 포토닉스",
    "LAES": "양자보안 칩 · 반도체 보안",
    "ARQQ": "양자보안 · 암호화 기술",
})

US_INDUSTRY_MAP.update({
    "Semiconductor Equipment & Materials": "반도체 장비 · 소재",
    "Computer Hardware": "컴퓨터 하드웨어 · 데이터 인프라",
    "Capital Markets": "투자은행 · 자본시장",
    "Specialty Industrial Machinery": "전문 산업기계",
    "Aerospace & Defense": "항공우주 · 방산",
    "Electronic Components": "전자부품",
    "Telecom Services": "통신 서비스",
    "Apparel Retail": "의류 리테일",
    "Asset Management": "자산운용",
    "REIT - Healthcare Facilities": "헬스케어 리츠",
    "Railroads": "철도 운송",
    "Farm & Heavy Construction Machinery": "농기계 · 중장비",
    "Advertising Agencies": "광고 플랫폼",
    "Conglomerates": "복합 산업재",
    "Travel Services": "여행 서비스",
    "REIT - Industrial": "물류 리츠",
    "REIT - Specialty": "특수 리츠",
    "REIT - Retail": "리테일 리츠",
    "Electrical Equipment & Parts": "전력장비 · 부품",
    "Insurance - Property & Casualty": "손해보험",
    "Home Improvement Retail": "주택개선 리테일",
    "Financial Data & Stock Exchanges": "금융데이터 · 거래소",
    "Tobacco": "담배 · 니코틴",
    "Restaurants": "외식 프랜차이즈",
    "Biotechnology": "바이오테크",
    "Gold": "금광 · 귀금속",
    "Building Products & Equipment": "빌딩 설비 · 장비",
    "Engineering & Construction": "엔지니어링 · 건설",
    "Utilities - Regulated Electric": "전력 유틸리티",
    "Utilities - Independent Power Producers": "민자 발전 · 전력",
    "Lodging": "호텔 · 숙박",
    "Copper": "구리 · 광산",
    "Banks - Regional": "지역은행",
    "Oil & Gas Midstream": "천연가스 파이프라인",
    "Integrated Freight & Logistics": "종합 물류",
    "Medical Distribution": "의약품 유통",
    "Waste Management": "폐기물 처리",
    "Specialty Chemicals": "특수화학",
    "Insurance Brokers": "보험 중개",
    "Confectioners": "제과 · 스낵",
    "Scientific & Technical Instruments": "정밀 계측장비",
    "Building Materials": "건자재",
    "Auto & Truck Dealerships": "자동차 판매",
    "Auto Parts": "자동차 부품",
    "Oil & Gas Equipment & Services": "유전 서비스",
    "Household & Personal Products": "생활용품",
    "Auto Manufacturers": "자동차 제조",
    "Oil & Gas Refining & Marketing": "정유 · 에너지",
    "Oil & Gas E&P": "석유 · 가스 개발",
    "Rental & Leasing Services": "렌탈 · 리스",
    "Footwear & Accessories": "신발 · 스포츠웨어",
})

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


def normalize_us_symbol(symbol):
    return str(symbol).strip().replace(".", "-")


def extract_us_symbol(item):
    if isinstance(item, dict):
        item = item.get("ticker") or item.get("symbol") or ""

    return normalize_us_symbol(item)


def dedupe_tickers(tickers):
    seen = set()
    unique = []

    for ticker in tickers:
        normalized = extract_us_symbol(ticker)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(normalized)

    return unique


def read_cached_us_universe():
    try:
        if not US_UNIVERSE_CACHE.exists():
            return None

        payload = json.loads(US_UNIVERSE_CACHE.read_text(encoding="utf-8"))
        created_at = float(payload.get("created_at", 0))

        if time.time() - created_at > US_UNIVERSE_CACHE_TTL:
            return None

        tickers = payload.get("tickers") or []

        if len(tickers) < 100:
            return None

        return dedupe_tickers(tickers)
    except Exception as error:
        print(f"[US UNIVERSE CACHE ERROR] {error}")
        return None


def save_cached_us_universe(tickers):
    try:
        US_UNIVERSE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        US_UNIVERSE_CACHE.write_text(
            json.dumps(
                {
                    "created_at": time.time(),
                    "tickers": tickers,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as error:
        print(f"[US UNIVERSE CACHE SAVE ERROR] {error}")


def read_wikipedia_tickers(url, column_name):
    try:
        import pandas as pd

        tables = pd.read_html(url)

        for table in tables:
            if column_name in table.columns:
                return dedupe_tickers(table[column_name].dropna().tolist())
    except Exception as error:
        print(f"[US UNIVERSE FETCH ERROR] {url}: {error}")

    return []


def read_local_us_index_tickers(group_key=None):
    try:
        settings = json.loads(US_INDEX_GROUPS_FILE.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"[US LOCAL INDEX ERROR] {error}")
        settings = {}

    tickers = []

    for group in settings.get("US", []):
        if group_key and group.get("key") != group_key:
            continue

        source_file = group.get("source_file")

        if not source_file:
            continue

        try:
            data = json.loads((APP_DATA_DIR / source_file).read_text(encoding="utf-8"))
        except Exception as error:
            print(f"[US LOCAL INDEX FILE ERROR] {source_file}: {error}")
            continue

        tickers.extend(data)

    return dedupe_tickers(tickers)


def ensure_tickers_included(tickers, required_tickers):
    combined = list(tickers)
    seen = set(combined)

    for ticker in required_tickers:
        if ticker in seen:
            continue

        seen.add(ticker)
        combined.append(ticker)

    return combined


def normalize_kr_symbol(code):
    clean_code = str(code).strip().zfill(6)
    return f"{clean_code}.KS"


def classify_kr_sector(name, raw_sector=""):
    text = f"{name} {raw_sector}".lower()

    rules = [
        ("반도체", ["반도체", "하이닉스", "삼성전자", "db하이텍", "리노공업"]),
        ("이차전지", ["배터리", "2차전지", "이차전지", "에너지솔루션", "sdi", "엘앤에프", "포스코퓨처"]),
        ("자동차", ["자동차", "현대차", "기아", "모비스", "만도", "타이어", "전장"]),
        ("바이오·헬스케어", ["바이오", "제약", "의약", "헬스", "셀트리온", "유한양행", "한미약품"]),
        ("금융", ["금융", "은행", "보험", "증권", "카드", "캐피탈", "지주"]),
        ("인터넷 플랫폼", ["naver", "카카오", "인터넷", "플랫폼", "게임", "엔터", "콘텐츠"]),
        ("정유·에너지", ["정유", "석유", "가스", "에너지", "s-oil", "이노베이션"]),
        ("철강·화학", ["철강", "화학", "소재", "포스코", "금속", "비철", "고무"]),
        ("조선·해운", ["조선", "해운", "해양", "중공업", "팬오션", "hmm"]),
        ("건설·인프라", ["건설", "시멘트", "건자재", "기계", "플랜트", "엔지니어링"]),
        ("유틸리티·가스", ["전력", "전기", "가스", "유틸", "한국전력", "지역난방"]),
        ("통신", ["통신", "텔레콤", "텔레콤", "kt", "skt", "유플러스"]),
        ("소비재", ["식품", "음료", "화장품", "생활", "유통", "백화점", "마트", "호텔", "여행"]),
        ("방산·항공우주", ["방산", "항공", "우주", "한화에어로", "kai", "한국항공"]),
        ("지주사·종합상사", ["상사", "홀딩스", "지주", "물산"]),
    ]

    for sector, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return sector

    return raw_sector or "기타"


def get_local_kr_listings(path, fallback_listings, fallback_description):
    try:
        listings = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"[KR LOCAL LIST ERROR] {path.name}: {error}")
        listings = fallback_listings

    normalized = []
    seen = set()

    for item in listings:
        code = str(
            item.get("code") or
            item.get("ticker", "").replace(".KS", "").replace(".KQ", "")
        ).zfill(6)
        ticker = item.get("ticker") or normalize_kr_symbol(code)

        if ticker in seen:
            continue

        seen.add(ticker)
        name = item.get("name") or code
        raw_sector = item.get("sector") or ""

        normalized.append({
            "ticker": ticker,
            "code": code,
            "name": name,
            "sector": classify_kr_sector(name, raw_sector),
            "description": item.get("description") or raw_sector or fallback_description,
        })

    return normalized


def get_kospi_listings():
    return get_local_kr_listings(
        KOSPI_LISTINGS_FILE,
        FALLBACK_KOSPI_LISTINGS,
        "KOSPI",
    )


def get_kosdaq_listings():
    return get_local_kr_listings(
        KOSDAQ_LISTINGS_FILE,
        [],
        "KOSDAQ",
    )


def get_kr_listings():
    return get_kospi_listings() + get_kosdaq_listings()


def get_kospi_listing_map():
    return {
        listing["ticker"]: listing
        for listing in get_kospi_listings()
    }


def get_kr_listing_map():
    return {
        listing["ticker"]: listing
        for listing in get_kr_listings()
    }


def get_us_ticker_universe():
    local_tickers = read_local_us_index_tickers()

    if local_tickers:
        limited_tickers = apply_us_scan_limit(local_tickers)
        return ensure_tickers_included(limited_tickers, read_local_us_index_tickers("etc"))

    cached = read_cached_us_universe()

    if cached:
        return apply_us_scan_limit(cached)

    nasdaq100 = read_wikipedia_tickers(
        "https://en.wikipedia.org/wiki/Nasdaq-100",
        "Ticker",
    )
    sp500 = read_wikipedia_tickers(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "Symbol",
    )
    tickers = dedupe_tickers(nasdaq100 + sp500)

    if len(tickers) < 100:
        tickers = dedupe_tickers(FALLBACK_US_TICKERS)
    else:
        save_cached_us_universe(tickers)

    return apply_us_scan_limit(tickers)


def get_us_index_tickers():
    return {
        "sp500": read_wikipedia_tickers(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            "Symbol",
        ),
        "sp400": read_wikipedia_tickers(
            "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
            "Symbol",
        ),
        "sp600": read_wikipedia_tickers(
            "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies",
            "Symbol",
        ),
        "nasdaq100": read_wikipedia_tickers(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            "Ticker",
        ),
    }


def apply_us_scan_limit(tickers):
    raw_limit = os.getenv("US_SCAN_LIMIT", "").strip()

    if not raw_limit:
        return tickers

    try:
        limit = int(raw_limit)
    except ValueError:
        return tickers

    if limit <= 0:
        return tickers

    return tickers[:limit]


def get_stock_info_cache_path(ticker):
    safe_ticker = ticker.replace("/", "-").replace(".", "-")
    return APP_CACHE_DIR / "stock_info" / f"{safe_ticker}.json"


def read_cached_stock_info(ticker):
    path = get_stock_info_cache_path(ticker)

    try:
        if not path.exists():
            return None

        payload = json.loads(path.read_text(encoding="utf-8"))
        created_at = float(payload.get("created_at", 0))

        if time.time() - created_at > STOCK_INFO_CACHE_TTL:
            return None

        info = payload.get("info")

        if not isinstance(info, dict):
            return None

        return info
    except Exception as error:
        print(f"[INFO CACHE ERROR] {ticker}: {error}")
        return None


def save_cached_stock_info(ticker, info):
    path = get_stock_info_cache_path(ticker)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "created_at": time.time(),
                    "info": info,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as error:
        print(f"[INFO CACHE SAVE ERROR] {ticker}: {error}")


def has_korean(text):
    return any("가" <= char <= "힣" for char in str(text or ""))


def cleanup_us_company_name(name):
    cleaned = str(name or "").strip()

    if not cleaned:
        return ""

    replacements = [
        "Corporation",
        "Company",
        "Incorporated",
        "International",
        "Technologies",
        "Technology",
        "Holdings",
        "Holding",
        "Systems",
        "Services",
        "Group",
        "Limited",
        "Common Stock",
        "Common St",
        "Class A",
        "Class B",
        "Class C",
        "New",
        "Inc.",
        "Inc",
        "Corp.",
        "Corp",
        "PLC",
        "plc",
        "(The)",
        "The ",
    ]

    for value in replacements:
        cleaned = cleaned.replace(value, "")

    return " ".join(cleaned.replace(",", " ").replace("  ", " ").split()) or name


def get_us_display_name(ticker, fallback_name):
    ticker = str(ticker or "").upper()

    if ticker in US_KOREAN_NAME_MAP:
        return US_KOREAN_NAME_MAP[ticker]

    fallback_name = fallback_name or ticker

    if has_korean(fallback_name):
        return fallback_name

    return cleanup_us_company_name(fallback_name) or ticker


def get_us_display_description(ticker, fallback_description="", fallback_sector=""):
    ticker = str(ticker or "").upper()

    if ticker in US_DESCRIPTION_MAP:
        return US_DESCRIPTION_MAP[ticker]

    for value in [fallback_description, fallback_sector]:
        value = str(value or "").strip()

        if not value:
            continue

        if value in US_INDUSTRY_MAP:
            return US_INDUSTRY_MAP[value]

        if value in US_SECTOR_MAP:
            return US_SECTOR_MAP[value]

        if has_korean(value):
            return value

    return "미국 주식 · 세부 정보 확인"


def get_market_tickers(market: str):
    if market == "KR":
        return [listing["ticker"] for listing in get_kr_listings()]

    return get_us_ticker_universe()


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
    if market == "KR" or ticker.endswith(".KS") or ticker.endswith(".KQ"):
        listing = get_kr_listing_map().get(ticker)

        if not listing and ticker in KR_STOCK_INFO:
            info = KR_STOCK_INFO[ticker]
            sector = KR_SECTOR_MAP.get(info["sector"], info["sector"])
            listing = {
                "ticker": ticker,
                "name": info["name"],
                "sector": sector,
                "description": info["description"],
            }

        if not listing:
            listing = {
                "ticker": ticker,
                "name": ticker.replace(".KS", "").replace(".KQ", ""),
                "sector": "기타",
                "description": "KR",
            }

        market_cap = 0
        average_volume = 0

        try:
            stock = yf.Ticker(ticker)
            fast_info = stock.fast_info
            market_cap = fast_info.get("marketCap") or fast_info.get("market_cap") or 0
            average_volume = (
                fast_info.get("threeMonthAverageVolume") or
                fast_info.get("three_month_average_volume") or
                fast_info.get("tenDayAverageVolume") or
                fast_info.get("ten_day_average_volume") or
                0
            )

            if not market_cap or not average_volume:
                info = stock.info
                market_cap = market_cap or info.get("marketCap") or 0
                average_volume = (
                    average_volume or
                    info.get("averageVolume") or
                    info.get("averageVolume10days") or
                    0
                )
        except Exception as error:
            print(f"[KR FAST INFO ERROR] {ticker}: {error}")

        return {
            "ticker": ticker,
            "name": listing["name"],
            "sector": listing["sector"],
            "description": listing["description"],
            "price": 0,
            "target": 0,
            "roe": 0,
            "earnings_growth": 0,
            "market_cap": market_cap,
            "average_volume": average_volume,
        }

    cached_info = read_cached_stock_info(ticker)

    if cached_info:
        cached_info = cached_info.copy()
        cached_info["name"] = get_us_display_name(ticker, cached_info.get("name"))
        cached_info["description"] = get_us_display_description(
            ticker,
            cached_info.get("description"),
            cached_info.get("sector"),
        )
        cached_info["sector"] = get_us_display_description(
            "",
            cached_info.get("sector"),
            cached_info.get("sector"),
        )
        return cached_info

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

    description = get_us_display_description(ticker, raw_industry, raw_sector)

    stock_info = {
        "ticker": ticker,
        "name": get_us_display_name(ticker, info.get("shortName", ticker)),
        "sector": sector,
        "description": description,
        "price": info.get("currentPrice") or 0,
        "target": info.get("targetMeanPrice") or 0,
        "roe": float(info.get("returnOnEquity") or 0),
        "earnings_growth": float(info.get("earningsGrowth") or 0),
        "market_cap": info.get("marketCap") or 0,
        "average_volume": info.get("averageVolume") or 0,
    }
    save_cached_stock_info(ticker, stock_info)

    return stock_info


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


def format_event_date(value):
    if not value:
        return None

    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).date().isoformat()

        if hasattr(value, "date"):
            return value.date().isoformat()

        return datetime.fromisoformat(str(value).split(" ")[0]).date().isoformat()
    except Exception:
        return None


def format_transaction_value(value):
    try:
        number = float(value)
    except Exception:
        return "—"

    if number == 0:
        return "$0"

    abs_number = abs(number)
    sign = "-" if number < 0 else ""

    if abs_number >= 1_000_000:
        return f"{sign}${round(abs_number / 1_000_000, 2)}M"

    if abs_number >= 1_000:
        return f"{sign}${round(abs_number / 1_000, 1)}K"

    return f"{sign}${round(abs_number, 2)}"


def get_insider_net_summary(net_total):
    if net_total > 0:
        return "순취득", "buy", format_transaction_value(net_total)

    if net_total < 0:
        return "순처분", "sell", format_transaction_value(abs(net_total))

    return "순매매", "neutral", "$0"


def get_column_value(row, names, default=None):
    for name in names:
        if name in row and row[name] == row[name]:
            return row[name]

    return default


def classify_insider_transaction(transaction, shares=0, value=0):
    text = str(transaction or "").strip()
    normalized = text.lower().replace("_", " ")
    compact = normalized.replace(".", " ").replace("-", " ")
    tokens = set(compact.split())

    sell_keywords = [
        "sale",
        "sell",
        "sold",
        "disposition",
        "disposed",
        "tax withholding",
        "taxwithholding",
        "withholding",
    ]
    buy_keywords = [
        "purchase",
        "buy",
        "bought",
        "acquisition",
        "acquired",
        "grant",
        "award",
    ]
    option_keywords = [
        "option",
        "exercise",
        "conversion",
        "derivative",
    ]

    # SEC Form 4 transaction codes commonly appear as a single letter or
    # as a prefix like "S - Sale" / "A - Grant". Classify those explicitly.
    if "s" in tokens or any(keyword in normalized for keyword in sell_keywords):
        return "처분", "sell"

    if "p" in tokens or "a" in tokens or any(keyword in normalized for keyword in buy_keywords):
        return "취득", "buy"

    if "m" in tokens or any(keyword in normalized for keyword in option_keywords):
        return "옵션행사", "option"

    if "d" in tokens or "f" in tokens:
        return "처분", "sell"

    if "g" in tokens or "gift" in normalized:
        return "증여", "other"

    shares = safe_numeric_value(shares)
    value = safe_numeric_value(value)

    if shares < 0 or value < 0:
        return "처분", "sell"

    if value > 0 and ("$" in text or any(unit in normalized for unit in [" k", " m", " b"])):
        return "처분", "sell"

    return "기타", "other"


def safe_numeric_value(value):
    try:
        if isinstance(value, str):
            text = value.strip().upper().replace("$", "").replace(",", "")
            multiplier = 1

            if text.endswith("B"):
                multiplier = 1_000_000_000
                text = text[:-1]
            elif text.endswith("M"):
                multiplier = 1_000_000
                text = text[:-1]
            elif text.endswith("K"):
                multiplier = 1_000
                text = text[:-1]

            return float(text or 0) * multiplier

        return float(value or 0)
    except Exception:
        return 0.0


def get_insider_transactions(ticker: str, limit: int = 8):
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return {
            "buy_total": "$0",
            "sell_total": "$0",
            "net_total": "$0",
            "net_label": "순매매",
            "net_type": "neutral",
            "count": 0,
            "items": [],
            "source": "SEC Form 4 (yfinance) · 한국 종목은 미지원",
        }

    try:
        stock = yf.Ticker(ticker)
        transactions = stock.insider_transactions
    except Exception as error:
        print(f"[INSIDER ERROR] {ticker}: {error}")
        transactions = None

    if transactions is None or getattr(transactions, "empty", True):
        return {
            "buy_total": "$0",
            "sell_total": "$0",
            "net_total": "$0",
            "net_label": "순매매",
            "net_type": "neutral",
            "count": 0,
            "items": [],
            "source": "SEC Form 4 (yfinance)",
        }

    items = []
    buy_total = 0.0
    sell_total = 0.0

    for _, row in transactions.head(limit).iterrows():
        date_value = get_column_value(row, ["Start Date", "Date", "startDate"])
        holder = get_column_value(row, ["Insider", "Holder", "Name"], "Unknown")
        position = get_column_value(row, ["Position", "Relationship"], "")
        transaction = str(get_column_value(row, ["Text", "Type", "Code", "Transaction"], "기타"))
        shares = get_column_value(row, ["Shares", "Shares Traded", "Transaction Shares"], 0)
        value = get_column_value(row, ["Value", "Shares Value", "Transaction Value"], 0)

        numeric_value = safe_numeric_value(value)
        numeric_shares = safe_numeric_value(shares)
        action, action_type = classify_insider_transaction(
            transaction=transaction,
            shares=numeric_shares,
            value=numeric_value,
        )

        if action_type == "sell":
            sell_total += abs(numeric_value)
        elif action_type == "buy":
            buy_total += abs(numeric_value)

        items.append({
            "date": format_event_date(date_value) or "—",
            "action": action,
            "action_type": action_type,
            "holder": str(holder),
            "position": str(position or transaction),
            "value": format_transaction_value(numeric_value),
        })

    net_total = buy_total - sell_total
    net_label, net_type, net_value = get_insider_net_summary(net_total)

    return {
        "buy_total": format_transaction_value(buy_total),
        "sell_total": format_transaction_value(sell_total),
        "net_total": net_value,
        "net_label": net_label,
        "net_type": net_type,
        "count": len(items),
        "items": items,
        "source": "SEC Form 4 (yfinance) · 옵션행사·증여는 별도 분류",
    }


def get_stock_events(ticker: str, days: int = 120):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
    except Exception as error:
        print(f"[EVENT ERROR] {ticker}: {error}")
        info = {}

    now = datetime.now().date()
    until = now + timedelta(days=days)
    events = []

    def append_event(raw_date, label, event_type):
        event_date = format_event_date(raw_date)

        if not event_date:
            return

        parsed = datetime.fromisoformat(event_date).date()

        if parsed < now or parsed > until:
            return

        days_left = (parsed - now).days
        d_label = "D-day" if days_left == 0 else f"D-{days_left}"

        events.append({
            "date": event_date,
            "d_label": d_label,
            "label": label,
            "type": event_type,
        })

    append_event(info.get("earningsTimestamp"), "실적 발표", "실적")
    append_event(info.get("exDividendDate"), "배당락", "배당")
    append_event(info.get("dividendDate"), "배당 지급", "배당")

    try:
        calendar = stock.calendar
    except Exception:
        calendar = None

    if calendar is not None:
        try:
            if isinstance(calendar, dict):
                earnings_date = calendar.get("Earnings Date")
            else:
                earnings_date = calendar.loc["Earnings Date"][0]

            if isinstance(earnings_date, (list, tuple)):
                earnings_date = earnings_date[0]

            append_event(earnings_date, "실적 발표", "실적")
        except Exception:
            pass

    unique_events = []
    seen = set()

    for event in sorted(events, key=lambda item: item["date"]):
        key = (event["date"], event["label"])

        if key in seen:
            continue

        seen.add(key)
        unique_events.append(event)

    return {
        "count": len(unique_events),
        "items": unique_events,
        "source": "yfinance 캘린더 · 매크로(FOMC/CPI 등)는 상단 스트립에서 확인",
    }
