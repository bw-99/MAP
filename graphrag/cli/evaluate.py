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
from graphrag.evaluate.load_graph import read_graph
from graphrag.logger.print_progress import PrintProgressLogger

logger = PrintProgressLogger("")


def keyword_matching_evaluation(
    config_filepath: Path | None,
    root_exp: Path,
    dry_run: bool,
    evaluate_files: list[str] = ["create_final_entities.parquet", "create_final_viztree.parquet"],
    n_iter: int = 5,
) -> pd.DataFrame:
    """Run the pipeline with the given config."""
    root = root_exp.resolve()
    config_exp = load_config(root, config_filepath)

    exp_dict = read_graph(config_exp, evaluate_files)

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    # 1. Evaluating via keyword matching
    all_results = []
    for _ in range(n_iter):
        keyword_results = asyncio.run(
            api.evaluate_keyword(
                config=config_exp,
                entities=exp_dict["create_final_entities"],
                viztree=exp_dict["create_final_viztree"],
            )
        )
        all_results.append(keyword_results)
    mean_results = pd.concat(all_results).groupby("K", as_index=False).mean()
    mean_results.to_csv("keyword_results.csv", index=False)
    logger.info(f"Keyword Results: \n{mean_results}")
    return mean_results


def graph_llm_evaluation(
    config_filepath: Path | None,
    root_exp: Path,
    root_ctl: Path,
    response_type: str,
    dry_run: bool,
    evaluate_files: list[str] = [
        "create_final_nodes.parquet",
        "create_final_entities.parquet",
        "create_final_communities.parquet",
        "create_final_community_reports.parquet",
        "create_final_viztree.parquet",
    ],
) -> str:
    """Run the pipeline with the given config."""
    root = root_exp.resolve()
    config_exp = load_config(root, config_filepath)

    root = root_ctl.resolve()
    config_ctl = load_config(root, config_filepath)

    exp_dict, ctl_dict = read_graph(config_exp, evaluate_files), read_graph(config_ctl, evaluate_files)

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    # 1. Evaluating via graph
    response, _ = asyncio.run(
        api.evaluate_graph(
            config=(config_exp, config_ctl),
            nodes=(exp_dict["create_final_nodes"], ctl_dict["create_final_nodes"]),
            entities=(exp_dict["create_final_entities"], ctl_dict["create_final_entities"]),
            communities=(exp_dict["create_final_communities"], ctl_dict["create_final_communities"]),
            community_reports=(exp_dict["create_final_community_reports"], ctl_dict["create_final_community_reports"]),
            response_type=response_type,
        )
    )
    with open("graph_results.txt", "w") as f:
        f.write(response)
    logger.info(f"Evaluate Response: \n{response}")

    return response


def evaluate_query(
    config_filepath: Path | None,
    root_exp: Path,
    response_type: str,
    dry_run: bool,
    evaluate_files: list[str] = [
        "create_final_nodes.parquet",
        "create_final_entities.parquet",
        "create_final_communities.parquet",
        "create_final_community_reports.parquet",
    ],

):
    """Run the pipeline with the given config."""
    # root = root_exp.resolve()
    # config_exp = load_config(root, config_filepath)

    raise NotImplementedError("Not implemented yet")
