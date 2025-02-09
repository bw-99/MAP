import pytest
import pandas as pd
import os

def load_parquet_file():
    """Load the parquet file for testing."""
    file_path = "output/create_final_viztree.parquet"  # 데이터 파일 경로
    if not os.path.exists(file_path):
        pytest.fail(f"Parquet file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        pytest.fail(f"Failed to load parquet file: {e}")
    return df

def test_parent_no_negative_one_for_doc_or_entity():
    """Test if 'parent' column does not contain -1 when 'type' is 'doc' or 'entity'."""
    df = load_parquet_file()
    
    # 'type'이 'doc' 또는 'entity'인 경우 필터링
    filtered_df = df[df["type"].isin(["doc", "entity"])]
    
    # 필터링된 데이터가 존재하는 경우만 테스트 진행
    if not filtered_df.empty:
        assert -1 not in filtered_df["parent"].values, "Found -1 in the 'parent' column for 'doc' or 'entity' types."

