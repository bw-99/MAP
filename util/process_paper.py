import os
import time
import argparse
import random
import base64
import json
import re
import requests
import pyautogui
import pandas as pd
import tqdm
import scipdf
from threading import Thread
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from difflib import SequenceMatcher
from util.const import TITLE_LIST, PDF_LINK_CSV, PARSED_DIR

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

def download_pdf(path: Path, url: str) -> None:
    if path.exists():
        return
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)
    except Exception as e:
        print(f"Failed download {url}: {e}")


def parse_pdf(path: Path, hashed: str) -> None:
    out = PARSED_DIR / f"{hashed}.json"
    try:
        data = scipdf.parse_pdf_to_dict(path)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Parse error {path}: {e}")
    finally:
        if path.exists():
            path.unlink()

# ==== Selenium Helpers ====

def init_browser() -> webdriver.Chrome:
    opts = Options()
    opts.headless = False
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    return driver


def simulate_mouse_continuous() -> None:
    while True:
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

def fetch_acm_titles(max_pages: int, use_cache=True) -> list[str]:
    if TITLE_LIST.exists() and not use_cache:
        print(f"[ACM] Titles already fetched, loading from {TITLE_LIST}")
        TITLE_LIST.read_text(encoding='utf-8').splitlines() if TITLE_LIST.exists() else []

    titles = []
    Thread(target=simulate_mouse_continuous, daemon=True).start()
    with open(TITLE_LIST, "w", encoding='utf-8') as f:
        for page in range(max_pages):
            ACM_QUERY['startPage'] = page
            url = f"{ACM_SEARCH_URL}?{urlencode(ACM_QUERY, quote_via=quote_plus)}"
            print(f"[ACM] Page {page} -> {url}")

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
                    title = similar = re.sub(r'\s+', ' ', raw)
                    print(f"✔ {title}")
                    titles.append(title)
                    f.write(title + '\n')
            time.sleep(1)

    print(f"[ACM] Collected {len(titles)} titles")
    return titles


def fetch_arxiv_links(titles: list[str], use_cache=True) -> pd.DataFrame:
    if PDF_LINK_CSV.exists() and not use_cache:
        print(f"[ArXiv] Links already fetched, loading from {PDF_LINK_CSV}")
        return pd.read_csv(PDF_LINK_CSV)

    records = []
    for title in titles[:10]:
        url = ARXIV_SEARCH_TEMPLATE.format(quote_plus(title))
        print(f"[ArXiv] Searching -> {url}")
        resp = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        item = soup.select_one('li.arxiv-result')
        if not item:
            continue
        atitle = item.select_one('p.title')
        at = atitle.text.strip() if atitle else ''
        if similarity(title, at) < 0.9:
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
        hashed = base64.urlsafe_b64encode(at.encode()).decode()
        records.append({
            'Title': at,
            'DOI': doi,
            'PDF_Link': pdf_link,
            'Abstract': abstract,
            'Hashed': hashed
        })
        time.sleep(1)
    df = pd.DataFrame(records)
    df.to_csv(PDF_LINK_CSV, index=False)
    return df

# ==== CLI Entrypoint ====

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch_titles', action='store_true')
    parser.add_argument('--fetch_links', action='store_true')
    parser.add_argument('--download_pdfs', action='store_true')
    parser.add_argument('--parse_pdfs', action='store_true')
    args = parser.parse_args()

    if args.fetch_titles:
        titles = fetch_acm_titles(max_pages=50, use_cache=False)

    if args.fetch_links:
        titles = fetch_acm_titles(max_pages=50, use_cache=True)
        df_links = fetch_arxiv_links(titles)

    if args.download_pdfs:
        titles = fetch_acm_titles(max_pages=50, use_cache=True)
        df_links = fetch_arxiv_links(titles, use_cache=True)
        for _, row in tqdm.tqdm(df_links.dropna(subset=['PDF_Link']).iterrows(), total=len(df_links)):
            download_pdf(PARSED_DIR / f"{row['Hashed']}.pdf", row['PDF_Link'])

    if args.parse_pdfs:
        titles = fetch_acm_titles(max_pages=50, use_cache=True)
        df_links = fetch_arxiv_links(titles, use_cache=True)
        for _, row in tqdm.tqdm(df_links.dropna(subset=['PDF_Link']).iterrows(), total=len(df_links)):
            parse_pdf(PARSED_DIR / f"{row['Hashed']}.pdf", row['Hashed'])
