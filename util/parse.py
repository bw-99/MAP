import scipdf
import pandas as pd
from const import *
import requests
import json
import tqdm
import warnings
from bs4 import XMLParsedAsHTMLWarning

def download_pdf(url, Hashed):
    tmp_path = f"{PARSED_PATH}/{Hashed}.pdf"
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(tmp_path, 'wb') as file:
            file.write(response.content)
    except Exception as e:
        print(f'Error during download: {e}')
    return tmp_path


def parse_pdf(pdf_path, Hashed):
    output_path = f"{PARSED_PATH}/{Hashed}.json"
    try:
        article_dict = scipdf.parse_pdf_to_dict(pdf_path)
        with open(output_path, "w") as f:
            json.dump(article_dict, f)
    except Exception as e:
        print(f'Error during parsing: {e}')
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__=="__main__":
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    
    df = pd.read_csv(CSV_PATH)
    df = df.iloc[df.notna()["PDF Link"].values]
    
    for idx, row in tqdm.tqdm(df.iterrows(), total=df.shape[0]):
        Hashed, url = row["Hashed"], row["PDF Link"]
        if os.path.exists(f"{PARSED_PATH}/{Hashed}.json"):
            continue
        pdf_path = download_pdf(url=url, Hashed=Hashed)
        parse_pdf(pdf_path=pdf_path, Hashed=Hashed)
        