import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv(dotenv_path="./example/.env")

API_KEY = os.getenv("GRAPHRAG_API_KEY")
if not API_KEY:
    raise ValueError("❌ API_KEY is missing. Please check your .env file.")


client = AsyncOpenAI(api_key=API_KEY)



async def extract_and_explain_latex_with_llm(text: str) -> dict:
    """
    Uses an LLM to detect mathematical equations in the given academic text
    and provides explanations for each equation in the context of the paper.
    """

    prompt = f"""
    **Task:** Extract all mathematical equations from the given academic text and provide explanations.

    ### **Instructions:**
    1. Identify **all mathematical expressions** in the text, including:
       - LaTeX-style equations (`$...$`, `\\begin{{equation}}...\\end{{equation}}`, `\\frac`, `\\sum`, `\\int`, etc.).
       - Standard mathematical notations (e.g., `E = mc^2`, `f(x) = ax^2 + bx + c`, `∑`, `∫`).
    2. Provide a clear and **contextual explanation** for each equation based on the subject of the text.
    3. Ensure that the explanation is **concise, but detailed enough** to describe the role of the equation in the text.
    4. Maintain the **exact JSON format** in the output.

    ---
    ### **Academic Text:**
    ```
    {text}
    ```

    **Expected Output Format (Strict JSON Format):**
    ```
    {{
        "equations": [
            "Equation 1",
            "Equation 2"
        ],
        "explanations": {{
            "Equation 1": "Explanation 1",
            "Equation 2": "Explanation 2"
        }}
    }}
    ```
    **Do NOT provide any additional text outside this JSON format.**
    """



    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in LaTeX, mathematics, and scientific document analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000
        )

        result = response.choices[0].message.content

        if not result.strip():  # Handle empty response
            return {"equations": [], "explanations": {}, "error": "LLM returned an empty response."}


        # Ensure JSON formatting by removing extraneous text
        result = result.strip()


        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(result)  # Convert to JSON
        except json.JSONDecodeError:
            print("⚠️ JSON parsing error. Trying alternative method...")
            return {
                "equations": [],
                "explanations": {},
                "error": "JSON parsing failed. Check LLM response formatting."
            }

    except Exception as e:
        return {"equations": [], "explanations": {}, "error": str(e)}
