# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

import logging

from typing import Any, cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_base_text_units import (
    create_base_text_units,
)
from graphrag.index.flows.interpret_equation import interpret_equation
from graphrag.index.flows.reconstruct_sentence import reconstruct_sentence
from graphrag.index.operations.snapshot import snapshot
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_base_text_units"

log = logging.getLogger(__name__)


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for text units.

    ## Dependencies
    (input dataframe)
    """
    chunk_by_columns = config.get("chunk_by", []) or []
    text_chunk_config = config.get("text_chunk", {})
    chunk_strategy = text_chunk_config.get("strategy")
    snapshot_transient = config.get("snapshot_transient", False) or False
    equation_interpretation_config = config.get("equation_interpretation", {})
    interpretation_enabled = equation_interpretation_config.get("enabled", False)
    interpretation_strategy = equation_interpretation_config.get("strategy", {})
    interpretation_async_mode = equation_interpretation_config.get("async_mode")
    interpretation_num_threads = equation_interpretation_config.get("num_threads")

    sentence_reconstruction_config = config.get("sentence_reconstruction", {})
    reconstruction_enabled = sentence_reconstruction_config.get("enabled", False)
    reconstruction_strategy = sentence_reconstruction_config.get("strategy", {})
    reconstruction_async_mode = sentence_reconstruction_config.get("async_mode")
    reconstruction_num_threads = sentence_reconstruction_config.get("num_threads")

    return [
        {
            "verb": workflow_name,
            "args": {
                "chunk_by_columns": chunk_by_columns,
                "chunk_strategy": chunk_strategy,
                "snapshot_transient_enabled": snapshot_transient,
                "interpretation_enabled": interpretation_enabled,
                "interpretation_strategy": interpretation_strategy,
                "interpretation_async_mode": interpretation_async_mode,
                "interpretation_num_threads": interpretation_num_threads,
                "reconstruction_enabled": reconstruction_enabled,
                "reconstruction_strategy": reconstruction_strategy,
                "reconstruction_async_mode": reconstruction_async_mode,
                "reconstruction_num_threads": reconstruction_num_threads,
            },
            "input": {"source": DEFAULT_INPUT_NAME},
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    chunk_by_columns: list[str],
    chunk_strategy: dict[str, Any] | None = None,
    snapshot_transient_enabled: bool = False,
    interpretation_enabled: bool = False,
    interpretation_strategy: dict[str, Any] | None = None,
    interpretation_async_mode: AsyncType = AsyncType.AsyncIO,
    interpretation_num_threads: int = 4,
    reconstruction_enabled: bool = False,
    reconstruction_strategy: dict[str, Any] | None = None,
    reconstruction_async_mode: AsyncType = AsyncType.AsyncIO,
    reconstruction_num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base text_units."""
    source = cast("pd.DataFrame", input.get_input())

    output = create_base_text_units(
        source,
        callbacks,
        chunk_by_columns,
        chunk_strategy=chunk_strategy,
    )

    if interpretation_enabled:
        log.info("Equation interpretation is enabled")
        output = await interpret_equation(
            output,
            callbacks,
            cache,
            interpretation_strategy,
            interpretation_async_mode,
            interpretation_num_threads,
        )

    if reconstruction_enabled:
        log.info("Sentence reconstruction is enabled")
        output = await reconstruct_sentence(
            output,
            callbacks,
            cache,
            reconstruction_strategy,
            reconstruction_async_mode,
            reconstruction_num_threads,
        )

    await runtime_storage.set("base_text_units", output)

    if snapshot_transient_enabled:
        await snapshot(
            output,
            name="create_base_text_units",
            storage=storage,
            formats=["parquet"],
        )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
