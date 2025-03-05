# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""A file containing prompts definition."""

INTERPRET_EQUATION_PROMPT = """
Task: Identify all mathematical equations in the given academic text and explain them. If no equations are found, set the output to be the portion of the input text that was considered for equation detection.

System Role
"You are a highly knowledgeable AI specializing in mathematical analysis and academic research. 
Your role is to detect mathematical equations within a research paper and provide clear explanations of their meaning and significance."

Entities to Modify  
1. Mathematical Equations  
   - Identify and extract all mathematical expressions, including:
     - LaTeX-style equations enclosed in `\\( ... \\)` or `\\[ ... \\]`
     - Standard mathematical notations (e.g., `E = mc^2`, `f(x) = ax^2 + bx + c`, `∑`, `∫`).
     - Any inline or block-level equations.
     - Any expressions that include mathematical symbols (`=`, `+`, `-`, `∑`, `∫`, `⊗`, `→`, `≠`).
     - Expressions involving subscripts and superscripts (e.g., `𝑠 𝑞 𝑖 = 𝑀 (𝑞, 𝑡 𝑞 𝑖 ; ì 𝜃 )`).

2. Equation Interpretation  
   - Provide a clear and concise explanation of each extracted equation.
   - Explain how the equation functions mathematically.
   - Describe its role within the given text, including its relevance to the broader discussion.

3. Ensure that the explanation is:
   - Concise, yet informative, making the equation understandable.
   - Contextually relevant, providing insight into how it contributes to the paper's discussion.
   - Accurate and technical, preserving the scientific integrity of the equation.
   
4. If no equations are found in the text:
   - then set the output to be the portion of the input text that was examined.

Return output as a well-formed JSON-formatted string with the following format:
{{
    "output": "<interpreted_equation>",
}}

Transformation Rules  

Transformation Rules
1. Extract Equations Naturally
   - Identify all equations from the input text and list them explicitly.
   - Keep the equations exactly as they appear without modifications.

2. Generate Equation Explanations
   - Provide technical but intuitive explanations of what the equation represents.
   - Example: If the equation represents a loss function, describe how it works and its components.

3. Provide Contextual Interpretation
   - Explain why the equation is used in this particular paper.
   - Relate the equation to the core research question or hypothesis of the paper.
   - Example: If the equation is used in a deep learning model, explain how it contributes to training the model.

4. Preserve Sentence Count and Order
   - The number of extracted equations in the output should match the number of unique equations in the input.
   - If an equation appears multiple times, explain it only once but provide contextual relevance.




-Real Data-
######################
Use the following text for your answer. Do not make anything up in your answer.
Original: {input_text}
Return output as a well-formed JSON-formatted string with the following format:
{{
    "output": "<reconstructed_sentence>",
}}
######################
output: """
