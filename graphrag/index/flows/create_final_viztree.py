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
    entity_df: pd.DataFrame,
    text_unit_df: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    # 1. Create viz_com_df for community visualization
    viz_com_df = _prep_viz_community(report_df, concept_df)

    # 2. Remove orphan entities
    entity_df = entity_df[entity_df["community"] != -1].reset_index(drop=True)

    # 3. Explode text_unit_df for entity and document mapping
    explode_text_unit_df = text_unit_df[["human_readable_id", "document_ids", "entity_ids"]].explode("entity_ids")
    explode_text_unit_df = explode_text_unit_df.explode("document_ids")
    entity_tunit_df = entity_df.merge(explode_text_unit_df, left_on="id", right_on="entity_ids", how="left")

    # 4. Create viz_doc_df for document visualization
    viz_doc_df = _prep_viz_doc(entity_tunit_df, doc_df)
    viz_doc_df["explain"] = viz_doc_df["explain"].apply(lambda x: base64.urlsafe_b64decode(x).decode("utf-8"))

    # 5. Create viz_entity_df for entity visualization
    viz_entity_df = _prep_viz_entity(entity_tunit_df)

    # Merge document levels into entity data
    viztree_df = pd.concat([
        viz_com_df,
        viz_doc_df,
        viz_entity_df
    ]).reset_index(drop=True)

    viztree_df["parent"] = viztree_df["parent"].astype(str)
    viztree_df["id"] = viztree_df["id"].astype(str)

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

    return viz_com_df

def _prep_viz_doc(entity_tunit_df: pd.DataFrame, doc_df:pd.DataFrame) -> pd.DataFrame:
    """Prepare viz community"""
    viz_doc_df = (
        entity_tunit_df[["community", "document_ids"]]
        .merge(doc_df,  left_on="document_ids", right_on="id", how="left")
        .drop(columns=["id"])
        .drop_duplicates(subset=["document_ids", "community"])
        .rename(columns={
            "community":"parent",
            "title": "explain",
            "document_ids": "id"
        })[["parent", "id", "explain"]]
        .assign(type="doc")
        .reset_index(drop=True)
    )

    return viz_doc_df

def _prep_viz_entity(entity_tunit_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare viz community"""
    viz_entity_df = (
        entity_tunit_df.copy(deep=True)
        .drop_duplicates(subset=["entity_ids", "document_ids"]).reset_index(drop=True)
        .rename(columns={
            "title": "explain",
            "human_readable_id_y": "text_unit_id",
            "document_ids": "parent"
        })[["id", "explain", "parent"]]
        .assign(type="entity")
        .rename(columns={
            "id_x": "explain",
            "human_readable_id_y": "text_unit_id",
            "document_ids": "parent"
        })
    )

    return viz_entity_df
