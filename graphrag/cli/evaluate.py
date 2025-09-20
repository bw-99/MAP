# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
# Evaluating the snippet from OnePaper/graphrag/cli/index.py. Written by SH Han (2025.01.13)

"""CLI implementation of the evaluate subcommand."""

import os
import sys
import asyncio
from pathlib import Path
from enum import Enum

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.evaluate.load_graph import read_graph
from graphrag.logger.print_progress import PrintProgressLogger

from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader

logger = PrintProgressLogger("")

class EvalType(Enum):
    """The type of evaluation to run."""

    KEYWORD_MATCHING = "keyword"
    GRAPH_LLM = "graph"
    QUERY = "query"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value
    
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

def select_relevant_report(context, k=5) -> list[dict]:
    """
    Selects the top k most relevant reports based on occurrence weight and rank.
    
    Args:
        context (dict): The context dictionary containing reports.
    
    Returns:
        dict: The most relevant report based on the context.
    """
    sorted_reports = sorted(
        context['reports'], 
        key=lambda x: (x.get('occurrence weight', 0), x.get('rank', 0)), 
        reverse=True
    )
    return sorted_reports[:k] if sorted_reports else []

async def evaluate_query(
        user_input: str,
        response: str,
        retrieved_contexts: dict | None = None,
        gt_answer: str | None = None,
        gt_contexts: list[str] | None = None,
        config_filepath: Path | None = None,
        root: Path = Path.cwd(),
) -> str:
    """
    Asynchronously evaluates the response using ragas metrics.

    Args:
        user_input (str): The input question from the user.
        response (str): The generated response from the system.
        retrieved_context_obj (dict): The raw context object containing reports found by the system.
        gt_answer (str): The ground truth answer from the test set.
        gt_contexts (list[str]): The ground truth contexts from the test set.
        config_filepath (Path | None): Path to the configuration file.
        root (Path): Root directory for config loading.

    Returns:
        str: A formatted string of the evaluation results.
    """

    root = root.resolve()
    config = load_config(root, config_filepath)

    os.environ["OPENAI_API_KEY"] = config.llm.api_key

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=config.llm.model))
    evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=config.embeddings.llm.model))

    # Select the most relevant report for retrieval evaluation
    k = 5
    top_reports = select_relevant_report(retrieved_contexts, k=k) if retrieved_contexts else []

    retrieved_contexts_list = [report['content'] for report in top_reports]

    sample = { # fixed column names for ragas metrics
        "user_input": user_input,
        "response": response,
        "retrieved_contexts": retrieved_contexts_list,
        "answer": gt_answer,
        "reference": [gt_contexts],
    }

    logger.info("Starting evaluation using individual ragas metrics...")
    
    faithfulness_metric = Faithfulness(llm=evaluator_llm)
    answer_relevancy_metric = AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)
    context_precision_metric = ContextPrecision(llm=evaluator_llm)
    context_precision_wo_ref_metric = LLMContextPrecisionWithoutReference(llm=evaluator_llm)
    response_relevancy_metric = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)

    faithfulness_score = await faithfulness_metric.ascore(sample)
    answer_relevancy_score = await answer_relevancy_metric.ascore(sample)
    context_precision_score = await context_precision_metric.ascore(sample)
    context_precision_wo_ref_score = await context_precision_wo_ref_metric.ascore(sample)
    response_relevancy_score = await response_relevancy_metric.ascore(sample)

    results = {
        "faithfulness": faithfulness_score,
        "answer_relevancy": answer_relevancy_score,
        "context_precision": context_precision_score,
        "LLMContextPrecisionWithoutReference": context_precision_wo_ref_score,
        "ResponseRelevancy": response_relevancy_score,
    }
    
    evaluation_lines = [f"{metric}: {score:.4f}" for metric, score in results.items()]
    evaluation_output = "\n".join(evaluation_lines)

    return evaluation_output
