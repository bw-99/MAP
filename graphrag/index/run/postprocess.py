# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Post Processing functions for the GraphRAG run module."""

from typing import cast

import pandas as pd
from datashaper import DEFAULT_INPUT_NAME, WorkflowCallbacks

from graphrag.index.config.input import PipelineInputConfigTypes
from graphrag.index.config.workflow import PipelineWorkflowStep
from graphrag.index.context import PipelineRunContext
from graphrag.index.workflows.load import create_workflow


def _create_postprocess_steps(
    config: PipelineInputConfigTypes | None,
) -> list[PipelineWorkflowStep] | None:
    """Retrieve the post process steps for the pipeline."""
    return config.post_process if config is not None else None


async def _run_post_process_steps(
    post_process: list[PipelineWorkflowStep] | None,
    dataset: pd.DataFrame,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame:
    """Run the pipeline.

    Args:
        - post_process - The post process steps to run
        - dataset - The dataset to run the steps on
        - context - The pipeline run context
    Returns:
        - output - The dataset after running the post process steps
    """
    
    if post_process:
        input_workflow = create_workflow(
            "Input Post Process",
            post_process,
        )
        input_workflow.add_table(DEFAULT_INPUT_NAME, dataset)

        # 수식과 텍스트 분리 전처리 추가
        dataset["text"], dataset["equations"] = zip(*dataset["raw_text"].apply(split_text_and_equations))

        await input_workflow.run(
            context=context,
            callbacks=callbacks,
        )
        dataset = cast("pd.DataFrame", input_workflow.output())
    return dataset


# 수식 분리 함수 
def split_text_and_equations(text):
    """수식과 일반 텍스트를 분리하는 함수"""
    import re
    equations = re.findall(r'\$\$(.*?)\$\$', text)  # $$...$$ 수식 추출
    clean_text = re.sub(r'\$\$(.*?)\$\$', "[EQUATION]", text)  # 수식 자리에 태그 추가
    return clean_text, equations