import pytest
import pandas as pd
from pathlib import Path
import yaml
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_viztree(root_path, file_name="create_final_viztree.parquet"):
    file_path = root_path / "output" / file_name
    if not file_path.exists():
        logger.warning(f"Parquet file not found: {file_path}. Skipping test.")
        pytest.skip(f"Parquet file not found: {file_path}. Skipping test.")
        return

    df = pd.read_parquet(file_path)
    logger.info("Unique types in Parquet file:", df["type"].unique())
    return df

def load_entity_types(root_path):
    file_path = root_path / "settings.yaml"
    if not file_path.exists():
        logger.warning(f"Setting file not found: {file_path}. Skipping test.")
        pytest.skip(f"Setting file not found: {file_path}. Skipping test.")
        return

    with file_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        entity_types = config.get("entity_extraction", {}).get("entity_types", [])

    assert entity_types, "No entity types found in settings.yaml"
    return entity_types

def test_parent_no_negative_one_for_entity_types(root_path):
    df = load_viztree(root_path)
    entity_types = load_entity_types(root_path)

    logger.info("Filtering DataFrame with entity types:", entity_types)
    filtered_df = df[df["type"].isin(entity_types)]

    logger.info("Filtered DataFrame shape:", filtered_df.shape)

    if filtered_df.empty:
        pytest.skip("No relevant data to test in the Parquet file.")

    assert -1 not in filtered_df["parent"].values, "Found -1 in the 'parent' column for specified entity types."
