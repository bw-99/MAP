# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast
import logging

import pandas as pd
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
from graphrag.index.flows.extract_graph import extract_graph
from graphrag.index.flows.fuse_graph import fuse_graph
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_graphml import snapshot_graphml

from graphrag.storage.pipeline_storage import PipelineStorage

from graphrag.index.utils.ds_util import get_required_input_table
from graphrag.config.enums import EdgeFuseStrategy

workflow_name = "extract_graph"

log = logging.getLogger(__name__)


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for the entity graph.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_final_documents`
    """
    entity_extraction_config = config.get("entity_extract", {})
    async_mode = entity_extraction_config.get("async_mode", AsyncType.AsyncIO)
    extraction_strategy = entity_extraction_config.get("strategy")
    extraction_num_threads = entity_extraction_config.get("num_threads", 4)
    entity_types = entity_extraction_config.get("entity_types")

    entity_extraction_config_source_paper = config.get("entity_extract_source_paper", {})
    entity_extraction_enabled_source_paper = entity_extraction_config_source_paper.get("enabled", False)
    async_mode_source_paper = entity_extraction_config_source_paper.get("async_mode", AsyncType.AsyncIO)
    extraction_strategy_source_paper = entity_extraction_config_source_paper.get("strategy")
    extraction_num_threads_source_paper = entity_extraction_config_source_paper.get("num_threads", 1)
    entity_types_source_paper = entity_extraction_config_source_paper.get("entity_types")
    edge_fuse_strategy = entity_extraction_config_source_paper.get("edge_fuse_strategy", EdgeFuseStrategy.CONCAT)

    summarize_descriptions_config = config.get("summarize_descriptions", {})
    summarization_strategy = summarize_descriptions_config.get("strategy")
    summarization_num_threads = summarize_descriptions_config.get("num_threads", 4)

    snapshot_graphml = config.get("snapshot_graphml", False) or False
    snapshot_transient = config.get("snapshot_transient", False) or False

    input = {
        "source": "workflow:create_base_text_units",
        "documents": "workflow:create_final_documents",
    }

    return [
        {
            "verb": workflow_name,
            "args": {
                # extract_graph
                "extraction_strategy": extraction_strategy,
                "extraction_num_threads": extraction_num_threads,
                "extraction_async_mode": async_mode,
                "entity_types": entity_types,
                # extract_source_paper_graph
                "entity_extraction_enabled_source_paper": entity_extraction_enabled_source_paper,
                "extraction_strategy_source_paper": extraction_strategy_source_paper,
                "extraction_num_threads_source_paper": extraction_num_threads_source_paper,
                "extraction_async_mode_source_paper": async_mode_source_paper,
                "entity_types_source_paper": entity_types_source_paper,
                "edge_fuse_strategy": edge_fuse_strategy,
                # summarize_descriptions
                "summarization_strategy": summarization_strategy,
                "summarization_num_threads": summarization_num_threads,
                "snapshot_graphml_enabled": snapshot_graphml,
                "snapshot_transient_enabled": snapshot_transient,
            },
            "input": input,
        },
    ]


@verb(
    name=workflow_name,
    treats_input_tables_as_immutable=True,
)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    # extract_graph
    extraction_strategy: dict[str, Any] | None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    # extract_source_paper_graph
    entity_extraction_enabled_source_paper: bool = False,
    extraction_strategy_source_paper: dict[str, Any] | None = None,
    extraction_num_threads_source_paper: int = 1,
    extraction_async_mode_source_paper: AsyncType = AsyncType.AsyncIO,
    entity_types_source_paper: list[str] | None = None,
    edge_fuse_strategy: EdgeFuseStrategy = EdgeFuseStrategy.CONCAT,
    # summarize_descriptions
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    snapshot_graphml_enabled: bool = False,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    text_units = await runtime_storage.get("base_text_units")

    # doc token to doc title mapping
    token2doc_df = await runtime_storage.get("token2doc")
    token2doc_dict = token2doc_df["title"].to_dict()

    # augment text_units with human_readable_id to use as a distinct identifier for each doc reference
    doc_units = cast("pd.DataFrame", get_required_input_table(input, "documents").table)

    columns_to_use = list(text_units.columns) + ["human_readable_id"]
    text_units = (
        text_units.explode("document_ids")
        .merge(doc_units[["id", "human_readable_id"]], left_on="document_ids", right_on="id")
        .rename(columns={"id_x": "id"})
        .groupby("id")
        .agg({"document_ids": list, "text": " ".join, "human_readable_id": "first", "n_tokens": "first"})
        .reset_index()
    )
    text_units = text_units[columns_to_use]

    base_entity_nodes, base_relationship_edges = await extract_graph(
        text_units,
        token2doc_dict,
        callbacks,
        cache,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
    )

    if entity_extraction_enabled_source_paper:
        log.info("extract_source_paper_graph enabled")
        src_graph_entity_nodes, src_graph_relationship_edges = await extract_graph(
            text_units,
            token2doc_dict,
            callbacks,
            cache,
            extraction_strategy=extraction_strategy_source_paper,
            extraction_num_threads=extraction_num_threads_source_paper,
            extraction_async_mode=extraction_async_mode_source_paper,
            entity_types=entity_types_source_paper,
            summarization_strategy=summarization_strategy,
            summarization_num_threads=summarization_num_threads,
        )

        base_entity_nodes, base_relationship_edges = await fuse_graph(
            base_entity_nodes,
            base_relationship_edges,
            src_graph_entity_nodes,
            src_graph_relationship_edges,
            edge_fuse_strategy,
        )

    await runtime_storage.set("base_entity_nodes", base_entity_nodes)
    await runtime_storage.set("base_relationship_edges", base_relationship_edges)

    if snapshot_graphml_enabled:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(base_relationship_edges)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=storage,
        )

    if snapshot_transient_enabled:
        await snapshot(
            base_entity_nodes,
            name="base_entity_nodes",
            storage=storage,
            formats=["parquet"],
        )
        await snapshot(
            base_relationship_edges,
            name="base_relationship_edges",
            storage=storage,
            formats=["parquet"],
        )

    return create_verb_result(cast("Table", pd.DataFrame()))
