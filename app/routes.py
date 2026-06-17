from flask import Blueprint, render_template

main = Blueprint("main", __name__)

STOCKS = [
    {
        "rank": 1,
        "ticker": "GOOGL",
        "name": "알파벳",
        "description": "검색 · 유튜브 · 클라우드",
        "sector": "Mag 7",
        "score": 91,
        "signal": "근접 구간 · 지지",
        "signal_type": "green",
        "price": 371.52,
        "change": 3.29,
        "rsi": 51.4,
        "target": 436.92,
        "target_change": 17.6,
        "reason": ["RS88", "EPS↑", "ROE39%"]
    },
    {
        "rank": 2,
        "ticker": "NVDA",
        "name": "엔비디아",
        "description": "AI GPU · 블랙웰 · HBM",
        "sector": "Mag 7",
        "score": 88,
        "signal": "관망 · RSI",
        "signal_type": "yellow",
        "price": 225.15,
        "change": 1.98,
        "rsi": 71.8,
        "target": 269.95,
        "target_change": 19.9,
        "reason": ["RS88", "EPS↑", "AI"]
    },
    {
        "rank": 3,
        "ticker": "AMZN",
        "name": "아마존",
        "description": "AWS · 이커머스 · 광고",
        "sector": "Mag 7",
        "score": 76,
        "signal": "관망 · VWAP",
        "signal_type": "yellow",
        "price": 265.64,
        "change": -0.07,
        "rsi": 63.5,
        "target": 311.55,
        "target_change": 17.3,
        "reason": ["EPS↑", "ROE24%", "목표가↑"]
    },
    {
        "rank": 4,
        "ticker": "AAPL",
        "name": "애플",
        "description": "아이폰 · 맥 · 애플 실리콘",
        "sector": "Mag 7",
        "score": 69,
        "signal": "주의 · 과열",
        "signal_type": "red",
        "price": 296.49,
        "change": 0.57,
        "rsi": 74.7,
        "target": 305.28,
        "target_change": 3.0,
        "reason": ["ROE141%", "RSI75", "신고가"]
    },
    {
        "rank": 5,
        "ticker": "MSFT",
        "name": "마이크로소프트",
        "description": "애저 · 클라우드 · 코파일럿",
        "sector": "Mag 7",
        "score": 47,
        "signal": "관망",
        "signal_type": "yellow",
        "price": 402.39,
        "change": -1.32,
        "rsi": 45.7,
        "target": 561.56,
        "target_change": 39.6,
        "reason": ["ROE34%", "목표가↑"]
    },
    {
        "rank": 6,
        "ticker": "META",
        "name": "메타",
        "description": "페북 · 인스타 · 광고 플랫폼",
        "sector": "Mag 7",
        "score": 47,
        "signal": "관망",
        "signal_type": "yellow",
        "price": 605.48,
        "change": 0.41,
        "rsi": 42.0,
        "target": 826.69,
        "target_change": 36.5,
        "reason": ["EPS↑", "ROE33%"]
    },
    {
        "rank": 7,
        "ticker": "TSLA",
        "name": "테슬라",
        "description": "전기차 · FSD · 에너지",
        "sector": "Mag 7",
        "score": 43,
        "signal": "주의 · Reduce",
        "signal_type": "red",
        "price": 445.45,
        "change": 2.77,
        "rsi": 70.2,
        "target": 412.25,
        "target_change": -7.5,
        "reason": ["RSI70", "과열"]
    },
]


@main.route("/")
def index():
    return render_template("index.html", stocks=STOCKS)