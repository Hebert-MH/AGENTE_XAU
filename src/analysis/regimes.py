"""Detección de regímenes de mercado: trending vs ranging, bull vs bear."""
from __future__ import annotations
import numpy as np
import pandas as pd


def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    h, l, c = df["High"], df["Low"], df["Close"]
    up = h.diff()
    dn = -l.diff()
    plus_dm  = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr_n = pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean()
    plus_di  = 100 * pd.Series(plus_dm,  index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_n
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_n
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx_v = dx.ewm(alpha=1 / n, adjust=False).mean()
    return pd.DataFrame({"+DI": plus_di, "-DI": minus_di, "ADX": adx_v})


def regime_trend_range(df: pd.DataFrame, adx_threshold: float = 20.0) -> pd.Series:
    """TREND_UP / TREND_DOWN / RANGE según ADX y dirección de EMA50."""
    a = adx(df, n=14)
    ema50 = df["Close"].ewm(span=50, adjust=False).mean()
    slope = ema50.diff(5)  # pendiente 5 periodos
    out = pd.Series("RANGE", index=df.index)
    out[(a["ADX"] >= adx_threshold) & (slope > 0)] = "TREND_UP"
    out[(a["ADX"] >= adx_threshold) & (slope < 0)] = "TREND_DOWN"
    return out


def bull_bear_phases(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """Cruce de medias clásico para identificar fases de largo plazo."""
    f = df["Close"].ewm(span=fast, adjust=False).mean()
    s = df["Close"].ewm(span=slow, adjust=False).mean()
    return pd.Series(np.where(f > s, "BULL", "BEAR"), index=df.index)


def regime_summary(df: pd.DataFrame) -> dict:
    tr = regime_trend_range(df).dropna()
    bb = bull_bear_phases(df).dropna()
    last = -1
    return {
        "regimen_actual":          str(tr.iloc[last]),
        "fase_largo_plazo":        str(bb.iloc[last]),
        "pct_tiempo_tendencia":    float(tr.isin(["TREND_UP", "TREND_DOWN"]).mean() * 100),
        "pct_tiempo_rango":        float((tr == "RANGE").mean() * 100),
        "pct_tiempo_bull":         float((bb == "BULL").mean() * 100),
        "adx_actual":              float(adx(df)["ADX"].iloc[-1]),
    }
