"""Motor de evaluación de alertas + persistencia + deduplicación."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import REPORTS_DIR
from src.alerts.rules import Rule, CATALOG
from src.analysis.setup import diagnose


SEVERITY_ORDER = {"STRONG": 0, "WARN": 1, "INFO": 2}
HISTORY_FILE = REPORTS_DIR / "alerts_history.jsonl"


def run(df_daily: pd.DataFrame, rules: list[Rule] | None = None, state: dict | None = None) -> list[dict]:
    """Evalúa todas las reglas. Devuelve lista de alertas disparadas ordenadas por severidad."""
    state = state or diagnose(df_daily)
    rules = rules or CATALOG
    fired = [r.evaluate(state) for r in rules]
    fired = [a for a in fired if a is not None]
    fired.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 9))
    for a in fired:
        a["timestamp_utc"] = state["timestamp_utc"]
        a["precio"] = state["precio"]
    return fired


def persist(alerts: list[dict], path: Path = HISTORY_FILE) -> None:
    """Append cada alerta como JSON line para histórico/auditoría."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for a in alerts:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")


def format_text(alerts: list[dict]) -> str:
    if not alerts:
        return "Sin alertas disparadas."
    icons = {"STRONG": "[!!]", "WARN": "[!]", "INFO": "[i]"}
    lines = []
    for a in alerts:
        icon = icons.get(a["severity"], "[?]")
        lines.append(f"{icon} {a['name']} ({a['severity']})")
        lines.append(f"   {a['message']}")
        if a.get("tags"):
            lines.append(f"   tags: {', '.join(a['tags'])}")
    return "\n".join(lines)
