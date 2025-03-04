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

logger = PrintProgressLogger("")

def evaluate_cli(
    config_filepath: Path | None,
    root_dir1: Path,
    root_dir2: Path,
    response_type: str,
    dry_run: bool,
):
    """Run the pipeline with the given config."""
    root = root_dir1.resolve()
    config1 = load_config(root, config_filepath)
    
    root = root_dir2.resolve()
    config2 = load_config(root, config_filepath)
    _run_evaluate(
        config1=config1,
        config2=config2,
        dry_run=dry_run,
        response_type=response_type,
    )

def _run_evaluate(
    config1,
    config2,
    dry_run,
    response_type,
):
    """Perform the actual pipeline to evaluate LLM responses.
    
    Loads index files required for evaluation and runs the evaluation pipeline."""
    
    # config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config1)
    resolve_paths(config2)
    
    dataframe_dict1 = _resolve_output_files(
        config=config1,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes1: pd.DataFrame = dataframe_dict1["create_final_nodes"]
    final_entities1: pd.DataFrame = dataframe_dict1["create_final_entities"]
    final_communities1: pd.DataFrame = dataframe_dict1["create_final_communities"]
    final_community_reports1: pd.DataFrame = dataframe_dict1[
        "create_final_community_reports"
    ]

    dataframe_dict2 = _resolve_output_files(
        config=config2,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes2: pd.DataFrame = dataframe_dict2["create_final_nodes"]
    final_entities2: pd.DataFrame = dataframe_dict2["create_final_entities"]
    final_communities2: pd.DataFrame = dataframe_dict2["create_final_communities"]
    final_community_reports2: pd.DataFrame = dataframe_dict2[
        "create_final_community_reports"
    ]
    
    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    response, context_data = asyncio.run(
        api.evaluate_graph(
            config=(config1, config2),
            nodes=(final_nodes1, final_nodes2),
            entities=(final_entities1, final_entities2),
            communities=(final_communities1, final_communities2),
            community_reports=(final_community_reports1, final_community_reports2),
            response_type=response_type,
        )
    )
    
    logger.success(f"Evaluate Response: \n{response}")
    return response, context_data

def _resolve_output_files(
    config: GraphRagConfig,
    output_list: list[str],
    optional_list: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Read indexing output files to a dataframe dict."""
    dataframe_dict = {}
    pipeline_config = create_pipeline_config(config)
    storage_config = pipeline_config.storage.model_dump()  # type: ignore
    storage_obj = StorageFactory().create_storage(
        storage_type=storage_config["type"], kwargs=storage_config
    )
    for output_file in output_list:
        df_key = output_file.split(".")[0]
        df_value = asyncio.run(
            load_table_from_storage(name=output_file, storage=storage_obj)
        )
        dataframe_dict[df_key] = df_value

    # for optional output files, set the dict entry to None instead of erroring out if it does not exist
    if optional_list:
        for optional_file in optional_list:
            file_exists = asyncio.run(storage_obj.has(optional_file))
            df_key = optional_file.split(".")[0]
            if file_exists:
                df_value = asyncio.run(
                    load_table_from_storage(name=optional_file, storage=storage_obj)
                )
                dataframe_dict[df_key] = df_value
            else:
                dataframe_dict[df_key] = None

    return dataframe_dict