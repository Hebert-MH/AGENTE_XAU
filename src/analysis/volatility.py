"""Análisis de volatilidad: ATR, volatilidad realizada, clustering."""
from __future__ import annotations
import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()


def realized_vol(df: pd.DataFrame, window: int = 21, annualize: int = 252) -> pd.Series:
    r = np.log(df["Close"] / df["Close"].shift(1))
    return r.rolling(window).std() * np.sqrt(annualize)


def vol_regime(df: pd.DataFrame, window: int = 21, q_low: float = 0.33, q_high: float = 0.66) -> pd.Series:
    rv = realized_vol(df, window=window)
    lo, hi = rv.quantile(q_low), rv.quantile(q_high)
    return pd.cut(rv, bins=[-np.inf, lo, hi, np.inf], labels=["LOW", "MID", "HIGH"])


def vol_by_hour(df_hourly: pd.DataFrame) -> pd.DataFrame:
    d = df_hourly.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d["tr_bps"] = true_range(d) / d["Close"].shift(1) * 1e4
    d["hour"] = d.index.hour
    g = d.groupby("hour")["tr_bps"]
    return pd.DataFrame({
        "mean_tr_bps":   g.mean(),
        "median_tr_bps": g.median(),
        "p90_tr_bps":    g.quantile(0.90),
        "n":             g.count(),
    }).round(2)


def vol_summary(df_daily: pd.DataFrame) -> dict:
    rv = realized_vol(df_daily, window=21)
    rv_252 = realized_vol(df_daily, window=252)
    a = atr(df_daily, n=14)
    last_close = float(df_daily["Close"].iloc[-1])
    return {
        "vol_21d_anual_actual_pct": float(rv.iloc[-1] * 100),
        "vol_252d_anual_pct":       float(rv_252.iloc[-1] * 100),
        "atr_14_usd":               float(a.iloc[-1]),
        "atr_14_pct":               float(a.iloc[-1] / last_close * 100),
        "rv_21_p_actual":           float((rv <= rv.iloc[-1]).mean()),  # percentil del valor actual
    }
