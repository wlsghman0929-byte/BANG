"""indicators.py — 기술적 지표 계산"""
from __future__ import annotations
import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def macd(s: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(s, fast) - ema(s, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0):
    mid = sma(s, n)
    sd = s.rolling(n).std()
    return mid + k * sd, mid, mid - k * sd


def add_all(df: pd.DataFrame, fast_ma: int, slow_ma: int) -> pd.DataFrame:
    """OHLCV DataFrame에 표준 지표 컬럼을 추가."""
    out = df.copy()
    c = out["Close"]
    out["MA_fast"] = sma(c, fast_ma)
    out["MA_slow"] = sma(c, slow_ma)
    out["RSI"] = rsi(c, 14)
    m, sig, hist = macd(c)
    out["MACD"], out["MACD_signal"], out["MACD_hist"] = m, sig, hist
    up, mid, low = bollinger(c, 20, 2.0)
    out["BB_up"], out["BB_mid"], out["BB_low"] = up, mid, low
    return out
