import pytest
import pandas as pd
import os
import yaml

def load_parquet_file():
    """Load the parquet file for testing."""
    file_path = "output/create_final_viztree.parquet" 
    if not os.path.exists(file_path):
        pytest.fail(f"Parquet file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path)
        print("Unique types in Parquet file:", df["type"].unique())  # ✅ Parquet 데이터 확인

    except Exception as e:
        pytest.fail(f"Failed to load parquet file: {e}")
    return df

def load_entity_types():
    yaml_path = "./settings.yaml" 
    if not os.path.exists(yaml_path):
        pytest.fail(f"Settings file not found: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            entity_types = config.get("entity_extraction", {}).get("entity_types", [])
            
            if not entity_types:
                pytest.fail("No entity types found in settings.yaml")

            print("Loaded entity types:", entity_types)
            return entity_types
    except Exception as e:
        pytest.fail(f"Failed to load settings file: {e}")

def test_parent_no_negative_one_for_entity_types():
    """Test if 'parent' column does not contain -1 for specified entity types."""
    df = load_parquet_file()
    entity_types = load_entity_types()

    print("Filtering DataFrame with entity types:", entity_types) 

    filtered_df = df[df["type"].isin(entity_types)]

    print("Filtered DataFrame shape:", filtered_df.shape)  

    if filtered_df.empty:
        print("No relevant data found after filtering. Skipping test.") 
        pytest.skip("No relevant data to test in the Parquet file.")

    assert -1 not in filtered_df["parent"].values, "Found -1 in the 'parent' column for specified entity types."
