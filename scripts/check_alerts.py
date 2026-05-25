"""Evalúa el catálogo de alertas contra el estado actual y lo imprime."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.loader import load
from src.alerts.engine import run, persist, format_text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--no-persist", action="store_true", help="No guardar historial")
    p.add_argument("--json", action="store_true", help="Salida como JSON")
    args = p.parse_args()

    daily = load("XAUUSD", interval="1d")
    alerts = run(daily)

    if args.json:
        import json
        print(json.dumps(alerts, ensure_ascii=False, indent=2))
    else:
        print(format_text(alerts))

    if not args.no_persist:
        persist(alerts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
