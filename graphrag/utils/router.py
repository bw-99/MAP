import asyncio
from enum import Enum
from pathlib import Path

from datashaper import NoopVerbCallbacks

from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.llm.load_llm import load_llm
from graphrag.prompts.query.router import ROUTER_SYSTEM_PROMPT
from graphrag.utils.timer import with_latency_logger


class SearchType(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"


@with_latency_logger("query_router_llm")
def route_query_with_llm(
    query: str,
    *,
    config_path: Path | None,
    root_dir: Path,
) -> SearchType:
    """Route a user query to either Local or Global search using an LLM decision."""
    
    # 1) Load config
    cfg = load_config(root_dir, config_path)
    resolve_paths(cfg)

    # 2) Load LLM instance
    llm = load_llm(
        name="router_llm",
        config=cfg.llm,
        callbacks=NoopVerbCallbacks(),
        cache=None,
        chat_only=True,
    )

    # 3) Build prompt
    prompt = ROUTER_SYSTEM_PROMPT.format(query=query.strip())

    # 4) Call LLM (sync or async depending on implementation)
    if hasattr(llm, "acall"):
        raw = asyncio.run(llm.acall(prompt, temperature=0, max_tokens=1))
    elif hasattr(llm, "call"):
        raw = llm.call(prompt, temperature=0, max_tokens=1)
    else:
        raw = llm(prompt, temperature=0, max_tokens=1)
        if asyncio.iscoroutine(raw):
            raw = asyncio.run(raw)

    # 5) Extract result
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

    if decision not in (SearchType.LOCAL.value, SearchType.GLOBAL.value):
        raise ValueError(f"[router] Unexpected decision: {decision!r}")

    print(f"[router] decision={decision}")
    return SearchType(decision)
