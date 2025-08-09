# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_plain_llm, run_reconstruct_sentence and _create_text_splitter methods to run graph intelligence."""

import traceback
from datashaper import VerbCallbacks
from fnllm import ChatLLM
from dataclasses import asdict

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.llm.load_llm import load_llm, read_llm_params
from graphrag.index.operations.reconstruct_sentence.sentence_reconstructor import SentenceReconstructor
from graphrag.index.operations.reconstruct_sentence.typing import (
    BaseTextUnit,
    SentenceReconstructionResult,
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
) -> SentenceReconstructionResult:
    """Run the plain llm sentence reconstruction strategy."""
    llm_config = read_llm_params(args.get("llm", {}))
    llm = load_llm("sentence_reconstruction", llm_config, callbacks=callbacks, cache=cache)
    return await run_reconstruct_sentence(llm, tunit, callbacks, args)


async def run_reconstruct_sentence(
    llm: ChatLLM,
    tunit: BaseTextUnit,
    callbacks: VerbCallbacks | None,
    args: StrategyConfig,
) -> SentenceReconstructionResult:
    # RateLimiter
    rate_limiter = RateLimiter(rate=1, per=60)
    reconstructor = SentenceReconstructor(
        llm,
        reconstruction_prompt=args.get("reconstruction_prompt", None),
        on_error=lambda e, stack, _data: callbacks.error("Sentence Reconstruction Error", e, stack),
    )

    try:
        await rate_limiter.acquire()
        reconstructed_sentence = await reconstructor(tunit.text)
        result = SentenceReconstructionResult(**asdict(tunit))
        result["text"] = reconstructed_sentence.output
        return result
    except Exception as e:
        log.exception("Error processing docs: %s", tunit.id)
        callbacks.error("Sentence Recontruction Error", e, traceback.format_exc())
        return None
