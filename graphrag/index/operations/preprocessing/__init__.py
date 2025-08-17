# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine equation interpretation package root."""

from graphrag.index.operations.preprocessing.preprocessing import (
    SentencePreprocessingStrategyType,
    run_preprocessing,
)

__all__ = ["SentencePreprocessingStrategyType", "run_preprocessing"]
