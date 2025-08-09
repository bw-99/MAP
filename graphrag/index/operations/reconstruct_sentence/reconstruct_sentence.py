# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing entity_extract methods."""

import logging
from typing import Any

import pandas as pd
from datashaper import (
    AsyncType,
    NoopVerbCallbacks,
    VerbCallbacks,
    derive_from_rows,
    progress_ticker,
)

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.reconstruct_sentence.typing import (
    BaseTextUnit,
    SentenceReconstructionStrategy,
    SentenceReconstructionStrategyType,
)

log = logging.getLogger(__name__)


async def run_resonstruct_sentence(
    base_text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recontruct sentence from a piece of text."""

    tick = progress_ticker(callbacks.progress, len(base_text_units))
    strategy_config = {**strategy}
    runner = _load_strategy(strategy.get("type", SentenceReconstructionStrategyType.plain_llm))

    async def run_generate(record):
        result = await runner(
            tunit=BaseTextUnit(**record),
            callbacks=callbacks,
            cache=cache,
            args=strategy_config,
        )
        tick()
        return result

    reconstructed_sentences = await derive_from_rows(
        base_text_units,
        run_generate,
        callbacks=NoopVerbCallbacks(),
        num_threads=num_threads,
        scheduling_type=async_mode,
    )
    reconstructed_sentences = [item for item in reconstructed_sentences if item is not None]

    return pd.DataFrame(reconstructed_sentences)


def _load_strategy(strategy_type: SentenceReconstructionStrategyType) -> SentenceReconstructionStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case SentenceReconstructionStrategyType.plain_llm:
            from graphrag.index.operations.reconstruct_sentence.plain_llm_strategy import (
                run_plain_llm,
            )

            return run_plain_llm

        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
