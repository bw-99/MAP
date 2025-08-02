# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel
from typing import Optional


class VizTreeConfigInput(BaseModel):
    """Configuration section for viztree."""

    include_concept: Optional[bool] = False
    strategy: Optional[dict] = None
    enabled: Optional[bool] = False
