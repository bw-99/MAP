import logging
import random
import time
from threading import Thread
from threading import Event
from urllib.parse import quote_plus, urlencode
from util.process_paper.const import ACM_QUERY, ACM_SEARCH_URL, TITLE_LIST
from bs4 import BeautifulSoup
import re
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

logger = logging.getLogger(__name__)

def init_browser():
    opts = Options()
    opts.headless = False
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    return driver

def simulate_mouse_continuous(stop_event: Event) -> None:
    import pyautogui
    while not stop_event.is_set():
        x = random.randint(300, 800)
        y = random.randint(200, 700)
        pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.6))
        time.sleep(random.uniform(1.0, 2.0))

def _fetch_acm_titles(max_pages: int) -> list[str]:
    titles = []

    with open(TITLE_LIST, "w", encoding='utf-8') as f:
        for page in range(max_pages):
            ACM_QUERY['startPage'] = page
            url = f"{ACM_SEARCH_URL}?{urlencode(ACM_QUERY, quote_via=quote_plus)}"
            logger.info(f"[ACM] Page {page} -> {url}")

            driver = init_browser()
            driver.get(url)
            time.sleep(5)

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

def fetch_titles(use_cache: bool=False) -> list[str]:
    if TITLE_LIST.exists() and use_cache:
        result = TITLE_LIST.read_text(encoding='utf-8').splitlines()
        if result:
            logger.info(f"[ACM] Titles already fetched, loading from {TITLE_LIST}")
            return result

    stop_event = Event()
    mouse_thread = Thread(target=simulate_mouse_continuous, args=(stop_event,), daemon=True)
    mouse_thread.start()

    try:
        _fetch_acm_titles(50)
        time.sleep(1)
    finally:
        stop_event.set()
        if mouse_thread.is_alive():
            mouse_thread.join(timeout=1.0)
