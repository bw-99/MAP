import glob
import json
import os
import argparse
from pathlib import Path

from util.process_paper.const import KEYWORD_KEY
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def paper_availability(data: dict) -> bool:
    if not all(item.strip() for item in data[KEYWORD_KEY]):
        return False
    return True


def create_corpus_from_json(data: dict) -> str:
    corpus_parts = []
    for key, value in data.items():
        keys_in_exclude = any(item in key.lower() for item in {"keyword", "reference"})
        if isinstance(value, str) and value.strip() and not keys_in_exclude:
            corpus_parts.append(f"### {key}\n\n{value}")
    return "\n\n".join(corpus_parts)


# CLI arguments parser
parser = argparse.ArgumentParser(description="Process some files.")
parser.add_argument("--root", type=str, default="onepiece_rag", help="Root directory")
parser.add_argument("--num_example", type=int, default=1, help="Number of examples to process")
args = parser.parse_args()

ROOT = args.root
NUM_EXAMPLE = args.num_example

os.makedirs(f"{ROOT}/input", exist_ok=True)
json_flst = glob.glob("data/parsed/*.json")

sample_counts = 0
for _, f_path in enumerate(json_flst):
    if sample_counts >= NUM_EXAMPLE:
        break

    data = json.load(open(f_path, "r", encoding="utf-8"))
    # 부적절한 논문은 제외한다.
    if not paper_availability(data):
        continue

    with open(f"{ROOT}/input/{Path(f_path).stem}.txt", "w", encoding="utf-8") as f:
        f.write(create_corpus_from_json(data))
        sample_counts += 1

logger.info(f"Processed {len(glob.glob(f'{ROOT}/input/*.txt'))} files")
