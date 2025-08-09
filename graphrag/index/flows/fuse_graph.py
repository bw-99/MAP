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


async def fuse_graph(
    base_entity_nodes: pd.DataFrame,
    base_relationship_edges: pd.DataFrame,
    src_graph_entity_nodes: pd.DataFrame,
    src_graph_relationship_edges: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to fuse the base entity graph with the source paper graph."""
    return base_entity_nodes, base_relationship_edges
