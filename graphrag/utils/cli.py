# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI functions for the GraphRAG module."""

import asyncio
import pandas as pd
import argparse
import json
from pathlib import Path
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.storage.factory import StorageFactory
from graphrag.utils.storage import load_table_from_storage

def file_exist(path):
    """Check for file existence."""
    if not Path(path).is_file():
        msg = f"File not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path

def dir_exist(path):
    """Check for directory existence."""
    if not Path(path).is_dir():
        msg = f"Directory not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path


def redact(config: dict) -> str:
    """Sanitize secrets in a config object."""

    # Redact any sensitive configuration
    def redact_dict(config: dict) -> dict:
        if not isinstance(config, dict):
            return config

        result = {}
        for key, value in config.items():
            if key in {
                "api_key",
                "connection_string",
                "container_name",
                "organization",
            }:
                if value is not None:
                    result[key] = "==== REDACTED ===="
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [redact_dict(i) for i in value]
            else:
                result[key] = value
        return result

    redacted_dict = redact_dict(config)
    return json.dumps(redacted_dict, indent=4)


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
