import pytest
import pandas as pd
from pathlib import Path
import yaml

def load_viztree(root_path, file_name="create_final_viztree.parquet"):
    file_path = root_path / "output" / file_name
    assert file_path.exists(), f"Parquet file not found: {file_path}"

    df = pd.read_parquet(file_path)
    print("Unique types in Parquet file:", df["type"].unique())  
    return df

def load_entity_types(root_path):
    yaml_path = root_path / "settings.yaml"
    assert yaml_path.exists(), f"Settings file not found: {yaml_path}"

    with yaml_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        entity_types = config.get("entity_extraction", {}).get("entity_types", [])
    
    assert entity_types, "No entity types found in settings.yaml"
    
    print("Loaded entity types:", entity_types)
    return entity_types

def test_parent_no_negative_one_for_entity_types(root_path):
    df = load_viztree(root_path)
    entity_types = load_entity_types(root_path)

    print("Filtering DataFrame with entity types:", entity_types)  
    
    filtered_df = df[df["type"].isin(entity_types)]
    
    print("Filtered DataFrame shape:", filtered_df.shape)  

    if filtered_df.empty:
        print("No relevant data found after filtering. Skipping test.") 
        pytest.skip("No relevant data to test in the Parquet file.")

    assert -1 not in filtered_df["parent"].values, "Found -1 in the 'parent' column for specified entity types."
