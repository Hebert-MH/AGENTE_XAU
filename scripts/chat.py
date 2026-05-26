"""CLI conversacional con el agente LLM de XAUUSD.

Requiere ANTHROPIC_API_KEY en el entorno.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: define ANTHROPIC_API_KEY antes de ejecutar este script.", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
        return 1

    from src.data.loader import load, load_all
    from src.agent.chat import chat

    print("[boot] cargando datos diarios + horarios + panel macro...", file=sys.stderr)
    daily = load("XAUUSD", interval="1d")
    hourly = load("XAUUSD", interval="1h")
    panel = load_all(interval="1d")
    print(f"[boot] OK: diario {len(daily)} velas, horario {len(hourly)} velas, panel {len(panel)} activos", file=sys.stderr)

    chat(daily, hourly, panel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
