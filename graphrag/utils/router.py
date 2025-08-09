from enum import Enum
from pathlib import Path
import asyncio
import logging

from pydantic import BaseModel
from datashaper import NoopVerbCallbacks

from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.llm.load_llm import load_llm
from graphrag.prompts.query.router import ROUTER_SYSTEM_PROMPT
from graphrag.utils.timer import with_latency_logger

log = logging.getLogger(__name__)


class RouteDecision(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"


class RouteLLMOutput(BaseModel):
    decision: RouteDecision


@with_latency_logger("query_router_llm")
def route_query_with_llm(
    query: str,
    *,
    config_path: Path | None,
    root_dir: Path,
) -> RouteDecision:
    # 1) Config load
    cfg = load_config(root_dir, config_path)
    resolve_paths(cfg)

    # 2) LLM load
    llm = load_llm(
        name="router_llm",
        config=cfg.llm,
        callbacks=NoopVerbCallbacks(),
        cache=None,
        chat_only=True,
    )

    # 3) Prompt
    prompt = ROUTER_SYSTEM_PROMPT.format(query=query.strip())

    # 4) Call
    if hasattr(llm, "acall"):
        llm_output = asyncio.run(llm.acall(prompt, temperature=0))
    else:
        result = llm(prompt, temperature=0)
        llm_output = asyncio.run(result) if asyncio.iscoroutine(result) else result

    # 5) Extract text
    text = llm_output.output.content

    # 6) parse output
    try:
        parsed = RouteLLMOutput.parse_raw(text)
    except Exception as e:
        raise RuntimeError(f"Fail to parse LLM output:\n{text}") from e

    decision = parsed.decision
    return decision
