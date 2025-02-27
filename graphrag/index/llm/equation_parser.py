import re
from transformers import pipeline

# LLM 모델 불러오기
llm = pipeline("text-generation", model="gpt-4o-mini")  # 필요하면 다른 모델 사용 가능

def convert_equations_to_text(text: str) -> str:
    """논문에서 수식을 감지하고, LLM을 사용하여 자연어 설명을 생성."""
    equations = extract_equations(text)
    explanations = []

    for eq in equations:
        prompt = f"수식 '{eq}' 를 자연어로 설명해줘."
        explanation = llm(prompt, max_length=100, do_sample=True)[0]["generated_text"]
        explanations.append(explanation)

    return explanations

def extract_equations(text: str) -> list:
    """텍스트에서 LaTeX 또는 일반적인 수식을 추출"""
    equation_pattern = r"\$.*?\$|\$\$.*?\$\$"  # LaTeX 수식 감지
    return re.findall(equation_pattern, text)
