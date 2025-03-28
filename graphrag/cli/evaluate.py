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
from graphrag.evaluate.load_graph import read_graph
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.logger.print_progress import PrintProgressLogger
from graphrag.storage.factory import StorageFactory
from graphrag.utils.storage import load_table_from_storage
from graphrag.utils.cli import _resolve_output_files

logger = PrintProgressLogger("")

def evaluate_index(
    config_filepath: Path | None,
    root_exp: Path,
    root_ctl: Path,
    response_type: str,
    dry_run: bool,
    evaluate_files: list[str] = ["create_final_nodes.parquet", "create_final_entities.parquet", "create_final_communities.parquet", "create_final_community_reports.parquet"]
):
    """Run the pipeline with the given config."""
    root = root_exp.resolve()
    config_exp = load_config(root, config_filepath)

    root = root_ctl.resolve()
    config_ctl = load_config(root, config_filepath)

    exp_dict, ctl_dict = read_graph(config_exp, evaluate_files), read_graph(config_ctl, evaluate_files)

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    response, context_data = asyncio.run(
        api.evaluate_graph(
            config=(config_exp, config_ctl),
            nodes=(exp_dict["create_final_nodes"], ctl_dict["create_final_nodes"]),
            entities=(exp_dict["create_final_entities"], ctl_dict["create_final_entities"]),
            communities=(exp_dict["create_final_communities"], ctl_dict["create_final_communities"]),
            community_reports=(exp_dict["create_final_community_reports"], ctl_dict["create_final_community_reports"]),
            response_type=response_type,
        )
    )

    logger.success(f"Evaluate Response: \n{response}")
    return response, context_data


def evaluate_query(
    config_filepath: Path | None,
    root_exp: Path,
    response_type: str,
    dry_run: bool,
    evaluate_files: list[str] = ["create_final_nodes.parquet", "create_final_entities.parquet", "create_final_communities.parquet", "create_final_community_reports.parquet"]
):
    """Run the pipeline with the given config."""
    root = root_exp.resolve()
    config_exp = load_config(root, config_filepath)

    assert False, "Not implemented yet"
