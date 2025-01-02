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
from graphrag.prompts.index.keyword_report import KEYWORD_REPORT_PROMPT

log = logging.getLogger(__name__)


class KeywordReportResponse(BaseModel):
    """A model for the expected LLM response shape."""

    keyword: str = Field(description="The core keyword of the community.")
    keyword_explanation: str = Field(description="An explanation of the keyword.")

    extra_attributes: dict[str, Any] = Field(
        default_factory=dict, description="Extra attributes."
    )


@dataclass
class KeywordReportsResult:
    """Keyword reports result class definition."""

    output: str
    structured_output: KeywordReportResponse | None


class KeywordReportsExtractor:
    """Keyword reports extractor class definition."""

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
        self._extraction_prompt = extraction_prompt or KEYWORD_REPORT_PROMPT
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
                name="create_keyword_reports",
                json_model=KeywordReportResponse,
                model_parameters={"max_tokens": self._max_report_length},
            )
            output = response.parsed_json
        except Exception as e:
            log.exception("error generating community report")
            self._on_error(e, traceback.format_exc(), None)

        text_output = self._get_text_output(output) if output else ""
        return KeywordReportsResult(
            structured_output=output,
            output=text_output,
        )

    def _get_text_output(self, report: KeywordReportResponse) -> str:
        return f"# {report.keyword}\n\n{report.keyword_explanation}"
