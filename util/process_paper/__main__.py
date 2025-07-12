import argparse
import logging
from util.process_paper.fetch_title import fetch_titles
from util.process_paper.fetch_link import fetch_links
from util.process_paper.fetch_pdf import fetch_pdfs
from util.process_paper.parse_pdf import parse_pdfs
from util.process_paper.parse_keyword import parse_keywords

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--function', type=str, required=True, choices=['fetch_titles', 'fetch_links', 'fetch_pdfs', 'parse_pdfs', 'parse_keywords'])
    args = parser.parse_args()

    globals()[args.function](use_cache=False)
