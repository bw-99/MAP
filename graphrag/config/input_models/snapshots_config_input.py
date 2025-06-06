# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class SnapshotsConfigInput(TypedDict):
    """Configuration section for snapshots."""

    embeddings: NotRequired[bool | str | None]
    graphml: NotRequired[bool | str | None]
    transient: NotRequired[bool | str | None]
    token2doc: NotRequired[bool | str | None]
