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
from graphrag.index.operations.summarize_communities.extract_concepts import extract_concepts
from graphrag.index.operations.summarize_communities import schemas
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


async def extract_core_concept(
    final_community_reports: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> None:
    """All the steps to generate all embeddings."""

    community_contexts = _prep_report(
        final_community_reports,
        callbacks,
        summarization_strategy.get("max_input_length", 16_000),
    )

    log.info("Creating core concept")
    core_concept_reports = await extract_concepts(
        community_contexts,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return core_concept_reports


def _prep_report(
    final_community_reports: pd.DataFrame,
    callbacks: VerbCallbacks,
    max_tokens: int = 16_000,
):
    """Prep communities for report generation."""
    context_columns = [schemas.TITLE, schemas.SUMMARY, schemas.FINDINGS]
    input = final_community_reports
    meta_contexts = []
    for idx, row in progress_iterable(input.iterrows(), callbacks.progress, len(input)):
        contexts = []
        for label in context_columns:
            contexts.append(
                f"-----{label}-----\n{row[label]}"
            )
        meta_contexts.append("\n\n".join(contexts))
    input[schemas.REPORT_CONTEXT] = meta_contexts
    input[schemas.REPORT_CONTEXT_SIZE] = input.loc[:, schemas.REPORT_CONTEXT].map(num_tokens)
    input[schemas.REPORT_CONTEXT_EXCEED_FLAG] =  (
        input[schemas.REPORT_CONTEXT_SIZE] > max_tokens
    )

    input = input.loc[:, [schemas.NODE_COMMUNITY, schemas.REPORT_CONTEXT, schemas.REPORT_CONTEXT_SIZE, schemas.REPORT_CONTEXT_EXCEED_FLAG]]

    # Filter valid and invalid contexts using boolean logic
    valid_context_df = input.loc[
        ~input.loc[:, schemas.REPORT_CONTEXT_EXCEED_FLAG]
    ]

    return valid_context_df
