"""Descarga y caché de datos de mercado vía yfinance."""
from __future__ import annotations
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import CACHE_DIR, TICKERS, DEFAULT_HISTORY_DAILY, DEFAULT_HISTORY_HOURLY


def _cache_path(name: str, interval: str) -> Path:
    return CACHE_DIR / f"{name}_{interval}.parquet"


def _download(symbol: str, period: str, interval: str, retries: int = 3) -> pd.DataFrame:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            df = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df.index = pd.to_datetime(df.index, utc=True)
                df.index.name = "datetime"
                return df
        except Exception as exc:
            last_err = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"No se pudo descargar {symbol} ({interval}): {last_err}")


def load(
    name: str,
    interval: str = "1d",
    period: str | None = None,
    use_cache: bool = True,
    refresh: bool = False,
) -> pd.DataFrame:
    """Carga un activo desde caché o lo descarga. `name` debe estar en config.TICKERS."""
    if name not in TICKERS:
        raise KeyError(f"{name} no está en config.TICKERS. Disponibles: {list(TICKERS)}")
    symbol = TICKERS[name]
    period = period or (DEFAULT_HISTORY_HOURLY if interval.endswith("h") or interval == "60m" else DEFAULT_HISTORY_DAILY)
    path = _cache_path(name, interval)

    if use_cache and not refresh and path.exists():
        return pd.read_parquet(path)

    df = _download(symbol, period=period, interval=interval)
    df.to_parquet(path)
    return df


def load_all(interval: str = "1d", refresh: bool = False) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for name in TICKERS:
        try:
            out[name] = load(name, interval=interval, refresh=refresh)
        except Exception as exc:
            print(f"[warn] no se pudo cargar {name}: {exc}")
    return out


def returns(df: pd.DataFrame, col: str = "Close", log: bool = True) -> pd.Series:
    import numpy as np
    s = df[col].astype(float)
    if log:
        return np.log(s / s.shift(1))
    return s.pct_change()
