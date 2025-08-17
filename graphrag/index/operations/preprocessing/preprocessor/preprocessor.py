# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CommunityReportsResult' and 'CommunityReportsExtractor' models."""

import logging
import traceback
from dataclasses import dataclass

from fnllm import ChatLLM
from pydantic import BaseModel, Field

from graphrag.index.typing import ErrorHandlerFn
from graphrag.prompts.index.sentence_preprocessing import PREPROCESSING_PROMPT

log = logging.getLogger(__name__)


class SentencePreprocessingResponse(BaseModel):
    """A model for the expected LLM response shape."""

    output: str = Field(description="Preprocessed sentence.")


@dataclass
class SentencePreprocessingResult:
    """Core concept reports result class definition."""

    output: str | None


class PreProcessor:
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
        preprocessing_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_token: int = None,
    ):
        """Init method definition."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._preprocessing_prompt = preprocessing_prompt or PREPROCESSING_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_token = max_token or 1500

    async def __call__(self, text: str):
        """Call method definition."""
        output = None
        try:
            prompt = self._preprocessing_prompt.format(**{self._input_text_key: text})

            response = await self._llm(
                prompt,
                json=True,
                name="sentence_preprocessing",
                json_model=SentencePreprocessingResponse,
                model_parameters={"max_tokens": self._max_token},
            )
            output = response.parsed_json
        except Exception as e:
            log.exception("error preprocessing sentence")
            self._on_error(e, traceback.format_exc(), None)

        return SentencePreprocessingResult(
            output=output.output if output is not None else text,
        )
