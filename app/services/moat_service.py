import math


MOAT_AXES = [
    ("switching_cost", "전환비용", "고객이 다른 제품으로 갈아타기 어려운 정도"),
    ("network_effect", "네트워크 효과", "사용자가 많을수록 서비스 가치가 커지는 정도"),
    ("intangible_assets", "무형자산", "브랜드·특허·규제 자산처럼 모방이 어려운 자산"),
    ("cost_advantage", "원가 우위", "규모·공정·조달력으로 더 싸게 만들 수 있는 구조"),
    ("roic_durability", "ROIC 지속성", "투자 대비 수익률을 꾸준히 유지할 가능성"),
]


MOAT_OVERRIDES = {
    "AAPL": (2.0, 1.5, 2.0, 1.5, 2.0),
    "MSFT": (2.0, 1.5, 2.0, 1.5, 2.0),
    "GOOGL": (1.5, 2.0, 2.0, 1.5, 2.0),
    "GOOG": (1.5, 2.0, 2.0, 1.5, 2.0),
    "NVDA": (1.5, 1.5, 2.0, 1.5, 2.0),
    "AMZN": (1.5, 2.0, 2.0, 2.0, 1.5),
    "META": (1.0, 2.0, 2.0, 1.5, 1.5),
    "AVGO": (1.5, 1.0, 1.5, 2.0, 2.0),
    "TSLA": (1.0, 1.0, 2.0, 1.5, 1.0),
    "V": (2.0, 2.0, 2.0, 1.5, 2.0),
    "MA": (2.0, 2.0, 2.0, 1.5, 2.0),
    "COST": (1.5, 1.0, 2.0, 2.0, 2.0),
    "KO": (1.0, 1.0, 2.0, 2.0, 2.0),
    "PEP": (1.0, 1.0, 2.0, 2.0, 1.5),
    "MCD": (1.0, 1.0, 2.0, 2.0, 1.5),
    "JPM": (1.5, 1.0, 1.5, 1.5, 1.5),
    "BRK-B": (1.0, 1.0, 2.0, 1.5, 2.0),
    "ASML": (2.0, 1.0, 2.0, 2.0, 2.0),
    "TSM": (2.0, 1.0, 2.0, 2.0, 2.0),
    "005930": (1.5, 1.0, 2.0, 2.0, 1.5),
    "000660": (1.5, 1.0, 1.5, 1.5, 1.0),
    "035420": (1.5, 2.0, 2.0, 1.0, 1.0),
    "035720": (1.5, 2.0, 1.5, 1.0, 0.5),
    "005380": (1.0, 1.0, 2.0, 1.5, 1.0),
    "000270": (1.0, 1.0, 2.0, 1.5, 1.0),
    "ALAB": (1.5, 1.0, 1.5, 1.0, 1.0),
    "CRWV": (1.5, 1.5, 1.0, 1.0, 0.8),
    "NBIS": (1.2, 1.0, 1.0, 1.0, 0.8),
    "PL": (1.0, 0.8, 1.2, 0.6, 0.5),
    "QXO": (0.8, 0.5, 0.8, 1.0, 0.5),
    "PGY": (1.0, 1.0, 1.0, 0.6, 0.5),
    "IONQ": (1.0, 0.8, 1.5, 0.5, 0.5),
    "IREN": (0.7, 0.6, 0.5, 1.0, 0.4),
    "HUT": (0.6, 0.5, 0.5, 0.8, 0.4),
    "EOSE": (0.8, 0.4, 1.0, 0.8, 0.4),
    "BE": (1.0, 0.6, 1.2, 1.0, 0.6),
    "LPTH": (0.8, 0.4, 1.0, 0.6, 0.4),
    "ASTS": (1.0, 1.0, 1.5, 0.5, 0.4),
    "SMR": (1.0, 0.4, 1.2, 0.6, 0.4),
    "OKLO": (1.0, 0.4, 1.3, 0.6, 0.4),
    "SEI": (0.8, 0.5, 0.6, 1.0, 0.7),
    "WTS": (1.0, 0.5, 1.0, 1.2, 1.2),
    "RGTI": (0.8, 0.6, 1.2, 0.4, 0.3),
    "QBTS": (0.8, 0.6, 1.2, 0.4, 0.3),
    "TEM": (1.0, 0.8, 1.2, 0.5, 0.4),
    "CRDO": (1.2, 0.8, 1.2, 1.0, 0.8),
    "CLS": (0.8, 0.5, 0.7, 1.2, 1.0),
    "ACHR": (0.8, 0.5, 1.2, 0.5, 0.3),
    "JOBY": (0.8, 0.5, 1.2, 0.5, 0.3),
    "SERV": (0.8, 0.6, 1.0, 0.4, 0.2),
    "SPCX": (1.5, 1.5, 2.0, 1.0, 0.8),
    "GLXY": (0.8, 0.8, 1.0, 0.8, 0.6),
    "QUBT": (0.8, 0.6, 1.2, 0.4, 0.3),
    "TSEM": (1.0, 0.6, 1.0, 1.0, 0.8),
    "MKSI": (1.0, 0.6, 1.0, 1.0, 0.8),
    "CIFR": (0.6, 0.4, 0.4, 0.8, 0.3),
    "CORZ": (0.6, 0.5, 0.5, 0.8, 0.4),
    "CLSK": (0.6, 0.4, 0.5, 0.8, 0.4),
    "RDDT": (1.0, 1.5, 1.5, 0.6, 0.5),
    "BBAI": (0.8, 0.5, 0.8, 0.5, 0.3),
    "AI": (1.0, 0.8, 1.0, 0.5, 0.4),
    "CRCL": (1.0, 1.2, 1.0, 0.8, 0.4),
    "SOFI": (1.0, 0.8, 1.0, 0.7, 0.5),
    "UPST": (1.0, 0.6, 1.0, 0.5, 0.3),
    "OPEN": (0.6, 0.5, 0.6, 0.5, 0.2),
    "NNE": (0.8, 0.4, 1.2, 0.5, 0.3),
    "LEU": (1.2, 0.5, 1.2, 1.0, 0.8),
    "CCJ": (1.0, 0.5, 1.0, 1.2, 1.0),
    "LUNR": (0.8, 0.5, 1.0, 0.5, 0.3),
    "KULR": (0.8, 0.5, 1.0, 0.6, 0.3),
    "AEHR": (0.9, 0.5, 1.0, 0.8, 0.5),
    "POET": (0.9, 0.6, 1.1, 0.5, 0.3),
    "LAES": (0.8, 0.5, 1.1, 0.5, 0.2),
    "ARQQ": (0.8, 0.5, 1.1, 0.4, 0.2),
}


def clamp_score(value, minimum=0.0, maximum=2.0):
    try:
        number = float(value)
    except Exception:
        return minimum

    if math.isnan(number) or math.isinf(number):
        return minimum

    return max(minimum, min(maximum, number))


def normalize_symbol(ticker):
    return str(ticker or "").upper().replace(".KS", "").replace(".KQ", "").replace(".", "-")


def keyword_score(text, keyword_groups):
    score = 0.0
    lowered = str(text or "").lower()

    for keywords, points in keyword_groups:
        if any(keyword.lower() in lowered for keyword in keywords):
            score += points

    return clamp_score(score)


def roic_durability_score(info):
    roe = 0.0
    earnings_growth = 0.0

    if isinstance(info, dict):
        try:
            roe = float(info.get("roe") or 0) * 100
        except Exception:
            roe = 0.0

        try:
            earnings_growth = float(info.get("earnings_growth") or 0) * 100
        except Exception:
            earnings_growth = 0.0

    score = 0.5

    if roe >= 30:
        score += 1.2
    elif roe >= 17:
        score += 0.9
    elif roe >= 10:
        score += 0.5

    if earnings_growth >= 25:
        score += 0.4
    elif earnings_growth >= 10:
        score += 0.2

    return clamp_score(score)


def build_moat(ticker="", name="", sector="", description="", info=None):
    symbol = normalize_symbol(ticker)

    if symbol in MOAT_OVERRIDES:
        scores = MOAT_OVERRIDES[symbol]
    else:
        text = " ".join([str(name or ""), str(sector or ""), str(description or "")])
        scores = (
            keyword_score(text, [
                (["클라우드", "소프트웨어", "saas", "erp", "crm", "데이터센터", "플랫폼"], 1.0),
                (["결제", "금융데이터", "거래소", "반도체 장비", "의료기기"], 0.6),
                (["소비재", "리테일", "정유", "원자재"], 0.3),
            ]),
            keyword_score(text, [
                (["플랫폼", "검색", "광고", "커머스", "전자상거래", "결제", "거래소"], 1.2),
                (["유튜브", "sns", "메신저", "네트워크", "카카오", "naver"], 0.8),
            ]),
            keyword_score(text, [
                (["브랜드", "특허", "제약", "바이오", "반도체", "로봇", "명품", "스포츠웨어"], 1.1),
                (["애플", "코카콜라", "나이키", "삼성", "현대", "테슬라"], 0.8),
            ]),
            keyword_score(text, [
                (["파운드리", "반도체", "대형마트", "리테일", "정유", "철강", "배터리", "물류"], 1.0),
                (["규모", "원가", "생산", "제조", "장비"], 0.6),
            ]),
            roic_durability_score(info),
        )

    total = round(sum(clamp_score(score) for score in scores), 1)

    if total >= 8:
        label = "강한 해자"
    elif total >= 6:
        label = "쓸만한 해자"
    elif total >= 4:
        label = "보통 해자"
    else:
        label = "약한 해자"

    axes = []

    for (key, label_text, description_text), score in zip(MOAT_AXES, scores):
        axes.append({
            "key": key,
            "label": label_text,
            "description": description_text,
            "score": round(clamp_score(score), 1),
            "max_score": 2,
        })

    return {
        "switching_cost": axes[0]["score"],
        "network_effect": axes[1]["score"],
        "intangible_assets": axes[2]["score"],
        "cost_advantage": axes[3]["score"],
        "roic_durability": axes[4]["score"],
        "total": total,
        "max_score": 10,
        "label": label,
        "summary": f"{label} · 해자 {total}/10",
        "axes": axes,
    }
