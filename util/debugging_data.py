import glob
import json
import os
import tqdm
import argparse

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

keys_to_extract = {'abstract', 'sections'}

for idx, fname in tqdm.tqdm(enumerate(json_flst), total=len(json_flst)):
    corpus = ""
    data = json.load(open(fname, "r"))
    data = {key: value for key, value in data.items() if key in keys_to_extract}
    queue = list(zip(list(data.keys()), list(data.values()), [1 for _ in range(len(data.items()))]))
    while queue:
        tmp_key, tmp_data, tmp_depth = queue.pop(0)
        corpus += f"<h{tmp_depth}>{tmp_key}</h{tmp_depth}>"
        if type(tmp_data) is dict:
            queue = list(zip(list(tmp_data.keys()), list(tmp_data.values()), [tmp_depth+1 for _ in range(len(tmp_data.items()))])) + queue
        elif type(tmp_data) is list and len(tmp_data) > 0 and type(tmp_data[0]) is dict:
            tmp_queue = []
            for tmp in tmp_data:
                tmp_queue = tmp_queue + list(zip(list(tmp.keys()), list(tmp.values()), [tmp_depth+1 for _ in range(len(tmp.items()))]))
            queue = tmp_queue + queue
        else:
            cleaned_text = str(tmp_data).replace("{", "").replace("}", "")
            corpus += " <p>"+cleaned_text+" </p>"
    fname = fname.split("/")[-1].split(".json")[0]
    with open(f"{ROOT}/input/{fname}.txt", "w") as f:
        f.write(corpus)

print(len(glob.glob(f"{ROOT}/input/*.txt")))
