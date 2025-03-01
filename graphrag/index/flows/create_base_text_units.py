# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base text_units."""

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd
from datashaper import (
    FieldAggregateOperation,
    Progress,
    VerbCallbacks,
    aggregate_operation_mapping,
)

from graphrag.index.operations.chunk_text import chunk_text
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.index.operations.equation_explainer import extract_and_explain_latex_with_llm 
import nest_asyncio 
import asyncio

nest_asyncio.apply()


async def process_with_llm(chunks: pd.DataFrame) -> pd.DataFrame:
    """
    Calls LLM asynchronously to extract and explain mathematical equations
    from each text chunk.
    """
    chunks = chunks.reset_index(drop=True)
    tasks = [extract_and_explain_latex_with_llm(row["text"]) for _, row in chunks.iterrows()]
    results = await asyncio.gather(*tasks)

    for index, result in enumerate(results):
        if result.get("equations"):
            equations = result["equations"]
            explanations = result["explanations"]
            explanation_text = "\n\n".join([f"{eq}:\n{explanations.get(eq, 'No explanation available')}" for eq in equations])
            chunks.iloc[index, chunks.columns.get_loc("text")] += f"\n\n### LLM-based Explanation ###\n{explanation_text}"

    return chunks


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: VerbCallbacks,
    chunk_by_columns: list[str],
    chunk_strategy: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    sort = documents.sort_values(by=["id"], ascending=[True])

    sort["text_with_ids"] = list(
        zip(*[sort[col] for col in ["id", "text"]], strict=True)
    )

    callbacks.progress(Progress(percent=0))

    aggregated = _aggregate_df(
        sort,
        groupby=[*chunk_by_columns] if len(chunk_by_columns) > 0 else None,
        aggregations=[
            {
                "column": "text_with_ids",
                "operation": "array_agg",
                "to": "texts",
            }
        ],
    )

    callbacks.progress(Progress(percent=1))

    chunked = chunk_text(
        aggregated,
        column="texts",
        to="chunks",
        callbacks=callbacks,
        strategy=chunk_strategy,
    )

    chunked = cast("pd.DataFrame", chunked[[*chunk_by_columns, "chunks"]])
    chunked = chunked.explode("chunks")
    chunked.rename(
        columns={
            "chunks": "chunk",
        },
        inplace=True,
    )
    chunked["id"] = chunked.apply(lambda row: gen_sha512_hash(row, ["chunk"]), axis=1)
    chunked[["document_ids", "chunk", "n_tokens"]] = pd.DataFrame(
        chunked["chunk"].tolist(), index=chunked.index
    )
    # rename for downstream consumption
    chunked.rename(columns={"chunk": "text"}, inplace=True)
    
    # **Call LLM to add equation explanations**
    loop = asyncio.get_event_loop()
    chunked = loop.run_until_complete(process_with_llm(chunked))

    return cast("pd.DataFrame", chunked[chunked["text"].notna()].reset_index(drop=True))

# TODO: would be nice to inline this completely in the main method with pandas
def _aggregate_df(
    input: pd.DataFrame,
    aggregations: list[dict[str, Any]],
    groupby: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate method definition."""
    aggregations_to_apply = _load_aggregations(aggregations)
    df_aggregations = {
        agg.column: _get_pandas_agg_operation(agg)
        for agg in aggregations_to_apply.values()
    }
    if groupby is None:
        output_grouped = input.groupby(lambda _x: True)
    else:
        output_grouped = input.groupby(groupby, sort=False)
    output = cast("pd.DataFrame", output_grouped.agg(df_aggregations))
    output.rename(
        columns={agg.column: agg.to for agg in aggregations_to_apply.values()},
        inplace=True,
    )
    output.columns = [agg.to for agg in aggregations_to_apply.values()]
    return output.reset_index()


@dataclass
class Aggregation:
    """Aggregation class method definition."""

    column: str | None
    operation: str
    to: str

    # Only useful for the concat operation
    separator: str | None = None


def _get_pandas_agg_operation(agg: Aggregation) -> Any:
    if agg.operation == "string_concat":
        return (agg.separator or ",").join
    return aggregate_operation_mapping[FieldAggregateOperation(agg.operation)]


def _load_aggregations(
    aggregations: list[dict[str, Any]],
) -> dict[str, Aggregation]:
    return {
        aggregation["column"]: Aggregation(
            aggregation["column"], aggregation["operation"], aggregation["to"]
        )
        for aggregation in aggregations
    }
