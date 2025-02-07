# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import cast

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
from graphrag.index.flows.create_final_communities import (
    create_final_communities,
)
from graphrag.index.flows.create_final_viztree import create_final_viztree
from graphrag.index.utils.ds_util import get_required_input_table
from graphrag.storage.pipeline_storage import PipelineStorage
import pandas as pd

workflow_name = "create_final_viztree"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final visualizable tree table.

    ## Dependencies
    * `workflow:extract_core_concept`
    """

    include_concept = config.get("include_concept", False)

    input = {
        "source": "workflow:extract_core_concept",
        "report_df": "workflow:create_final_community_reports",
        "doc_df": "workflow:create_final_documents",
        "entity_df": "workflow:create_final_entities",
        "node_df": "workflow:create_final_nodes",
        "text_unit_df": "workflow:create_final_text_units",
    }

    return [
        {
            "verb": workflow_name,
            "args": {
                "include_concept": include_concept
            },
            "input": input,
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    include_concept: bool,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final communities."""

    concept_df = cast("pd.DataFrame", input.get_input())
    report_df = cast("pd.DataFrame", get_required_input_table(input, "report_df").table)
    doc_df = cast("pd.DataFrame", get_required_input_table(input, "doc_df").table)
    entity_df = cast("pd.DataFrame", get_required_input_table(input, "entity_df").table)
    node_df = cast("pd.DataFrame", get_required_input_table(input, "node_df").table)
    node_df = node_df.merge(entity_df[["id", "type"]], how="left", on="id")
    text_unit_df = cast("pd.DataFrame", get_required_input_table(input, "text_unit_df").table)

    output = await create_final_viztree(
        concept_df=concept_df,
        report_df=report_df,
        doc_df=doc_df,
        node_df=node_df,
        text_unit_df=text_unit_df,
        include_concept=include_concept,
        callbacks=callbacks,
        cache=cache,
        async_mode=async_mode,
        num_threads=num_threads
    )

    print(output)

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
