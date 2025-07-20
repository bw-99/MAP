import glob
import json
import os
import tqdm
import argparse
from pathlib import Path


def create_corpus_from_json(data: dict) -> str:
    corpus_parts = []
    for key, value in data.items():
        keys_in_exclude = any(item in key.lower() for item in {"keyword", "reference"})
        if isinstance(value, str) and value.strip() and not keys_in_exclude:
            corpus_parts.append(f"### {key}\n\n{value}")
    return "\n\n".join(corpus_parts)


# CLI arguments parser
parser = argparse.ArgumentParser(description="Process some files.")
parser.add_argument('--root', type=str, default="onepiece_rag", help='Root directory')
parser.add_argument('--num_example', type=int, default=1, help='Number of examples to process')
args = parser.parse_args()

ROOT = args.root
NUM_EXAMPLE = args.num_example

os.makedirs(f"{ROOT}/input", exist_ok=True)
json_flst = glob.glob("data/parsed/*.json")
json_flst = json_flst[:NUM_EXAMPLE]

for idx, f_path in tqdm.tqdm(enumerate(json_flst), total=len(json_flst)):
    data = json.load(open(f_path, "r", encoding='utf-8'))
    corpus = create_corpus_from_json(data)

    with open(f"{ROOT}/input/{Path(f_path).stem}.txt", "w", encoding='utf-8') as f:
        f.write(corpus)

print(f"Processed {len(glob.glob(f'{ROOT}/input/*.txt'))} files")
