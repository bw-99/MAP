# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph reader implementation"""

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.resolve_path import resolve_paths
from graphrag.utils.cli import _resolve_output_files


def read_graph(config: GraphRagConfig, file_to_read: list[str]) -> dict[str, pd.DataFrame]:
    resolve_paths(config)

    dataframe_dict: dict[str, pd.DataFrame] = _resolve_output_files(
        config=config,
        output_list=file_to_read,
        optional_list=[],
    )

    return dataframe_dict
