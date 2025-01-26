# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    DEFAULT_INPUT_NAME,
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_token2document import (
    create_final_token2document,
)
from graphrag.storage.pipeline_storage import PipelineStorage

if TYPE_CHECKING:
    import pandas as pd


workflow_name = "create_final_token2document"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final token2document look-up table.

    ## Dependencies
    * `workflow:create_final_documents`
    """
    return [
        {
            "verb": workflow_name,
            "input": {
                "source": "workflow:create_final_documents",
            },
        },
    ]


@verb(
    name=workflow_name,
    treats_input_tables_as_immutable=True,
)
async def workflow(
    input: VerbInput,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create document token to document look-up table."""
    doc_df = cast("pd.DataFrame", input.get_input())

    output = create_final_token2document(doc_df)

    return create_verb_result(cast("Table", output))
