"""Chat loop: CLI conversacional contra Claude con tool use manual."""
from __future__ import annotations
import sys
from typing import Any

import anthropic
import pandas as pd

from src.agent.prompt import build_system
from src.agent.tools import TOOL_SCHEMAS, execute as execute_tool


MODEL = "claude-opus-4-7"
MAX_TOKENS = 16000
MAX_TURNS_PER_QUESTION = 8


def _text_of(content_blocks: list[Any]) -> str:
    return "\n".join(b.text for b in content_blocks if getattr(b, "type", None) == "text")


def chat(daily: pd.DataFrame, hourly: pd.DataFrame, panel: dict[str, pd.DataFrame]) -> None:
    client = anthropic.Anthropic()
    system_blocks = build_system(daily)
    messages: list[dict] = []

    print("Agente XAUUSD listo. Escribe tu pregunta (o 'salir' para terminar).\n")

    while True:
        try:
            user_input = input("\033[1mtú>\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"salir", "exit", "quit", ":q"}:
            break

        messages.append({"role": "user", "content": user_input})

        for _ in range(MAX_TURNS_PER_QUESTION):
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_blocks,
                tools=TOOL_SCHEMAS,
                messages=messages,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_uses = [b for b in response.content if b.type == "tool_use"]
                results = []
                for tu in tool_uses:
                    print(f"  \033[2m[tool] {tu.name}({tu.input})\033[0m", file=sys.stderr)
                    result = execute_tool(tu.name, tu.input, daily=daily, hourly=hourly, panel=panel)
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})
                messages.append({"role": "user", "content": results})
                continue

            text = _text_of(response.content)
            if text:
                print(f"\n\033[36magente>\033[0m {text}\n")
            usage = response.usage
            print(
                f"  \033[2m[stop={response.stop_reason} | in={usage.input_tokens} "
                f"cache_read={usage.cache_read_input_tokens} "
                f"cache_write={usage.cache_creation_input_tokens} "
                f"out={usage.output_tokens}]\033[0m",
                file=sys.stderr,
            )
            break
        else:
            print("\033[33m[warn] alcanzado MAX_TURNS_PER_QUESTION sin respuesta final\033[0m")
