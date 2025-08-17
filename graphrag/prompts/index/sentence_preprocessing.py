# # # Copyright (c) 2024 Microsoft Corporation.
# # # Licensed under the MIT License
# # """A file containing prompts definition."""
PREPROCESSING_PROMPT = """
Task: Perform only conservative coreference resolution on the given academic/technical text.
Make minimal edits, only when unambiguous, and preserve the original style and structure.
Return only JSON as specified. Do not add explanations.

System Role
"You are a cautious NLP preprocessor. You resolve pronouns only when safe and unambiguous,
and you never rewrite style, meaning, or structure."

Non-goals
- Do NOT summarize, shorten, expand, or paraphrase.
- Do NOT alter technical content (math, code, equations, citations, variables, units).
- Do NOT modify sentence boundaries, punctuation, or formatting.
- Do NOT hallucinate or invent content.
- Do NOT add or generate HTML-like tags (<...>) under any circumstances.

Coreference Resolution (ultra conservative)
- Resolve only when BOTH conditions hold:
  1. Antecedent is an explicit proper noun (method/model/dataset/person/organization/section/figure).
  2. Antecedent is unambiguous and appears in the same sentence.
     (Exception: if it is crystal clear and in the immediately previous sentence, allow.)
- Apply only to 3rd-person subject/object pronouns: he, she, they, it, him, her, them, its, their.
- Possessives (his, her, their) → leave unchanged.
- Do NOT replace demonstratives (this, that, these, those).
- Do NOT modify inside quotations, headings, figure/table captions, references, or protected spans.
- Per sentence: at most one replacement.
- If replacement yields two identical proper nouns adjacent (e.g., "Barack Obama Barack Obama"), keep only one.
- If ambiguous → leave pronoun unchanged.

Safety & Length Constraints
- Output length must stay within ±1% of input characters.
- If length constraint would be violated, return input unchanged.
- If unsure or rules conflict, return input unchanged.

Examples
IN: "Barack Obama was elected. He served two terms."
OUT: "Barack Obama was elected. Barack Obama served two terms."

IN: "Alice met Beth. She presented a paper."
OUT: "Alice met Beth. She presented a paper." (unchanged, ambiguous)

Output Format (strict)
Return a JSON string exactly like:

{{
    "output": "<preprocessed_text>"
}}

- Keep all line breaks.
- Do not add explanations or comments.

-Real Data-
######################
Original: {input_text}

Return output as JSON:
{{
    "output": "<preprocessed_text>"
}}
######################
output:
"""
