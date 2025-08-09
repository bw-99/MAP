# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_documents import (
    create_final_documents,
)
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.index.operations.snapshot import snapshot

if TYPE_CHECKING:
    import pandas as pd


workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final token2document look-up table.


    ## Dependencies
    * `workflow:create_base_documents`
    """

    snapshot_token2doc = config.get("snapshot_token2doc", True)

    return [
        {
            "verb": workflow_name,
            "args": {
                "snapshot_token2doc": snapshot_token2doc,
            },
            "input": {
                "source": "workflow:create_base_documents",
            },
        },
    ]


@verb(
    name=workflow_name,
    treats_input_tables_as_immutable=True,
)
async def workflow(
    input: VerbInput,
    runtime_storage: PipelineStorage,
    storage: PipelineStorage,
    snapshot_token2doc: bool,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create document token to document look-up table."""
    doc_df = cast("pd.DataFrame", input.get_input())

    output, token2doc = create_final_documents(doc_df)

    await runtime_storage.set("token2doc", token2doc)

    if snapshot_token2doc:
        await snapshot(token2doc, name="token2doc", storage=storage, formats=["parquet"])

    return create_verb_result(cast("Table", output))
