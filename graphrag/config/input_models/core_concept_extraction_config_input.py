# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from graphrag.config.input_models.llm_config_input import LLMConfigInput


class CoreConceptExtractionConfigInput(LLMConfigInput):
    """Configuration section for core concept extraction."""

    prompt: NotRequired[str | None]
    max_length: NotRequired[int | None]
    max_input_length: NotRequired[int | None]
    strategy: NotRequired[dict | None]
    enabled: NotRequired[bool | None]
