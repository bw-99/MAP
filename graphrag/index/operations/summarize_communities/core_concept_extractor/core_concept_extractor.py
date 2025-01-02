# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CommunityReportsResult' and 'CommunityReportsExtractor' models."""

import logging
import traceback
from dataclasses import dataclass
from typing import Any

from fnllm import ChatLLM
from pydantic import BaseModel, Field

from graphrag.index.typing import ErrorHandlerFn
from graphrag.prompts.index.core_concept_extraction import CORE_CONCEPT_EXTRACT_PROMPT

log = logging.getLogger(__name__)


class CoreConceptExtractionResponse(BaseModel):
    """A model for the expected LLM response shape."""

    core_concept: str = Field(description="The core_concept of the community.")
    core_concept_explanation: str = Field(description="An explanation of the core_concept.")

    extra_attributes: dict[str, Any] = Field(
        default_factory=dict, description="Extra attributes."
    )


@dataclass
class CoreConceptExtractionResult:
    """Core concept reports result class definition."""

    output: str
    structured_output: CoreConceptExtractionResponse | None


class CoreConceptExtractionExtractor:
    """Core concept reports extractor class definition."""

    _llm: ChatLLM
    _input_text_key: str
    _extraction_prompt: str
    _output_formatter_prompt: str
    _on_error: ErrorHandlerFn
    _max_report_length: int

    def __init__(
        self,
        llm_invoker: ChatLLM,
        input_text_key: str | None = None,
        extraction_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_report_length: int | None = None,
    ):
        """Init method definition."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._extraction_prompt = extraction_prompt or CORE_CONCEPT_EXTRACT_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_report_length = max_report_length or 1500

    async def __call__(self, inputs: dict[str, Any]):
        """Call method definition."""
        output = None
        try:
            input_text = inputs[self._input_text_key]
            prompt = self._extraction_prompt.replace(
                "{" + self._input_text_key + "}", input_text
            )
            response = await self._llm(
                prompt,
                json=True,
                name="extract_core_concept",
                json_model=CoreConceptExtractionResponse,
                model_parameters={"max_tokens": self._max_report_length},
            )
            output = response.parsed_json
        except Exception as e:
            log.exception("error generating community report")
            self._on_error(e, traceback.format_exc(), None)

        text_output = self._get_text_output(output) if output else ""
        return CoreConceptExtractionResult(
            structured_output=output,
            output=text_output,
        )

    def _get_text_output(self, report: CoreConceptExtractionResponse) -> str:
        return f"# {report.core_concept}\n\n{report.core_concept_explanation}"
