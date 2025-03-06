# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

class VizTreeConfig(BaseModel):
    """The viztree configuration to use."""

    include_concept: bool | None = Field(
        description="Whether the concept entity include to viztree", default=False
    )
    strategy: dict | None = Field(
        description="The viztree strategy override.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved viztree configuration."""

        return self.strategy or {
            "include_concept": self.include_concept
        }
