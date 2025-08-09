# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

import logging

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.reconstruct_sentence.reconstruct_sentence import run_resonstruct_sentence

log = logging.getLogger(__name__)


async def reconstruct_sentence(
    base_text_units: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> None:
    """All the steps to reconstruct sentences."""

    log.info("Reconstructing sentences")
    reconstructed_sentences = await run_resonstruct_sentence(
        base_text_units,
        callbacks,
        cache,
        strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return reconstructed_sentences
