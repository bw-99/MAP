# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Document' and 'EntityExtractionResult' models."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict

from datashaper import VerbCallbacks

from graphrag.cache.pipeline_cache import PipelineCache

StrategyConfig = dict[str, Any]

@dataclass
class BaseTextUnit:
    """Document class definition."""

    id: str
    text: str
    document_ids: list[str]
    n_tokens: int


class EquationInterpretationResult(TypedDict):
    """Sentence Interpretation result class definition."""

    id: str
    text: str
    document_ids: list[str]
    n_tokens: int


EquationInterpretationStrategy = Callable[
    [
        BaseTextUnit,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[EquationInterpretationResult],
]


class EquationInterpretationStrategyType(str, Enum):
    """EquationInterpretationStrategyType class definition."""

    plain_llm = "plain_llm"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
