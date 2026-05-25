"""Correlaciones de XAUUSD con activos macro (DXY, US10Y, SPX, VIX, SILVER, OIL)."""
from __future__ import annotations
import numpy as np
import pandas as pd


def _align_returns(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = {}
    for name, df in panel.items():
        s = pd.to_numeric(df["Close"], errors="coerce")
        s.index = pd.to_datetime(s.index, utc=True).normalize()
        cols[name] = np.log(s / s.shift(1))
    out = pd.DataFrame(cols).dropna(how="all")
    return out


def correlation_matrix(panel: dict[str, pd.DataFrame], method: str = "pearson") -> pd.DataFrame:
    r = _align_returns(panel)
    return r.corr(method=method).round(3)


def rolling_correlation(panel: dict[str, pd.DataFrame], base: str = "XAUUSD", window: int = 60) -> pd.DataFrame:
    r = _align_returns(panel).dropna()
    if base not in r.columns:
        raise KeyError(f"{base} no está en el panel")
    out = {col: r[base].rolling(window).corr(r[col]) for col in r.columns if col != base}
    return pd.DataFrame(out)


def lead_lag(panel: dict[str, pd.DataFrame], base: str = "XAUUSD", others: list[str] | None = None, max_lag: int = 5) -> pd.DataFrame:
    r = _align_returns(panel).dropna()
    others = others or [c for c in r.columns if c != base]
    out = {}
    for col in others:
        if col not in r.columns:
            continue
        row = {}
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                row[lag] = r[base].corr(r[col].shift(-lag))  # base lleva
            else:
                row[lag] = r[base].corr(r[col].shift(lag))   # otro lleva
        out[col] = row
    return pd.DataFrame(out).T.round(3)  # filas: activo, columnas: lag


def beta_to(panel: dict[str, pd.DataFrame], base: str = "XAUUSD") -> pd.Series:
    """β de XAUUSD respecto a cada otro activo (cov/var)."""
    r = _align_returns(panel).dropna()
    if base not in r.columns:
        raise KeyError(base)
    out = {}
    for col in r.columns:
        if col == base:
            continue
        cov = r[[base, col]].cov().iloc[0, 1]
        var = r[col].var()
        out[col] = cov / var if var else np.nan
    return pd.Series(out).round(3)
