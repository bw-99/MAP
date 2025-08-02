# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from graphrag.config.input_models.llm_config_input import LLMConfigInput


class EquationInterpretationConfigInput(LLMConfigInput):
    """Configuration section for equation interpretation."""

    prompt: NotRequired[str | None]
    enabled: NotRequired[bool | None]
    strategy: NotRequired[dict | None]
