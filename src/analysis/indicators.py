"""Indicadores técnicos clásicos."""
from __future__ import annotations
import numpy as np
import pandas as pd


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    dn = -delta.clip(upper=0)
    rs = up.ewm(alpha=1 / n, adjust=False).mean() / dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + rs)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ef = close.ewm(span=fast, adjust=False).mean()
    es = close.ewm(span=slow, adjust=False).mean()
    line = ef - es
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    m = close.rolling(n).mean()
    s = close.rolling(n).std()
    return pd.DataFrame({"mid": m, "upper": m + k * s, "lower": m - k * s, "bandwidth": (2 * k * s) / m})


def ema(close: pd.Series, n: int) -> pd.Series:
    return close.ewm(span=n, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    c = df["Close"]
    out["EMA20"]  = ema(c, 20)
    out["EMA50"]  = ema(c, 50)
    out["EMA200"] = ema(c, 200)
    out["RSI14"]  = rsi(c, 14)
    m = macd(c)
    out["MACD"] = m["macd"]; out["MACD_SIG"] = m["signal"]; out["MACD_HIST"] = m["hist"]
    bb = bollinger(c)
    out["BB_UP"] = bb["upper"]; out["BB_LO"] = bb["lower"]; out["BB_BW"] = bb["bandwidth"]
    return out


def technical_snapshot(df: pd.DataFrame) -> dict:
    d = add_indicators(df).dropna().iloc[-1]
    close = float(d["Close"])
    return {
        "close":          close,
        "rsi14":          float(d["RSI14"]),
        "ema20_dist_pct": (close / float(d["EMA20"]) - 1) * 100,
        "ema50_dist_pct": (close / float(d["EMA50"]) - 1) * 100,
        "ema200_dist_pct":(close / float(d["EMA200"]) - 1) * 100,
        "macd_hist":      float(d["MACD_HIST"]),
        "bb_position":    (close - float(d["BB_LO"])) / (float(d["BB_UP"]) - float(d["BB_LO"])),
    }
