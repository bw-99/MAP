import argparse
import logging
from util.process_paper import (
    fetch_titles,
    fetch_links,
    fetch_pdfs,
    parse_pdfs,
    parse_keywords,
    parse_references
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--function', type=str, required=True, choices=['fetch_titles', 'fetch_links', 'fetch_pdfs', 'parse_pdfs', 'parse_keywords', "parse_references"])
    args = parser.parse_args()

    globals()[args.function](use_cache=False)
