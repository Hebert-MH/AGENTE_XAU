"""Imprime un diagnóstico de setup actual de XAUUSD en consola (sin gráficos ni reporte completo)."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.loader import load
from src.analysis.setup import diagnose, to_markdown


def main() -> int:
    daily = load("XAUUSD", interval="1d")
    print(to_markdown(diagnose(daily)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
