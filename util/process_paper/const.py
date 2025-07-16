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
REFERENCE_KEY = "references_parsed"
KEYWORD_KEY = "keywords_parsed"

# Reference parsing prompt
REFERENCE_SYSTEM_PROMPT = """
    You are a citation parser.
    Your task is to extract structured metadata (title and ref_id) from raw citation strings.
    Output should be a list of JSON objects with ref_id and title.

    --Example--
    [
        [52] Wei-Lin Chiang, Zhuohan Li, Zi Lin, Ying Sheng, Zhanghao Wu, Hao Zhang, Lianmin Zheng, Siyuan Zhuang, Yonghao Zhuang, Joseph E. Gonzalez, Ion Stoica, and Eric P. Xing. 2023. Vicuna: An Open-Source Chatbot Impressing GPT-4 with 90%* ChatGPT Quality. https://lmsys.org/blog/2023-03-30-vicuna/,
        [53] Xiang Ao, Linli Xu, Peng Zhang, Qing He. 2021. Disentangled Sequence Completion for Session-based Recommendation. WWW 2021.
    ]

    --Output--
    [
        {
            "ref_id": 52,
            "title": "Vicuna: An Open-Source Chatbot Impressing GPT-4 with 90%* ChatGPT Quality"
        }
        {
            "ref_id": 53,
            "title": "Disentangled Sequence Completion for Session-based Recommendation"
        }
    ]
"""
