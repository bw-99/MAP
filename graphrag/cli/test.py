import os
import sys
from pathlib import Path

from graphrag.config.load_config import load_config
from graphrag.logger.print_progress import PrintProgressLogger

from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.embeddings import LangchainEmbeddingsWrapper

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