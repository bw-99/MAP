# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create document token to document look-up table."""

import pandas as pd
import json

def create_final_token2document(
    doc_df: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to create document token to document look-up table."""
    doc_refs = [
    pd.DataFrame(
            json.load(open(f"data/parsed/{fname}.json"))["references"]
        ).assign(doc_id=doc_id)
        .assign(ref_id=lambda x: x["ref_id"].str.upper())
        [["ref_id", "title", "doc_id"]] for fname, doc_id in zip(doc_df["title"], doc_df["human_readable_id"])
    ]
    doc_refs = pd.concat(doc_refs)
    doc_refs["doc_token"] = "["+doc_refs["doc_id"].astype(str) + ":" + doc_refs["ref_id"] + "]"
    
    return doc_refs.loc[:, ["title", "doc_token"]]
