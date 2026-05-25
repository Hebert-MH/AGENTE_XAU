"""Configuración global del agente XAUUSD."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = ROOT / "reports" / "output"

for d in (CACHE_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

TICKERS = {
    "XAUUSD": "GC=F",      # Gold futures (proxy de XAUUSD spot)
    "DXY":    "DX-Y.NYB",  # Dollar Index
    "US10Y":  "^TNX",      # Treasury 10Y yield
    "SPX":    "^GSPC",     # S&P 500
    "VIX":    "^VIX",      # Volatility index
    "SILVER": "SI=F",      # Silver futures (alta correlación con oro)
    "OIL":    "CL=F",      # WTI Crude
}

SESSIONS_UTC = {
    "ASIA":    (0, 8),
    "LONDON":  (7, 16),
    "NY":      (13, 22),
    "OVERLAP_LDN_NY": (13, 16),
}

DEFAULT_HISTORY_DAILY  = "10y"
DEFAULT_HISTORY_HOURLY = "730d"
