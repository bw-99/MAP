from pathlib import Path

# ==== Configuration & Paths ====
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
TITLE_LIST = DATA_DIR / "acm_titles.txt"
PDF_LINK_CSV = DATA_DIR / "arxiv_papers.csv"
PARSED_DIR = DATA_DIR / "parsed"
PDF_DIR = DATA_DIR / "pdf"
PARSED_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
