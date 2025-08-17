# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_plain_llm, run_preprocessing and _create_text_splitter methods to run graph intelligence."""

import traceback
from datashaper import VerbCallbacks
from fnllm import ChatLLM
from dataclasses import asdict

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.llm.load_llm import load_llm, read_llm_params
from graphrag.index.operations.preprocessing.preprocessor import PreProcessor
from graphrag.index.operations.preprocessing.typing import (
    BaseTextUnit,
    SentencePreprocessingResult,
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
) -> SentencePreprocessingResult:
    """Run the plain llm sentence preprocessing strategy."""
    llm_config = read_llm_params(args.get("llm", {}))
    llm = load_llm("sentence_preprocessing", llm_config, callbacks=callbacks, cache=cache)
    return await run_preprocessing(llm, tunit, callbacks, args)


async def run_preprocessing(
    llm: ChatLLM,
    tunit: BaseTextUnit,
    callbacks: VerbCallbacks | None,
    args: StrategyConfig,
) -> SentencePreprocessingResult:
    # RateLimiter
    rate_limiter = RateLimiter(rate=1, per=60)
    preprocessor = PreProcessor(
        llm,
        preprocessing_prompt=args.get("preprocessing_prompt", None),
        on_error=lambda e, stack, _data: callbacks.error("Sentence Preprocessing Error", e, stack),
    )
    try:
        await rate_limiter.acquire()
        preprocessed_sentence = await preprocessor(tunit.text)
        result = SentencePreprocessingResult(**asdict(tunit))
        result["text"] = preprocessed_sentence.output
        return result
    except Exception as e:
        log.exception("Error processing docs: %s", tunit.id)
        callbacks.error("Sentence Preprocessing Error", e, traceback.format_exc())
        return None
