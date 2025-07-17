import os
import sys
from pathlib import Path

from graphrag.config.load_config import load_config
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
    save_name = os.path.join(root, 'test_set.csv')
    df = dataset.to_pandas()
    df.to_csv(save_name)

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

async def evaluate_response(user_input, response, context, config_filepath: Path | None, root: Path):
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