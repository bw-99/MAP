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
    data_dir: Path | None,
    root_dir: Path,
    response_type: str,
    dry_run: bool,
):
    """Run the pipeline with the given config."""
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    _run_evaluate(
        config=config,
        data_dir=data_dir,
        dry_run=dry_run,
        response_type=response_type,
    )

def _run_evaluate(
    config,
    data_dir,
    dry_run,
    response_type,
):
    """Perform the actual pipeline to evaluate LLM responses.
    
    Loads index files required for evaluation and runs the evaluation pipeline."""
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
    final_community_reports: pd.DataFrame = dataframe_dict[
        "create_final_community_reports"
    ]

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)

    response, context_data = asyncio.run(
        api.evaluate_responses(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            communities=final_communities,
            community_reports=final_community_reports,
            response_type=response_type,
        )
    )
    
    logger.success(f"Evaluate Response: \n{response}")
    return response, context_data

# def _run_evaluate(
#     config,
#     verbose,
#     memprofile,
#     cache,
#     logger,
#     dry_run,
#     prompts_filepath,
#     data_dir,
#     skip_validation,
#     output_dir,
# ):
#     """
#     실제로 LLM의 응답을 평가하는 파이프라인을 수행하는 함수.
    
#     :param config: 로드된 설정 객체
#     :param verbose: 상세 로그 출력 여부
#     :param memprofile: 메모리 프로파일링 활성화 여부
#     :param cache: 캐시 사용 여부
#     :param logger: 사용할 LoggerType (콘솔, 파일, 진행 표시 등)
#     :param dry_run: 실제 평가를 수행하지 않고 단순 시뮬레이션/종료 플래그
#     :param prompts_filepath: 평가에 사용할 프롬프트 목록 파일 경로
#     :param data_dir: 평가에 필요한 참조 데이터(정답 등) 파일 경로
#     :param skip_validation: config 이름 검증 등을 스킵할지 여부
#     :param output_dir: 평가 결과 파일 등을 저장할 출력 경로(재정의)
#     """
#     progress_logger = LoggerFactory().create_logger(logger)
#     info, error, success = _logger(progress_logger)
#     run_id = time.strftime("%Y%m%d-%H%M%S") # without resume

#     config.storage.base_dir = str(output_dir) if output_dir else config.storage.base_dir
#     config.reporting.base_dir = (
#         str(output_dir) if output_dir else config.reporting.base_dir
#     )
#     resolve_paths(config, run_id)

#     if not cache:
#         config.cache.type = CacheType.none

#     enabled_logging, log_path = enable_logging_with_config(config, verbose)
#     if enabled_logging:
#         info(f"Logging enabled at {log_path}", True)
#     else:
#         info(
#             f"Logging not enabled for config {redact(config.model_dump())}",
#             True,
#         )

#     if skip_validation: # Why skip validation?
#         validate_config_names(progress_logger, config)

#     info(f"Starting evaluation run for: {run_id}, {dry_run=}", verbose)
#     # info(f"Using default configuration: {redact(config.model_dump())}", verbose)
#     info(f"Prompts file: {prompts_filepath}, Data file: {data_dir}", verbose)

#     if dry_run:
#         info("Dry run complete, exiting...", True)
#         sys.exit(0)

#     _register_signal_handlers(progress_logger)

#     outputs = asyncio.run(
#         api.evaluate_responses(
#             config=config,
#             run_id=run_id,
#             memory_profile=memprofile,
#             prompts_path=prompts_filepath,
#             data_dir=data_dir,
#             progress_logger=progress_logger,
#         )
#     )
#     # outputs는 예를 들어 [EvaluationResult(...), EvaluationResult(...)] 같은 형태를 가정
#     # EvaluationResult는 평가 결과를 담고 있는 객체로, errors, warnings, results 등을 포함
    
#     encountered_errors = any(
#         output.errors and len(output.errors) > 0 for output in outputs
#     )

#     progress_logger.stop()

#     progress_logger.stop()
#     if encountered_errors:
#         error(
#             "Errors occurred during the evaluation, see logs for more details.", True
#         )
#     else:
#         success("All workflows completed successfully.", True)

#     sys.exit(1 if encountered_errors else 0)


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