# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import Field

import graphrag.config.defaults as defs
from graphrag.config.models.llm_config import LLMConfig

class SentenceReconstructionConfig(LLMConfig):
    """Configuration section for entity extraction."""

    prompt: str | None = Field(
        description="The sentence reconstruction prompt to use.", default=None
    )
    enabled: bool = Field(
        default=True, description="Whether to reconstruct the sentences."
    )
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy", default=None
    )

    def resolved_strategy(self, root_dir: str) -> dict:
        """Get the resolved entity extraction strategy."""
        from graphrag.index.operations.reconstruct_sentence import (
            SentenceReconstructionStrategyType,
        )

        return self.strategy or {
            "type": SentenceReconstructionStrategyType.plain_llm,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "reconstruction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "enabled": self.enabled,
            "async_mode": self.async_mode,
        }
