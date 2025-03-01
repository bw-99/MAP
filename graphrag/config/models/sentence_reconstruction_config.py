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
    sentence_reconstruction: bool = Field(
        default=True, description="Whether to reconstruct the sentences."
    )
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy", default=None
    )
    
    # TODO: update the resolved_strategy method
    def resolved_strategy(self, root_dir: str, encoding_model: str | None) -> dict:
        """Get the resolved entity extraction strategy."""
        from graphrag.index.operations.extract_entities import (
            ExtractEntityStrategyType,
        )
        
        return self.strategy or {
            "type": ExtractEntityStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "max_gleanings": self.max_gleanings,
            # It's prechunked in create_base_text_units
            "encoding_name": encoding_model or self.encoding_model,
            "prechunked": True,
            "use_doc_id": self.use_doc_id,
        }
