import asyncio
import re
import faiss
import numpy as np
import webbrowser
import typer
import json
import pandas as pd
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.callbacks.llm_callbacks import BaseLLMCallback

EMBEDDING_DIM = 1536
index = faiss.IndexFlatL2(EMBEDDING_DIM)
document_list = []

callbacks = BaseLLMCallback()
cache = InMemoryCache()

def add_documents_to_index(documents: list):
    global document_list, index
    document_list.extend(documents)

    try:
        data = pd.DataFrame({"text": documents})
        strategy = {
            "type": "openai",
            "llm": {
                "type": "openai_embedding",
                "model": "text-embedding-3-small",
            },
        }

        embeddings = asyncio.run(embed_text(
            input=data,
            callbacks=callbacks,
            cache=cache,
            embed_column="text",
            strategy=strategy,
            embedding_name="text-embedding-3-small",
        ))

        if not embeddings or len(embeddings) == 0:
            print("Warning: OpenAI API returned empty embeddings. Skipping FAISS indexing.")
            return

        embeddings_array = np.array(embeddings, dtype=np.float32)
        index.add(embeddings_array)

    except Exception as e:
        print(f"Error adding documents to index: {e}")


def hybrid_search(query: str, top_k: int = 5) -> list:
    try:
        if not document_list:
            typer.echo("Warning: No documents found in index. Adding default documents...")

            default_documents = [
                "Neural networks are fundamental to AI research.",
                "Transformers have revolutionized NLP.",
                "GPT-4 is a powerful AI model based on transformers.",
                "Diffusion models are advancing image generation.",
                "Self-supervised learning improves data efficiency."
            ]

            add_documents_to_index(default_documents)

            if not document_list:
                typer.echo(f"Failed to add documents. Running web search for '{query}' instead...")
                search_online(query)
                return []

        keyword_results = [doc for doc in document_list if query.lower() in doc.lower()]

        data = pd.DataFrame({"text": [query]})
        strategy = {
            "type": "openai",
            "llm": {
                "type": "openai_embedding",
                "model": "text-embedding-3-small",
            },
        }

        query_embedding = asyncio.run(embed_text(
            input=data,
            callbacks=callbacks,
            cache=cache,
            embed_column="text",
            strategy=strategy,
            embedding_name="text-embedding-3-small",
        ))

        if query_embedding is None or len(query_embedding) == 0:
            typer.echo("Warning: OpenAI API returned empty query embedding. Skipping FAISS search.")
            return keyword_results

        query_vector = np.array([query_embedding[0]], dtype=np.float32)

        if index.ntotal > 0:
            _, idxs = index.search(query_vector, top_k)
            semantic_results = [document_list[i] for i in idxs[0]]
        else:
            semantic_results = []

        final_results = list(dict.fromkeys(keyword_results + semantic_results))

        if not final_results:
            typer.echo(f"No relevant results found for '{query}'. Running web search...")
            search_online(query)
            return []

        return final_results

    except Exception as e:
        typer.echo(f"Error occurred during hybrid search: {e}")
        return []


def search_online(query):
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        typer.echo(f" Searching online: {search_url}")
        webbrowser.open(search_url)
    except Exception as e:
        print(f"Error occurred during web search: {e}")
