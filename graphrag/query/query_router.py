"""Query routing logic using LLM to decide between local/global search."""

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.query.llm.get_client import get_llm


def judge_search_type(query: str, config: GraphRagConfig) -> str:
    """
    Use an LLM to determine whether a query is better suited for local or global search.

    Args:
        query (str): The user query
        config (GraphRagConfig): Config object used to initialize the LLM

    Returns:
        str: "local" or "global"
    """
    llm = get_llm(config)

    prompt = f"""
You are a system that determines whether a question is about a specific single paper (local)
or about a broad/general topic involving multiple papers (global).

Please analyze the following query and respond with one of the following labels:

"{query}"

Answer with only one of the following:
- local: specific question about a single paper
- global: generalized or cross-paper question
"""

    try:
        response = llm.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": "You are an expert tasked with classifying the query as 'local' or 'global'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower()
        if answer not in ("local", "global"):
            raise ValueError(f"Unexpected response from LLM: {answer}")
        return answer

    except Exception as e:
        raise RuntimeError(f"Failed to determine search type via LLM: {e}")
