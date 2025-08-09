import pandas as pd
import json
from itertools import chain
from graphrag.api.query import _get_embedding_store
from graphrag.config.models.graph_rag_config import GraphRagConfig
from util.process_paper.const import KEYWORD_KEY, PARSED_DIR
from glob import glob
from util.fileio import decode_paper_title
from pathlib import Path
from graphrag.utils.cli import redact
from graphrag.logger.print_progress import PrintProgressLogger

logger = PrintProgressLogger("graphrag.utils.graph")


def find_all_parents(extracted_entity_ids: list[int], viztree: pd.DataFrame) -> pd.DataFrame:
    # get the parents of the extracted entities
    num_iter = 0
    extracted_entities = pd.DataFrame({"id": extracted_entity_ids})
    extracted_entities[f"parents_{num_iter}"] = extracted_entities["id"]
    while (
        not extracted_entities[f"parents_{num_iter}"]
        .apply(lambda x: (any(pd.isna(x)) if isinstance(x, list) else pd.isna(x)) or (len(x) == 1 and x[0] == "-1"))
        .all()
    ):
        next_parents = (
            extracted_entities.merge(
                viztree[["id", "parent"]], left_on=f"parents_{num_iter}", right_on="id", how="inner"
            )
            .groupby(f"parents_{num_iter}")
            .agg({"parent": list})
            .reset_index()
        )
        extracted_entities = extracted_entities.merge(next_parents, on=f"parents_{num_iter}", how="left")
        extracted_entities = extracted_entities.explode("parent").rename(columns={"parent": f"parents_{num_iter+1}"})
        num_iter += 1

    # flatten all parents
    extracted_entities["parents"] = extracted_entities[[f"parents_{idx}" for idx in range(1, num_iter + 1)]].apply(
        lambda row: list({v for v in row if pd.notna(v) and v != "-1"}), axis=1
    )
    extracted_entities = (
        extracted_entities.groupby(["id"]).agg({"parents": lambda x: list(set(chain.from_iterable(x)))}).reset_index()
    )
    return extracted_entities[["id", "parents"]]


def get_embeddings(config: GraphRagConfig, embedding_name: str) -> pd.DataFrame:
    # get the pre-extracted embeddings
    logger.info(f"Vector Store Args: {redact(config.embeddings.vector_store)}")  # type: ignore # noqa
    embedding_store = _get_embedding_store(
        config_args=config.embeddings.vector_store,
        embedding_name=embedding_name,
    )
    embedding_df: pd.DataFrame = embedding_store.document_collection.to_pandas()
    embedding_df["id"] = embedding_df["id"].astype(str)
    embedding_df["vector"] = embedding_df["vector"].apply(lambda x: list(x))
    return embedding_df[["id", "vector", "text"]]


def get_all_paper_titles() -> pd.DataFrame:
    eval_paper_paths = glob(f"{PARSED_DIR}/*.json")
    return pd.DataFrame(
        {
            "title": [decode_paper_title(Path(p).stem) for p in eval_paper_paths],
            "keyword": [json.load(open(p))[KEYWORD_KEY] for p in eval_paper_paths],
        }
    )
