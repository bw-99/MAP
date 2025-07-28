import logging
import requests
from util.process_paper.const import PDF_LINK_CSV, ARXIV_SEARCH_TEMPLATE, HEADERS, TITLE_LIST
import pandas as pd
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import re
import time
from util.fileio import encode_paper_title
from util.process_paper.fetch_title import fetch_titles

logger = logging.getLogger(__name__)


def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def _fetch_arxiv_links(titles: list[str]) -> pd.DataFrame:
    records = []
    for title in titles:
        url = ARXIV_SEARCH_TEMPLATE.format(quote_plus(title))
        logger.info(f"[ArXiv] Searching -> {url}")
        resp = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        item = soup.select_one('li.arxiv-result')
        if not item:
            logger.warning(f"[ArXiv] No results found for title: {title}")
            continue
        atitle = item.select_one('p.title')
        at = atitle.text.strip() if atitle else ''
        if similarity(title, at) < 0.9:
            logger.warning(f"[ArXiv] Title mismatch: '{title}' vs '{at}'")
            continue
        abs_el = item.select_one('span.abstract-full')
        abstract = abs_el.text.strip() if abs_el else ''
        doi, pdf_link = None, None
        for a in item.select('a[href]'):
            href = a['href']
            txt = a.text.strip().lower()
            if 'doi.org' in href:
                doi = href
            if txt == 'pdf':
                pdf_link = href
        hashed = encode_paper_title(at)
        records.append({
            'Title': at,
            'DOI': doi,
            'PDF_Link': pdf_link,
            'Abstract': abstract,
            'Hashed': hashed
        })
        time.sleep(1)
    df_links = pd.DataFrame(records)
    df_links.to_csv(PDF_LINK_CSV, index=False)


def fetch_links(use_cache: bool=False) -> pd.DataFrame:
    if PDF_LINK_CSV.exists() and use_cache:
        result = pd.read_csv(PDF_LINK_CSV)
        if not result.empty:
            logger.info(f"[ArXiv] Links already fetched, loading from {PDF_LINK_CSV}")
            return result

    fetch_titles(use_cache=True)
    titles = TITLE_LIST.read_text(encoding='utf-8').splitlines()
    _fetch_arxiv_links(titles)
