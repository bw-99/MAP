# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""
import pandas as pd
import json
from util.process_paper.const import REFERENCE_KEY, PARSED_DIR
from util.fileio import decode_paper_title

def create_final_documents(
    doc_df: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to create final processed documents."""

    # Get title to doc_token mapping
    token2doc = create_final_token2doc(doc_df)

    # Maybe add more processing here
    # doc_df = ...

    return doc_df, token2doc


def create_final_token2doc(
    doc_df: pd.DataFrame,
) -> pd.DataFrame:
    doc_refs = [
    pd.DataFrame(
            json.load(open(f"{PARSED_DIR}/{fname}.json"))[REFERENCE_KEY]
            + [{
                "ref_id": "b0",
                "title": decode_paper_title(fname).strip().upper()
            }]
        ).assign(doc_id=doc_id)
        .assign(ref_id=lambda x: x["ref_id"].str.upper())
        [["ref_id", "title", "doc_id"]] for fname, doc_id in zip(doc_df["title"], doc_df["human_readable_id"])
    ]
    doc_refs = pd.concat(doc_refs)
    doc_refs["doc_token"] = "["+doc_refs["doc_id"].astype(str) + ":" + doc_refs["ref_id"] + "]"
    token2doc = doc_refs[["doc_token", "title"]].set_index("doc_token")
    return token2doc
