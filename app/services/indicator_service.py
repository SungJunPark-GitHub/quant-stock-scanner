import pandas as pd


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi.iloc[-1]), 2)


def calculate_ma(df: pd.DataFrame, period: int) -> float:
    ma = df["Close"].rolling(window=period).mean()
    return round(float(ma.iloc[-1]), 2)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return round(float(atr.iloc[-1]), 2)


def calculate_macd(df: pd.DataFrame):
    close = df["Close"]

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    macd = float(macd_line.iloc[-1])
    signal = float(signal_line.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_signal = float(signal_line.iloc[-2])

    if prev_macd <= prev_signal and macd > signal:
        status = "골든크로스"
        status_type = "green"
    elif prev_macd >= prev_signal and macd < signal:
        status = "데드크로스"
        status_type = "red"
    elif macd > signal:
        status = "상승 우위"
        status_type = "green"
    else:
        status = "하락 우위"
        status_type = "red"

    return {
        "macd": round(macd, 2),
        "signal": round(signal, 2),
        "histogram": round(float(histogram.iloc[-1]), 2),
        "status": status,
        "status_type": status_type,
    }


def calculate_52w_high(df: pd.DataFrame) -> float:
    high = df["High"].rolling(window=252).max()
    return round(float(high.iloc[-1]), 2)


def calculate_volume_ratio(df: pd.DataFrame) -> float:
    latest_volume = float(df["Volume"].iloc[-1])
    avg_volume_20 = float(df["Volume"].rolling(window=20).mean().iloc[-1])

    if avg_volume_20 == 0:
        return 0

    return round(latest_volume / avg_volume_20, 2)