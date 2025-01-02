# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging

import pandas as pd
from datashaper import (
    AsyncType,
    NoopVerbCallbacks,
    VerbCallbacks,
    derive_from_rows,
    progress_ticker,
)

import graphrag.config.defaults as defaults
import graphrag.index.operations.summarize_communities.schemas as schemas
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.summarize_communities.typing import (
    CoreConceptExtractionStrategy,
    CoreConceptExtractionStrategyType,
    CoreConceptExtraction
)

log = logging.getLogger(__name__)


async def extract_concepts(
    local_contexts,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
):
    """Generate community keywrod."""
    reports: list[CoreConceptExtraction | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))
    runner = load_strategy(strategy["type"])

    async def run_generate(record):
        result = await _generate_report(
            runner,
            community_id=record[schemas.NODE_COMMUNITY],
            report_context=record[schemas.REPORT_CONTEXT],
            callbacks=callbacks,
            cache=cache,
            strategy=strategy,
        )
        tick()
        return result

    local_reports = await derive_from_rows(
        local_contexts,
        run_generate,
        callbacks=NoopVerbCallbacks(),
        num_threads=num_threads,
        scheduling_type=async_mode,
    )
    reports.extend([lr for lr in local_reports if lr is not None])

    return pd.DataFrame(reports)


async def _generate_report(
    runner: CoreConceptExtractionStrategy,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    community_id: int,
    report_context: str,
) -> CoreConceptExtraction | None:
    """Generate a report for a single community."""
    return await runner(
        community_id, report_context, callbacks, cache, strategy
    )


def load_strategy(
    strategy: CoreConceptExtractionStrategyType,
) -> CoreConceptExtractionStrategy:
    """Load strategy method definition."""
    match strategy:
        case CoreConceptExtractionStrategyType.graph_intelligence:
            from graphrag.index.operations.summarize_communities.strategy_concept import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
