# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_plain_llm, run_interpret_equation and _create_text_splitter methods to run graph intelligence."""

import traceback
from datashaper import VerbCallbacks
from fnllm import ChatLLM
from dataclasses import asdict

import graphrag.config.defaults as defs
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.llm.load_llm import load_llm, read_llm_params
from graphrag.index.operations.interpret_equation.equation_interpretor import EquationInterpretor
from graphrag.index.operations.interpret_equation.typing import (
    BaseTextUnit,
    EquationInterpretationResult,
    StrategyConfig,
)
from graphrag.index.utils.rate_limiter import RateLimiter
import logging

log = logging.getLogger(__name__)

async def run_plain_llm(
    tunit: BaseTextUnit,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    args: StrategyConfig,
) -> EquationInterpretationResult:
    """Run the plain llm equation interpretation strategy."""
    llm_config = read_llm_params(args.get("llm", {}))
    llm = load_llm("equation_interpretation", llm_config, callbacks=callbacks, cache=cache)
    return await run_interpret_equation(llm, tunit, callbacks, args)


async def run_interpret_equation(
    llm: ChatLLM,
    tunit: BaseTextUnit,
    callbacks: VerbCallbacks | None,
    args: StrategyConfig,
) -> EquationInterpretationResult:
    # RateLimiter
    rate_limiter = RateLimiter(rate=1, per=60)
    interpretor = EquationInterpretor(
        llm,
        interpretation_prompt=args.get("interpretation_prompt", None),
        on_error=lambda e, stack, _data: callbacks.error(
            "Equation Interpretation Error", e, stack
        ),
    )
    try:
        await rate_limiter.acquire()
        interpreted_equation= await interpretor(tunit.text)
        result = EquationInterpretationResult(**asdict(tunit))
        result["text"]=interpreted_equation.output
        return result
    except Exception as e:
        log.exception("Error processing docs: %s", tunit.id)
        callbacks.error("Equation Interpretation Error", e, traceback.format_exc())
        return None
