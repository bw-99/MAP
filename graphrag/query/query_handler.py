import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import webbrowser
import typer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.IndexFlatL2(384) 
document_list = []  


def hybrid_search(query: str, top_k: int = 5) -> list:
    keyword_results = [doc for doc in document_list if query.lower() in doc.lower()]

    query_vector = np.array([embedding_model.encode(query)])
    if index.ntotal > 0:
        _, idxs = index.search(query_vector, top_k)
        semantic_results = [document_list[i] for i in idxs[0]]
    else:
        semantic_results = []

    combined_results = list(dict.fromkeys(keyword_results + semantic_results))
    return combined_results

def search_online(query):
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    typer.echo(f"Searching online: {search_url}")
    webbrowser.open(search_url)