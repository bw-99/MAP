# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
# Evaluating the snippet from OnePaper/graphrag/cli/index.py. Written by SH Han (2025.01.13)

"""CLI implementation of the evaluate subcommand."""

import asyncio
import sys
from pathlib import Path

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.logger.print_progress import PrintProgressLogger
from graphrag.storage.factory import StorageFactory
from graphrag.utils.storage import load_table_from_storage
from graphrag.utils.cli import _resolve_output_files

logger = PrintProgressLogger("")

def evaluate_cli(
    config_filepath: Path | None,
    root_exp: Path,
    root_ctl: Path,
    response_type: str,
    dry_run: bool,
):
    """Run the pipeline with the given config."""
    root = root_exp.resolve()
    config_exp = load_config(root, config_filepath)

    root = root_ctl.resolve()
    config_ctl = load_config(root, config_filepath)
    _run_evaluate(
        config_exp=config_exp,
        config_ctl=config_ctl,
        dry_run=dry_run,
        response_type=response_type,
    )

def _run_evaluate(
    config_exp,
    config_ctl,
    dry_run,
    response_type,
):
    """Perform the actual pipeline to evaluate LLM responses.

    Loads index files required for evaluation and runs the evaluation pipeline."""

    # config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config_exp)
    resolve_paths(config_ctl)

    dataframe_dict_exp = _resolve_output_files(
        config=config_exp,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes_exp: pd.DataFrame = dataframe_dict_exp["create_final_nodes"]
    final_entities_exp: pd.DataFrame = dataframe_dict_exp["create_final_entities"]
    final_communities_exp: pd.DataFrame = dataframe_dict_exp["create_final_communities"]
    final_community_reports_exp: pd.DataFrame = dataframe_dict_exp[
        "create_final_community_reports"
    ]

    dataframe_dict_ctl = _resolve_output_files(
        config=config_ctl,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes_ctl: pd.DataFrame = dataframe_dict_ctl["create_final_nodes"]
    final_entities_ctl: pd.DataFrame = dataframe_dict_ctl["create_final_entities"]
    final_communities_ctl: pd.DataFrame = dataframe_dict_ctl["create_final_communities"]
    final_community_reports_ctl: pd.DataFrame = dataframe_dict_ctl[
        "create_final_community_reports"
    ]

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    response, context_data = asyncio.run(
        api.evaluate_graph(
            config=(config_exp, config_ctl),
            nodes=(final_nodes_exp, final_nodes_ctl),
            entities=(final_entities_exp, final_entities_ctl),
            communities=(final_communities_exp, final_communities_ctl),
            community_reports=(final_community_reports_exp, final_community_reports_ctl),
            response_type=response_type,
        )
    )

    logger.success(f"Evaluate Response: \n{response}")
    return response, context_data
