import os

data_dir = 'data'
os.makedirs(data_dir, exist_ok=True)
os.makedirs(f"{data_dir}/parsed", exist_ok=True)
    
CSV_PATH = 'data/arxiv_conference_papers.csv'
PARSED_PATH = 'data/parsed'
