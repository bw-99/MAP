import pytest
import pandas as pd
from pathlib import Path
import yaml
import os

def change_directory(root_path):
    try:
        os.chdir(root_path)
        print(f"Changed working directory to: {root_path}")
    except Exception as e:
        pytest.fail(f"Failed to change directory: {e}")

def load_parquet_file(root_path):
    file_path = root_path / "output/create_final_viztree.parquet"
    if not file_path.exists():
        pytest.fail(f"Parquet file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path)
        print("Unique types in Parquet file:", df["type"].unique()) 
    except Exception as e:
        pytest.fail(f"Failed to load parquet file: {e}")
    return df

def load_entity_types(root_path):
    yaml_path = root_path / "settings.yaml"
    if not yaml_path.exists():
        pytest.fail(f"Settings file not found: {yaml_path}")

    try:
        with yaml_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            entity_types = config.get("entity_extraction", {}).get("entity_types", [])
            
            if not entity_types:
                pytest.fail("No entity types found in settings.yaml")

            print("Loaded entity types:", entity_types)
            return entity_types
    except Exception as e:
        pytest.fail(f"Failed to load settings file: {e}")

def test_parent_no_negative_one_for_entity_types(root_path):
    change_directory(root_path)
    df = load_parquet_file(root_path)
    entity_types = load_entity_types(root_path)

    print("Filtering DataFrame with entity types:", entity_types) 
    
    filtered_df = df[df["type"].isin(entity_types)]
    
    print("Filtered DataFrame shape:", filtered_df.shape)  
    
    if filtered_df.empty:
        print("No relevant data found after filtering. Skipping test.") 
        pytest.skip("No relevant data to test in the Parquet file.")

    assert -1 not in filtered_df["parent"].values, "Found -1 in the 'parent' column for specified entity types."
