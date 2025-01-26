# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.extract_entities import extract_entities
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)


async def extract_graph(
    text_units: pd.DataFrame,
    token2doc_df: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    extraction_strategy: dict[str, Any] | None = None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    entities, relationships = await extract_entities(
        text_units,
        callbacks,
        cache,
        text_column="text",
        id_column="id",
        human_readable_id_column="human_readable_id",
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        num_threads=extraction_num_threads,
    )

    # 1. filter out improperly extracted research paper entities and responsive relationships
    research_paper_entity_df = entities[entities["type"] == "RESEARCH PAPER"]
    anomaly_flag = ~research_paper_entity_df["title"].str.contains(r'\d+:B\d+')
    anomaly_df = research_paper_entity_df[anomaly_flag]
    research_paper_entity_df = research_paper_entity_df[~anomaly_flag]

    # 2. transform the doc token to doc title mapping
    research_paper_entity_df = research_paper_entity_df.merge(token2doc_df, left_on="title", right_on="doc_token", how="left")
    research_paper_entity_df.rename(columns={"title_y": "title"}, inplace=True)
    
    # 3. merge the research paper entities back to the entities dataframe
    entities = pd.concat([entities[entities["type"] != "RESEARCH PAPER"], research_paper_entity_df[entities.columns]], ignore_index=True)
    relationships = relationships[~relationships['source'].isin(anomaly_df['title']) & ~relationships['target'].isin(anomaly_df['title'])]
    
    # 4. update the source and target columns to be doc title from the doc token in the relationships dataframe
    source_map = research_paper_entity_df.set_index('title_x')['title']
    relationships['source'] = relationships['source'].apply(lambda x: source_map[x] if x in source_map else x)
    relationships['target'] = relationships['target'].apply(lambda x: source_map[x] if x in source_map else x)

    if not _validate_data(entities):
        error_msg = "Entity Extraction failed. No entities detected during extraction."
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    if not _validate_data(relationships):
        error_msg = (
            "Entity Extraction failed. No relationships detected during extraction."
        )
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities,
        relationships,
        callbacks,
        cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    base_relationship_edges = _prep_edges(relationships, relationship_summaries)

    base_entity_nodes = _prep_nodes(entities, entity_summaries)

    return (base_entity_nodes, base_relationship_edges)


def _prep_nodes(entities, summaries) -> pd.DataFrame:
    entities.drop(columns=["description"], inplace=True)
    nodes = entities.merge(summaries, on="title", how="left").drop_duplicates(
        subset="title"
    )
    nodes = nodes.loc[nodes["title"].notna()].reset_index()
    nodes["human_readable_id"] = nodes.index
    nodes["id"] = nodes["human_readable_id"].apply(lambda _x: str(uuid4()))
    return nodes


def _prep_edges(relationships, summaries) -> pd.DataFrame:
    edges = (
        relationships.drop(columns=["description"])
        .drop_duplicates(subset=["source", "target"])
        .merge(summaries, on=["source", "target"], how="left")
    )
    edges["human_readable_id"] = edges.index
    edges["id"] = edges["human_readable_id"].apply(lambda _x: str(uuid4()))
    return edges


def _validate_data(df: pd.DataFrame) -> bool:
    """Validate that the dataframe has data."""
    return len(df) > 0
