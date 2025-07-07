import argparse
import base64
import json
import logging
import random
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from threading import Event, Thread
from urllib.parse import quote_plus, urlencode

import arxiv
import pandas as pd
import pyautogui
import tqdm
from bs4 import BeautifulSoup
from docling.datamodel.document import DoclingDocument
from docling.document_converter import DocumentConverter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from util.const import PARSED_DIR, PDF_DIR, PDF_LINK_CSV, TITLE_LIST

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

client = arxiv.Client(page_size=1, delay_seconds=0.5, num_retries=3)

# ==== Utilities ====

def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9 \._]", "_", name)
    return clean.replace(" ", "_")

# ==== PDF Parsing & Download ====

def extract_sections_with_content(parsed_data: DoclingDocument) -> dict:
    sections = {}
    current_section = None
    current_content = []

    for text in parsed_data.get('texts', []):
        text_content = text.get('text', '')
        label = text.get('label', '')

        # docling은 추출할 때 1. Intro, 3.1 Overview 등을 모두 section_header 이름으로 추출해둔다.
        # 이를 이용해서 섹션 헤더 별 내용을 세분화해서 저장해둔다.
        # 새로운 섹션 헤더를 발견하면 이전 섹션을 저장하고 새로운 섹션을 시작한다.
        if label == 'section_header':
            if current_section:
                sections[current_section] = ' '.join(current_content).strip()

            current_section = text_content
            current_content = []

        elif current_section and label in ['text', 'list_item']:
            current_content.append(text_content)

    if current_section:
        sections[current_section] = ' '.join(current_content).strip()

    return sections

def parse_pdf(path: Path, hashed: str) -> None:
    converter = DocumentConverter()
    try:
        parsed = converter.convert(PDF_DIR / f"{hashed}.pdf").document
        section_contents = extract_sections_with_content(parsed)
        with open(PARSED_DIR / f"{hashed}.json", 'w', encoding='utf-8') as f:
            json.dump(section_contents, f)
    except Exception as e:
        logger.info(f"Parse error {path}: {e}")


# ==== Selenium Helpers ====

def init_browser() -> webdriver.Chrome:
    opts = Options()
    opts.headless = False
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    return driver


def simulate_mouse_continuous(stop_event: Event) -> None:
    while not stop_event.is_set():
        x = random.randint(300, 800)
        y = random.randint(200, 700)
        pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.6))
        time.sleep(random.uniform(1.0, 2.0))


def simulate_in_browser(driver: webdriver.Chrome) -> None:
    body = driver.find_element(By.TAG_NAME, 'body')
    actions = ActionChains(driver)
    for _ in range(5):
        x, y = random.randint(10, 100), random.randint(10, 100)
        try:
            actions.move_to_element_with_offset(body, x, y).pause(0.3)
        except Exception:
            pass
    actions.perform()

# ==== Main Pipeline Functions ====

def _fetch_acm_titles(max_pages: int) -> list[str]:
    with open(TITLE_LIST, "w", encoding='utf-8') as f:
        for page in range(max_pages):
            ACM_QUERY['startPage'] = page
            url = f"{ACM_SEARCH_URL}?{urlencode(ACM_QUERY, quote_via=quote_plus)}"
            logger.info(f"[ACM] Page {page} -> {url}")

            driver = init_browser()
            driver.get(url)
            time.sleep(5)
            simulate_in_browser(driver)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            items = soup.select('li.search__item.issue-item-container')
            driver.quit()
            if not items:
                break

            for it in items:
                tag = it.select_one('h3.issue-item__title a')
                heading = it.select_one('div.issue-heading')
                if tag and heading and 'proceeding' not in heading.text.lower():
                    raw = tag.get_text(' ', strip=True)
                    title = re.sub(r'\s+', ' ', raw)
                    logger.info(f"✔ {title}")
                    titles.append(title)
                    f.write(title + '\n')


def fetch_acm_titles(max_pages: int, use_cache=True) -> list[str]:
    if TITLE_LIST.exists() and use_cache:
        result = TITLE_LIST.read_text(encoding='utf-8').splitlines()
        if result:
            logger.info(f"[ACM] Titles already fetched, loading from {TITLE_LIST}")
            return result

    titles = []
    stop_event = Event()
    mouse_thread = Thread(target=simulate_mouse_continuous, args=(stop_event,), daemon=True)
    mouse_thread.start()

    try:
        _fetch_acm_titles(max_pages)
        time.sleep(1)
    finally:
        stop_event.set()
        if mouse_thread.is_alive():
            mouse_thread.join(timeout=1.0)

    logger.info(f"[ACM] Collected {len(titles)} titles")
    return titles


def fetch_arxiv_papers(titles: list[str], use_cache=True) -> pd.DataFrame:
    if PDF_LINK_CSV.exists() and use_cache:
        result = pd.read_csv(PDF_LINK_CSV)
        if not result.empty:
            logger.info(f"[ArXiv] Links already fetched, loading from {PDF_LINK_CSV}")
            return result

    records = []
    for title in titles:
        search = arxiv.Search(
            query = f"ti:{title}",
            max_results = 1,
            sort_by = arxiv.SortCriterion.Relevance
        )

        paper = next(client.results(search), None)

        # 검색 결과가 없다면 continue
        if paper is None:
            logger.warning(f"[ArXiv] No results found for title: {title}")
            continue

        # 제목 불일치 시 continue
        if similarity(title, paper.title) < 0.9:
            logger.warning(f"[ArXiv] Title mismatch: '{title}' vs '{paper.title}'")
            continue

        hashed = base64.urlsafe_b64encode(paper.title.encode()).decode()
        paper.download_pdf(dirpath=PDF_DIR, filename=f"{hashed}.pdf")
        records.append({
            'Title': paper.title,
            'DOI': paper.doi,
            'PDF_Link': paper.pdf_url,
            'Abstract': paper.summary,
            'Hashed': hashed
        })

    df = pd.DataFrame(records)
    df.to_csv(PDF_LINK_CSV, index=False)
    return df

# ==== CLI Entrypoint ====

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch_titles', action='store_true')
    parser.add_argument('--fetch_papers', action='store_true')
    parser.add_argument('--parse_pdfs', action='store_true')
    args = parser.parse_args()

    if args.fetch_titles:
        titles = fetch_acm_titles(max_pages=50, use_cache=False)

    if args.fetch_papers:
        titles = fetch_acm_titles(max_pages=50, use_cache=True)
        df_links = fetch_arxiv_papers(titles, use_cache=False)

    if args.parse_pdfs:
        titles = fetch_acm_titles(max_pages=50, use_cache=True)
        df_links = fetch_arxiv_papers(titles, use_cache=True)
        for _, row in tqdm.tqdm(df_links.dropna(subset=['PDF_Link']).iterrows(), total=len(df_links)):
            parse_pdf(PARSED_DIR / f"{row['Hashed']}.pdf", row['Hashed'])
