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
from graphrag.prompts.index.equation_interpretation import INTERPRET_EQUATION_PROMPT

log = logging.getLogger(__name__)


class EqautionInterpretationResponse(BaseModel):
    """A model for the expected LLM response shape."""

    output: str = Field(description="Interpreted equation.")


@dataclass
class EquationInterpretorResult:
    """Core concept reports result class definition."""

    output: str | None


class EquationInterpretor:
    """Core concept reports extractor class definition."""

    _llm: ChatLLM
    _input_text_key: str
    _reconstruction_prompt: str
    _on_error: ErrorHandlerFn
    max_token: int | None

    def __init__(
        self,
        llm_invoker: ChatLLM,
        input_text_key: str | None = None,
        interpretation_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_token: int = None
    ):
        """Init method definition."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._interpretation_prompt = interpretation_prompt or INTERPRET_EQUATION_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_token = max_token or 1500

    async def __call__(self, text: str):
        """Call method definition."""
        output = None
        try:
            prompt = self._interpretation_prompt.format(**{
                self._input_text_key: text
            })
            response = await self._llm(
                prompt,
                json=True,
                name="equation_interpretation",
                json_model=EqautionInterpretationResponse,
                model_parameters={"max_tokens": self._max_token},
            )
            output = response.parsed_json
        except Exception as e:
            log.exception("error interpretating equation")
            self._on_error(e, traceback.format_exc(), None)

        return EquationInterpretorResult(
            output=output.output if output is not None else text,
        )
