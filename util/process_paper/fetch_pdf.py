import requests
from pathlib import Path
import logging
from util.process_paper.fetch_link import fetch_links
from util.process_paper.const import PDF_DIR
import tqdm

logger = logging.getLogger(__name__)


def _download_pdf(path: Path, url: str) -> None:
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)
    except Exception as e:
        logger.info(f"Failed download {url}: {e}")


def fetch_pdfs(use_cache: bool = False) -> None:
    df_links = fetch_links(use_cache=True)
    for _, row in tqdm.tqdm(df_links.dropna(subset=["PDF_Link"]).iterrows(), total=len(df_links)):
        if use_cache and (PDF_DIR / f"{row['Hashed']}.pdf").exists():
            continue
        _download_pdf(PDF_DIR / f"{row['Hashed']}.pdf", row["PDF_Link"])
