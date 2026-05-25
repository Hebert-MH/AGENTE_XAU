"""Detección automática de niveles clave: swings, pivots, fibonacci, niveles psicológicos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def swing_points(df: pd.DataFrame, distance: int = 10, prominence_pct: float = 0.01) -> dict[str, pd.Series]:
    """Detecta swing highs/lows en velas diarias usando find_peaks."""
    high = df["High"].values
    low  = df["Low"].values
    close = df["Close"].iloc[-1]
    prom = float(close) * prominence_pct

    hi_idx, _ = find_peaks(high, distance=distance, prominence=prom)
    lo_idx, _ = find_peaks(-low, distance=distance, prominence=prom)

    return {
        "swing_highs": pd.Series(high[hi_idx], index=df.index[hi_idx]),
        "swing_lows":  pd.Series(low[lo_idx],  index=df.index[lo_idx]),
    }


def daily_pivots(df: pd.DataFrame) -> dict[str, float]:
    """Pivot points clásicos basados en la última vela diaria cerrada."""
    last = df.iloc[-1]
    h, l, c = float(last["High"]), float(last["Low"]), float(last["Close"])
    p = (h + l + c) / 3
    return {
        "P":  p,
        "R1": 2 * p - l,  "S1": 2 * p - h,
        "R2": p + (h - l), "S2": p - (h - l),
        "R3": h + 2 * (p - l), "S3": l - 2 * (h - p),
    }


def key_levels(df: pd.DataFrame, n_levels: int = 5, lookback: int = 365) -> dict:
    """Devuelve niveles cercanos al precio actual, ordenados por proximidad."""
    sub = df.tail(lookback)
    sw = swing_points(sub)
    close = float(df["Close"].iloc[-1])

    above = []
    below = []
    for s in (sw["swing_highs"], sw["swing_lows"]):
        for ts, lvl in s.items():
            lvl = float(lvl)
            dist_pct = (lvl - close) / close * 100
            entry = {"level": round(lvl, 2), "date": str(ts.date()), "dist_pct": round(dist_pct, 2)}
            if lvl > close:
                above.append(entry)
            else:
                below.append(entry)

    above.sort(key=lambda x: x["dist_pct"])
    below.sort(key=lambda x: -x["dist_pct"])
    return {
        "close":       close,
        "resistencias": above[:n_levels],
        "soportes":     below[:n_levels],
        "pivots_diarios": {k: round(v, 2) for k, v in daily_pivots(df).items()},
    }


def fibonacci_levels(df: pd.DataFrame, lookback: int = 90) -> dict:
    """Niveles de retroceso/extensión Fibonacci del último swing significativo."""
    sub = df.tail(lookback)
    hi_ts = sub["High"].idxmax()
    lo_ts = sub["Low"].idxmin()
    hi, lo = float(sub["High"].max()), float(sub["Low"].min())
    diff = hi - lo
    uptrend = hi_ts > lo_ts

    ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
    levels = {}
    for r in ratios:
        if uptrend:
            levels[f"{r*100:.1f}%"] = round(hi - diff * r, 2)
        else:
            levels[f"{r*100:.1f}%"] = round(lo + diff * r, 2)
    return {
        "direccion": "uptrend" if uptrend else "downtrend",
        "swing_high": {"price": round(hi, 2), "date": str(hi_ts.date())},
        "swing_low":  {"price": round(lo, 2), "date": str(lo_ts.date())},
        "fib": levels,
    }


def psychological_levels(close: float, step: int = 50, n: int = 3) -> dict:
    """Niveles psicológicos redondos (múltiplos de `step`) cercanos al precio."""
    base = int(close // step) * step
    above = [base + step * i for i in range(1, n + 1)]
    below = [base - step * (i - 1) for i in range(1, n + 1) if base - step * (i - 1) > 0]
    return {"arriba": above, "abajo": below}
