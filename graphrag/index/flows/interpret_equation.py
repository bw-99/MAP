# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

import logging

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
    progress_iterable,
)

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.interpret_equation.interpret_equation import run_interpret_equation

log = logging.getLogger(__name__)


async def interpret_equation(
    base_text_units: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> None:
    """All the steps to interpret equations."""

    log.info("Interpretating Equations")
    interpreted_equations = await run_interpret_equation(
        base_text_units,
        callbacks,
        cache,
        strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return interpreted_equations