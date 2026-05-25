"""Pipeline completo: descarga datos, calcula análisis, genera gráficos y reporte."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.loader import load, load_all
from src.reports import plots, summary


def main() -> int:
    p = argparse.ArgumentParser(description="Pipeline de análisis XAUUSD")
    p.add_argument("--refresh", action="store_true", help="Forzar re-descarga (ignorar caché)")
    p.add_argument("--no-plots", action="store_true", help="Saltar generación de gráficos")
    args = p.parse_args()

    print("[1/4] Descargando XAUUSD diario...")
    daily = load("XAUUSD", interval="1d", refresh=args.refresh)
    print(f"      {len(daily)} velas, rango {daily.index.min().date()} → {daily.index.max().date()}")

    print("[2/4] Descargando XAUUSD horario...")
    hourly = load("XAUUSD", interval="1h", refresh=args.refresh)
    print(f"      {len(hourly)} velas")

    print("[3/4] Descargando panel macro diario (DXY, US10Y, SPX, VIX, SILVER, OIL)...")
    panel = load_all(interval="1d", refresh=args.refresh)
    print(f"      activos cargados: {list(panel.keys())}")

    if not args.no_plots:
        print("[4/4] Generando gráficos...")
        from src.analysis.correlations import correlation_matrix
        plots.plot_returns_by_hour(hourly)
        plots.plot_returns_by_weekday(daily)
        plots.plot_volatility_by_hour(hourly)
        plots.plot_session_stats(hourly)
        plots.plot_price_with_indicators(daily)
        plots.plot_realized_vol(daily)
        plots.plot_correlation_matrix(correlation_matrix(panel))
        print("      gráficos OK")

    print("      Generando reporte Markdown...")
    out = summary.build(daily, hourly, panel)
    print(f"\n✓ Reporte: {out}")
    print(f"✓ Gráficos en: {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
