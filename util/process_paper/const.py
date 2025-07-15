from pathlib import Path

# ==== Configuration & Paths ====
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
TITLE_LIST = DATA_DIR / "acm_titles.txt"
PDF_LINK_CSV = DATA_DIR / "arxiv_papers.csv"
PARSED_DIR = DATA_DIR / "parsed"
PDF_DIR = DATA_DIR / "pdf"
TMP_DIR = Path("/tmp/map")

PARSED_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
TMP_DIR.mkdir(exist_ok=True)

# ==== Formatter ====
ACM_SEARCH_URL = "https://dl.acm.org/action/doSearch"
ACM_QUERY = {
    "AllField": "ctr prediction",
    "startPage": 0,
    "pageSize": 50,
    "AfterYear": 2023,
    "BeforeYear": 2025
}
ARXIV_SEARCH_TEMPLATE = (
    "https://arxiv.org/search/?query={}&searchtype=title"
    "&abstracts=show&order=-announced_date_first&size=50"
)
HEADERS = {"User-Agent": "Mozilla/5.0"}
REFERENCE_KEY = "references"
KEYWORD_KEY = "keywords_parsed"
