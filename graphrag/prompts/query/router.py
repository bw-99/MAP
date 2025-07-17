"""Query Routing LLM prompt template for deciding between Local vs Global search."""

ROUTER_SYSTEM_PROMPT = """
Given the user query, decide whether it should be answered using:
(1) Global Search — for summarizing themes or trends across documents, or
(2) Local Search — for answering specific questions about entities or terms.

Examples:
Q1: "Explain the main contribution of the 2017 paper ‘Attention Is All You Need’." → local
Q2: "What are the key research trends in diffusion models since 2022?" → global

User query:
\"\"\"{query}\"\"\"

Answer (local / global):
""".strip()
