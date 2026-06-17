from flask import Blueprint, render_template

main = Blueprint("main", __name__)

STOCKS = [
    {
        "rank": 1,
        "ticker": "NVDA",
        "name": "NVIDIA",
        "description": "AI GPU Leader",
        "sector": "Semiconductor",
        "score": 89,
        "signal": "GREEN",
        "price": 173.72,
        "change": 2.63,
        "rsi": 58,
        "target": 195.00,
        "reason": "AI 수요 증가"
    },
    {
        "rank": 2,
        "ticker": "AAPL",
        "name": "Apple",
        "description": "Consumer Tech",
        "sector": "Technology",
        "score": 77,
        "signal": "GREEN",
        "price": 245.50,
        "change": 1.12,
        "rsi": 51,
        "target": 270.00,
        "reason": "서비스 성장"
    },
    {
        "rank": 3,
        "ticker": "TSLA",
        "name": "Tesla",
        "description": "EV & Energy",
        "sector": "Automotive",
        "score": 62,
        "signal": "YELLOW",
        "price": 318.55,
        "change": -0.83,
        "rsi": 69,
        "target": 350.00,
        "reason": "로보택시 기대"
    }
]


@main.route("/")
def index():
    return render_template("index.html", stocks=STOCKS)