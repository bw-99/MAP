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
from graphrag.prompts.index.sentence_reconstruction import RECONSTRUCT_SENTENCE_PROMPT

log = logging.getLogger(__name__)


class SentenceReconstructionResponse(BaseModel):
    """A model for the expected LLM response shape."""

    output: str = Field(description="Reconstructed sentence.")


@dataclass
class SentenceReconstructorResult:
    """Core concept reports result class definition."""

    output: str | None


class SentenceReconstructor:
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
        reconstruction_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_token: int = None
    ):
        """Init method definition."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._reconstruction_prompt = reconstruction_prompt or RECONSTRUCT_SENTENCE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_token = max_token or 1500

    async def __call__(self, text: str):
        """Call method definition."""
        output = None
        try:
            prompt = self._reconstruction_prompt.format(**{
                self._input_text_key: text
            })
            response = await self._llm(
                prompt,
                json=True,
                name="sentence_reconstruction",
                json_model=SentenceReconstructionResponse,
                model_parameters={"max_tokens": self._max_token},
            )
            output = response.parsed_json
        except Exception as e:
            log.exception("error reconstructing sentence")
            self._on_error(e, traceback.format_exc(), None)

        return SentenceReconstructorResult(
            output=output.output ,
        )