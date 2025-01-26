# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

import base64
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.cache.pipeline_cache import PipelineCache

async def create_final_viztree(
    concept_df: pd.DataFrame,
    report_df: pd.DataFrame,
    doc_df: pd.DataFrame,
    node_df: pd.DataFrame,
    text_unit_df: pd.DataFrame,
    include_concept: bool,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    # 1. Create viz_com_df for community visualization
    viz_com_df = _prep_viz_community(report_df, concept_df)

    # 2. Remove orphan entities
    node_df = node_df[node_df["community"] != -1].reset_index(drop=True)
    
    # 3. Add research paper entities into graph as a leaf node
    papers_node_df = node_df
    if not include_concept:
        papers_node_df = node_df[node_df["type"]=="RESEARCH PAPER"]
    papers_node_df = (
        papers_node_df
        .rename(columns={
            "community":"parent",
            "title": "explain",
        })
        .assign(type="documnet")
        [["parent", "explain", "id", "type"]]
    )

    # Merge document levels into entity data
    viztree_df = pd.concat([
        viz_com_df,
        papers_node_df
    ]).reset_index(drop=True)

    viztree_df["parent"] = viztree_df["parent"].apply(lambda x: int(x) if isinstance(x, float) else x).astype(str)
    viztree_df["id"] = viztree_df["id"].apply(lambda x: int(x) if isinstance(x, float) else x).astype(str)

    return viztree_df


def _prep_viz_community(report_df: pd.DataFrame, concept_df:pd.DataFrame) -> pd.DataFrame:
    """Prepare viz community"""
    viz_com_df = (
        report_df.merge(concept_df, on="community", how="inner")[["parent", "core_concept", "community"]]
        .assign(type="community")
        .rename(columns={
            "core_concept": "explain",
            "community": "id"
        })
    )
    viz_com_df = viz_com_df[~viz_com_df["parent"].isna()]
    return viz_com_df