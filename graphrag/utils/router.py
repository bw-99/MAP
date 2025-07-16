import asyncio
import time
from enum import Enum
from pathlib import Path

from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.llm.load_llm import load_llm
from datashaper import NoopVerbCallbacks


class SearchType(str, Enum):
    LOCAL  = "local"
    GLOBAL = "global"


def route_query_with_llm(
    query: str,
    *,
    config_path: Path | None,
    root_dir: Path,
) -> SearchType:
    # 1) Load project configuration
    cfg = load_config(root_dir, config_path)
    resolve_paths(cfg)

    # 2) Create an LLM instance (no cache, no-op callbacks)
    llm = load_llm(
        name="router_llm",
        config=cfg.llm,
        callbacks=NoopVerbCallbacks(),
        cache=None,
        chat_only=True,
    )

    # 3) Build the routing prompt
    prompt = f"""
Given the user query, decide whether it should be answered using:
(1) Global Search — for summarizing themes or trends across documents, or
(2) Local Search — for answering specific questions about entities or terms.

Examples:
Q1: "Explain the main contribution of the 2017 paper ‘Attention Is All You Need’." → local
Q2: "What are the key research trends in diffusion models since 2022?" → global

User query:
\"\"\"{query}\"\"\"

Answer (local / global):
""".strip()

    # 4) Call the LLM and measure latency
    t0 = time.time()
    if hasattr(llm, "acall"):
        raw = asyncio.run(llm.acall(prompt, temperature=0, max_tokens=1))
    elif hasattr(llm, "call"):
        raw = llm.call(prompt, temperature=0, max_tokens=1)
    else:
        raw = llm(prompt, temperature=0, max_tokens=1)
        if asyncio.iscoroutine(raw):
            raw = asyncio.run(raw)

    # 5) Extract the plain "local"/"global" text from the various possible outputs
    if hasattr(raw, "output") and hasattr(raw.output, "content"):
        text = raw.output.content
    elif hasattr(raw, "raw_output") and hasattr(raw.raw_output, "content"):
        text = raw.raw_output.content
    elif hasattr(raw, "text"):
        text = raw.text
    elif isinstance(raw, (list, tuple)) and raw:
        cand = raw[0]
        text = cand.content if hasattr(cand, "content") else str(cand)
    else:
        s = str(raw).lower()
        if "local" in s:
            text = "local"
        elif "global" in s:
            text = "global"
        else:
            text = s

    decision = text.strip().lower()

    # 6) Validate and return
    if decision not in (SearchType.LOCAL.value, SearchType.GLOBAL.value):
        raise ValueError(f"[router] Unexpected decision: {decision!r}")

    print(f"[router] decision={decision} | T_gate={time.time() - t0:.2f}s")
    return SearchType(decision)
