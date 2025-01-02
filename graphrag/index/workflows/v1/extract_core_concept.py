# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.extract_core_concept import extract_core_concept

if TYPE_CHECKING:
    import pandas as pd

workflow_name = "extract_core_concept"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final community reports table with well-represented Core concepts.

    ## Dependencies
    * `workflow:create_final_community_reports`
    """
    core_concept_extract_config = config.get("core_concept_extract", {})
    summarization_strategy = core_concept_extract_config.get("strategy")
    async_mode = core_concept_extract_config.get("async_mode")
    num_threads = core_concept_extract_config.get("num_threads")

    input = {
        "source": "workflow:create_final_community_reports",
    }

    return [
        {
            "verb": workflow_name,
            "args": {
                "summarization_strategy": summarization_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": input,
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps transforming community reports to Core concept."""
    final_community_reports = cast("pd.DataFrame", input.get_input())

    output = await extract_core_concept(
        final_community_reports,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
