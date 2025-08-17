# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the query subcommand."""

import asyncio
import logging
import sys
from pathlib import Path

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.logger.print_progress import PrintProgressLogger

from graphrag.utils.cli import _resolve_output_files
from graphrag.utils.router import route_query_with_llm
from graphrag.utils.timer import with_latency_logger
from graphrag.utils.router import RouteDecision

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = PrintProgressLogger("")


def run_global_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int | None,
    dynamic_community_selection: bool,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_communities: pd.DataFrame = dataframe_dict["create_final_communities"]
    final_community_reports: pd.DataFrame = dataframe_dict["create_final_community_reports"]

    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.global_search_streaming(
                config=config,
                nodes=final_nodes,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
            ):
                if get_context_data:
                    context_data = stream_chunk
                    get_context_data = False
                else:
                    full_response += stream_chunk
                    print(stream_chunk, end="")  # noqa: T201
                    sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
        api.global_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            communities=final_communities,
            community_reports=final_community_reports,
            community_level=community_level,
            dynamic_community_selection=dynamic_community_selection,
            response_type=response_type,
            query=query,
        )
    )
    logger.success(f"Global Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def run_local_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
        ],
        optional_list=[
            "create_final_covariates.parquet",
        ],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict["create_final_community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["create_final_text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["create_final_relationships"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["create_final_covariates"]

    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.local_search_streaming(
                config=config,
                nodes=final_nodes,
                entities=final_entities,
                community_reports=final_community_reports,
                text_units=final_text_units,
                relationships=final_relationships,
                covariates=final_covariates,
                community_level=community_level,
                response_type=response_type,
                query=query,
            ):
                if get_context_data:
                    context_data = stream_chunk
                    get_context_data = False
                else:
                    full_response += stream_chunk
                    print(stream_chunk, end="")  # noqa: T201
                    sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
        api.local_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    )
    logger.success(f"Local Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def run_drift_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    streaming: bool,
    query: str,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
        ],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict["create_final_community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["create_final_text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["create_final_relationships"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]

    # call the Query API
    if streaming:
        error_msg = "Streaming is not supported yet for DRIFT search."
        raise NotImplementedError(error_msg)

    # not streaming
    response, context_data = asyncio.run(
        api.drift_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            community_level=community_level,
            query=query,
        )
    )
    logger.success(f"DRIFT Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    # TODO: Map/Reduce Drift Search answer to a single response
    return response, context_data


@with_latency_logger("auto_search_pipeline")
def run_auto_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    dynamic_community_selection: bool,
    response_type: str,
    streaming: bool,
    query: str,
):
    """
    1) 설정·파케이 파일을 **한 번만** 로드
    2) route_query_with_llm()으로 local / global 판단
    3) 판단 결과에 따라 api.local_search 또는 api.global_search 호출
    """
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
        ],
        optional_list=["create_final_covariates.parquet"],
    )

    nodes = dataframe_dict["create_final_nodes"]
    entities = dataframe_dict["create_final_entities"]
    communities = dataframe_dict.get("create_final_communities")
    comm_reports = dataframe_dict["create_final_community_reports"]
    text_units = dataframe_dict.get("create_final_text_units")
    relationships = dataframe_dict.get("create_final_relationships")
    covariates = dataframe_dict.get("create_final_covariates")

    route = route_query_with_llm(
        query=query,
        config_path=config_filepath,
        root_dir=root,
    )
    logger.info(f"[router] Decision: {route.value}")
    if route is RouteDecision.LOCAL:
        search_fn = api.local_search_streaming if streaming else api.local_search
        kwargs = dict(
            config=config,
            nodes=nodes,
            entities=entities,
            community_reports=comm_reports,
            text_units=text_units,
            relationships=relationships,
            covariates=covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )

    else:  # GLOBAL
        search_fn = api.global_search_streaming if streaming else api.global_search
        kwargs = dict(
            config=config,
            nodes=nodes,
            entities=entities,
            communities=communities,
            community_reports=comm_reports,
            community_level=community_level,
            dynamic_community_selection=dynamic_community_selection,
            response_type=response_type,
            query=query,
        )

    if streaming:

        async def _stream():
            full, ctx, first = "", None, True
            async for chunk in search_fn(**kwargs):
                if first:
                    ctx, first = chunk, False
                else:
                    full += chunk
                    print(chunk, end="")
                    sys.stdout.flush()
            print()
            return full, ctx

        return asyncio.run(_stream())
    else:
        response, ctx = asyncio.run(search_fn(**kwargs))
        logger.success(f"AUTO Search Response:\n{response}")
        return response, ctx

def run_paper_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
    seed_title: str,
):
    """Perform a paper-centric search (seed inferred from `query`, citations 1-hop)."""
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
            "create_final_documents.parquet",
        ],
        optional_list=["create_final_covariates.parquet"],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict["create_final_community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["create_final_text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["create_final_relationships"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["create_final_covariates"]
    final_documents: pd.DataFrame = dataframe_dict["create_final_documents"]

    if streaming:
        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.paper_search_streaming(
                config=config,
                nodes=final_nodes,
                entities=final_entities,
                community_reports=final_community_reports,
                text_units=final_text_units,
                relationships=final_relationships,
                covariates=final_covariates,
                community_level=community_level,
                response_type=response_type,
                query=query,
                seed_title=seed_title,
                doc_df=final_documents,
            ):
                if get_context_data:
                    context_data = stream_chunk  
                    get_context_data = False
                else:
                    full_response += stream_chunk
                    print(stream_chunk, end="") 
                    sys.stdout.flush()
            print() 
            return full_response, context_data

        return asyncio.run(run_streaming_search())

    response, context_data = asyncio.run(
        api.paper_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
            seed_title=seed_title,
            doc_df=final_documents,
        )
    )
    try:
        logger.success(f"Paper Search Response:\n{response}")
    except Exception:
        pass
    return response, context_data
