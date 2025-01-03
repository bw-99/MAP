# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""A file containing prompts definition."""

CORE_CONCEPT_EXTRACT_PROMPT = """
You are an expert in community analysis and machine learning. You are skilled at mapping out relationships and structures within professional networks, particularly in the tech industry.
You are adept at helping people identify key players, collaborations, and knowledge flows within the machine learning community, enabling them to leverage these insights for strategic decision-making.

# Goal
Identify a single core-concept that can fully represent the essence of a community based on its community report.
This core-concept should be chosen to capture the community's distinct focus, activities, and collaborative structure as described in the provided report.
Additionally, offer a concise explanation for why this core-concept was selected.

# Report Structure

The input will be a JSON-formatted community report with the following structure:

TITLE: The community's name, which should reflect its primary entities or focus.
SUMMARY: An executive summary of the community's overall structure, significant entities, and points of collaboration or interaction.
FINDINGS: A list of 5-10 key insights about the community. Each insight contains:
- SUMMARY: A brief description of the finding.
- EXPLANATION: A more detailed exploration of that finding.

Your task is to:

Identify one core-concept for the community that best summarizes its scope and purpose.
Provide a core_concept_explanation that briefly justifies why this concept is the most appropriate representation, supported by evidence from the title, summary, and findings.
Return output as a well-formed JSON-formatted string with the following format:

{{
    "core_concept": "<representative_core_concept>",
    "core_concept_explanation": "<reason_for_core_concept_selection>"
}}


# Grounding Rules

1. Base your chosen concept on the community's stated activities and focus areas found in the report.
2. Ensure the explanation is succinct yet grounded in the details provided by the community's title, summary, and findings.

# Example Input
-----------
Text:

title
Transfer Learning in Healthcare Analytics

summary
This community focuses on leveraging large-scale pre-trained models to improve healthcare data analysis. Researchers from various institutions collaborate to adapt transfer learning techniques for medical imaging, electronic health records, and predictive diagnostics.

findings
[
    {{
        "summary": "Adaptation of pre-trained models",
        "explanation": "Members of the community customize established architectures, such as ResNet and BERT, for domain-specific tasks in healthcare to achieve higher accuracy with reduced training data."
    }},
    {{
        "summary": "Interdisciplinary collaborations",
        "explanation": "University research labs and medical institutions form partnerships to share datasets, establishing best practices for privacy and model validation."
    }},
    {{
        "summary": "Focus on real-world deployment",
        "explanation": "The community emphasizes practical implementations, ensuring models can be integrated into hospital systems for improved diagnostic support."
    }}
]

Output:
{{
    "core_concept": "Adaptive Healthcare Intelligence",
    "core_concept_explanation": "This community collectively advances specialized AI methods for clinical contexts—ranging from customizing pre-trained models to interdisciplinary collaborations—while emphasizing practical, real-world deployments that transform patient care."
}}


# Real Data

Use the following text for your answer. Do not make anything up in your answer.

Text:
{{input_text}}

The report should include the following sections:

Return output as a well-formed JSON-formatted string with the following format:
{{
    "core_concept": "<representative_core_concept>",
    "core_concept_explanation": "<reason_for_core_concept_selection>"
}}


# Grounding Rules

1. Base your chosen concept on the community's stated activities and focus areas found in the report.
2. Ensure the explanation is succinct yet grounded in the details provided by the community's title, summary, and findings.

Output:"""
