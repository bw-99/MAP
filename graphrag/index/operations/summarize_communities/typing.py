# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Finding' and 'CommunityReport' models."""

from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any

from datashaper import VerbCallbacks
from typing_extensions import TypedDict

from graphrag.cache.pipeline_cache import PipelineCache

ExtractedEntity = dict[str, Any]
StrategyConfig = dict[str, Any]
RowContext = dict[str, Any]
EntityTypes = list[str]
Claim = dict[str, Any]


class Finding(TypedDict):
    """Finding class definition."""

    summary: str
    explanation: str


class CommunityReport(TypedDict):
    """Community report class definition."""

    community: str | int
    title: str
    summary: str
    full_content: str
    full_content_json: str
    rank: float
    level: int
    rank_explanation: str
    findings: list[Finding]

class CoreConceptExtraction(TypedDict):
    """Core Concpet report class definition."""

    community: str | int
    core_concept: str
    core_concept_explanation: str


CoreConceptExtractionStrategy = Callable[
    [
        str | int,
        str,
        int,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[CommunityReport | None],
]


CommunityReportsStrategy = Callable[
    [
        str | int,
        str,
        int,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[CommunityReport | None],
]


class CoreConceptExtractionStrategyType(str, Enum):
    """CoreConceptExtractionStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
