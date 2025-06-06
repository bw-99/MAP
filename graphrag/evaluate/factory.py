# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Evaluate Factory methods to support CLI."""

import tiktoken

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.model.community import Community
from graphrag.model.community_report import CommunityReport
from graphrag.model.entity import Entity
from graphrag.query.llm.get_client import get_llm
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch

def get_evaluate_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    entities: list[Entity],
    communities: list[Community],
    response_type: str,
    dynamic_community_selection: bool = False,
    map_system_prompt: str | None = None,
    reduce_system_prompt: str | None = None,
    general_knowledge_inclusion_prompt: str | None = None,
) -> GlobalSearch:
    """Create a global search engine based on data + configuration."""
    token_encoder = tiktoken.get_encoding(config.encoding_model)
    gs_config = config.global_search

    dynamic_community_selection_kwargs = {}

    llm = get_llm(config) # call the llm just once
    if dynamic_community_selection:
        # TODO: Allow for another llm definition only for Global Search to leverage -mini models

        dynamic_community_selection_kwargs.update({
            "llm": llm,
            "token_encoder": tiktoken.encoding_for_model(config.llm.model),
            "keep_parent": gs_config.dynamic_search_keep_parent,
            "num_repeats": gs_config.dynamic_search_num_repeats,
            "use_summary": gs_config.dynamic_search_use_summary,
            "concurrent_coroutines": gs_config.dynamic_search_concurrent_coroutines,
            "threshold": gs_config.dynamic_search_threshold,
            "max_level": gs_config.dynamic_search_max_level,
        })

    return GlobalSearch(
        llm=llm,
        map_system_prompt=map_system_prompt,
        reduce_system_prompt=reduce_system_prompt,
        general_knowledge_inclusion_prompt=general_knowledge_inclusion_prompt,
        context_builder=GlobalCommunityContext(
            community_reports=reports,
            communities=communities,
            entities=entities,
            token_encoder=token_encoder,
            dynamic_community_selection=dynamic_community_selection,
            dynamic_community_selection_kwargs=dynamic_community_selection_kwargs,
        ),
        token_encoder=token_encoder,
        max_data_tokens=gs_config.data_max_tokens,
        map_llm_params={
            "max_tokens": gs_config.map_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
            "n": gs_config.n,
        },
        reduce_llm_params={
            "max_tokens": gs_config.reduce_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
            "n": gs_config.n,
        },
        allow_general_knowledge=True,
        json_mode=False,
        context_builder_params={
            "use_community_summary": False,
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": gs_config.max_tokens,
            "context_name": "Reports",
        },
        concurrent_coroutines=gs_config.concurrency,
        response_type=response_type,
    )
