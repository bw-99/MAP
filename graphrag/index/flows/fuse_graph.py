# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from uuid import uuid4

import numpy as np
import pandas as pd

from graphrag.config.enums import EdgeFuseStrategy
import logging

log = logging.getLogger(__name__)


def _fuse_nodes(base_nodes: pd.DataFrame, src_nodes: pd.DataFrame) -> pd.DataFrame:
    data_key = ["title", "type", "description", "text_unit_ids"]
    merge_key = ["title", "type"]

    inter_nodes = base_nodes.merge(src_nodes[data_key], on=merge_key, how="inner", suffixes=("_base", "_src"))
    inter_nodes["text_unit_ids"] = inter_nodes.apply(
        lambda x: np.unique(x["text_unit_ids_base"] + x["text_unit_ids_src"]).tolist(), axis=1
    )
    inter_nodes["description"] = inter_nodes.apply(lambda x: x["description_base"] + " " + x["description_src"], axis=1)
    inter_nodes = inter_nodes.drop_duplicates(merge_key)[data_key].reset_index(drop=True)

    base_only = (
        base_nodes.merge(inter_nodes[merge_key], on=merge_key, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )[data_key]

    src_only = (
        src_nodes.merge(inter_nodes[merge_key], on=merge_key, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )[data_key]

    final_nodes = pd.concat([inter_nodes, base_only, src_only], ignore_index=True)
    final_nodes = final_nodes.assign(human_readable_id=np.arange(len(final_nodes)), index=np.arange(len(final_nodes)))
    final_nodes["id"] = final_nodes["human_readable_id"].apply(lambda _x: str(uuid4()))
    return final_nodes


def _mean_pool_edges(base_edges: pd.DataFrame, src_edges: pd.DataFrame) -> pd.DataFrame:
    edge_data_key = ["source", "target", "description", "weight", "text_unit_ids"]
    edge_merge_key = ["source", "target"]

    inter_relationships = base_edges.merge(
        src_edges[edge_data_key], on=edge_merge_key, how="inner", suffixes=("_base", "_src")
    )
    inter_relationships["text_unit_ids"] = inter_relationships.apply(
        lambda x: np.unique(x["text_unit_ids_base"] + x["text_unit_ids_src"]).tolist(), axis=1
    )
    inter_relationships["description"] = inter_relationships.apply(
        lambda x: x["description_base"] + " " + x["description_src"], axis=1
    )
    inter_relationships["weight"] = inter_relationships.apply(
        lambda x: (x["weight_base"] + x["weight_src"]) / 2, axis=1
    )
    inter_relationships = inter_relationships.drop_duplicates(edge_merge_key)[edge_data_key].reset_index(drop=True)

    base_edges_only = (
        base_edges.merge(inter_relationships[edge_merge_key], on=edge_merge_key, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )

    src_edges_only = (
        src_edges.merge(inter_relationships[edge_merge_key], on=edge_merge_key, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )[edge_data_key]

    final_edges = pd.concat([inter_relationships, base_edges_only, src_edges_only], ignore_index=True)
    final_edges["human_readable_id"] = np.arange(len(final_edges))
    final_edges["id"] = final_edges["human_readable_id"].apply(lambda _x: str(uuid4()))

    return final_edges


def _concat_edges(base_edges: pd.DataFrame, src_edges: pd.DataFrame) -> pd.DataFrame:
    final_edges = pd.concat([base_edges, src_edges], ignore_index=True)
    final_edges["human_readable_id"] = np.arange(len(final_edges))
    final_edges["id"] = final_edges["human_readable_id"].apply(lambda _x: str(uuid4()))
    return final_edges


def fuse_graph(
    base_entity_nodes: pd.DataFrame,
    base_relationship_edges: pd.DataFrame,
    src_graph_entity_nodes: pd.DataFrame,
    src_graph_relationship_edges: pd.DataFrame,
    edge_fuse_strategy: EdgeFuseStrategy,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to fuse the base entity graph with the source paper graph."""
    log.info(f"edge_fuse_strategy: {edge_fuse_strategy}")

    final_nodes = _fuse_nodes(base_entity_nodes, src_graph_entity_nodes)
    fuse_func = _mean_pool_edges if edge_fuse_strategy == EdgeFuseStrategy.MEAN_POOL else _concat_edges
    final_relationships = fuse_func(base_relationship_edges, src_graph_relationship_edges)

    return final_nodes, final_relationships
