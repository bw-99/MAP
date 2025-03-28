# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph reader implementation"""

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


def read_graph(config: GraphRagConfig, file_to_read: list[str]) -> dict[str, pd.DataFrame]:
    resolve_paths(config)

    dataframe_dict: dict[str, pd.DataFrame] = _resolve_output_files(
        config=config,
        output_list=file_to_read,
        optional_list=[],
    )

    return dataframe_dict
