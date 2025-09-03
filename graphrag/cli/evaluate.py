# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
# Evaluating the snippet from OnePaper/graphrag/cli/index.py. Written by SH Han (2025.01.13)

"""CLI implementation of the evaluate subcommand."""

import os
import sys
import asyncio
from pathlib import Path

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.evaluate.load_graph import read_graph
from graphrag.logger.print_progress import PrintProgressLogger

from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
    Faithfulness,
)

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader

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
    logger.info(f"Evaluate Response: \n{response}")

    return response

def testset_gen(
        config_filepath: Path | None,
        root: Path,
        dry_run: bool,
        testset_size: int = 10
):
    root = root.resolve()
    config = load_config(root, config_filepath)
    # api key setting for langchain-openai
    os.environ["OPENAI_API_KEY"] = config.llm.api_key

    # initialize generator & embedder
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model=config.llm.model))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=config.embeddings.llm.model))

    # get data
    path = os.path.join(root, 'input')
    loader = DirectoryLoader(path, glob='*.txt', loader_cls=TextLoader)
    docs = loader.load()

    if dry_run:
        logger.success("Dry run complete, exiting...")
        sys.exit(0)
    
    # build dataset generator
    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = generator.generate_with_langchain_docs(docs, testset_size=testset_size)

    # save
    output_dir = Path(root) / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "test_set.csv"

    print(f"Saving test set to: {save_path}")
    df = dataset.to_pandas()
    df.to_csv(save_path, index=False)

    print("Save complete.")

def select_relevant_report(context):
    """
    Selects the most relevant report based on occurrence weight and rank.
    
    Args:
        context (dict): The context dictionary containing reports.
    
    Returns:
        dict: The most relevant report based on the context.
    """
    sorted_reports = sorted(context['reports'], key=lambda x: (x['occurrence weight'], x['rank']), reverse=True)
    return sorted_reports[0] if sorted_reports else None

async def evaluate_query(user_input, response, context, config_filepath: Path | None, root: Path):
    """
    Asynchronously evaluates the response based on the context and the most relevant report using ragas.metrics.
    
    Args:
        user_input (str): The input question from the user.
        response (str): The generated response.
        context (dict): The context containing reports, claims, and other data.
        config_filepath (Path | None): Path to the configuration file (for API key setup).
        root (Path): Root directory for config loading.
    
    Returns:
        str: The evaluation of the response based on context using RAG metrics.
    """

    root = root.resolve()
    config = load_config(root, config_filepath)

    os.environ["OPENAI_API_KEY"] = config.llm.api_key

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=config.llm.model))
    evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=config.embeddings.llm.model))

    # Select the most relevant report for retrieval evaluation
    relevant_report = select_relevant_report(context)

    # Simulate retrieval (fetching relevant context for the user input)
    if relevant_report:
        retrieved_context = relevant_report['content']
    else:
        retrieved_context = ""

    input_ = SingleTurnSample(
        user_input=user_input,
        response=response,
        retrieved_contexts=[retrieved_context], # TODO: more than one context
        reference=None, # TODO: 정답 ref도 통합하여 다양한 Metric 사용하기
    )

    scorer_precision = LLMContextPrecisionWithoutReference(llm=evaluator_llm)
    precision_score = await scorer_precision.single_turn_ascore(input_)

    scorer_relevancy = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)
    relevancy_score = await scorer_relevancy.single_turn_ascore(input_)

    scorer_faithfulness = Faithfulness(llm=evaluator_llm)
    faithfulness_score = await scorer_faithfulness.single_turn_ascore(input_)

    # Combine all the metrics into one evaluation result
    evaluation = (
        f"Context Precision (without reference): {precision_score}\n"
        f"Response Relevancy: {relevancy_score}\n"
        f"Faithfulness: {faithfulness_score}"
    )

    return evaluation
