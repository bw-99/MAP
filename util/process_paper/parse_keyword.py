from tqdm.asyncio import tqdm
from util.process_paper.parse_pdf import parse_pdfs
import glob
from util.process_paper.const import API_RATE_GAP, API_MAX_RETRY, KEYWORD_PARSER_MODEL, KEYWORD_SYSTEM_PROMPT, PARSED_DIR, PDF_DIR, TMP_DIR, KEYWORD_KEY, MAX_CONCURRENT_REQUESTS
from pathlib import Path
import json
import logging
from pydantic import BaseModel
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import asyncio
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import shutil

class Keywords(BaseModel):
    keywords: List[str]

logger = logging.getLogger(__name__)

logger.info("Loading OpenAI client")
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("GRAPHRAG_API_KEY"))
semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def _get_first_page(hashed: str) -> BytesIO:
    with open(PDF_DIR / f"{hashed}.pdf", "rb") as f:
        reader = PdfReader(f)
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
    output_path = TMP_DIR / "pdf" / f"{hashed}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path

async def _parse_keywords(hashed: str) -> None:
    async with semaphore:
        logger.info(f"Parsing keywords for {hashed}...")
        await asyncio.sleep(API_RATE_GAP)
        parsed_paper = json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding='utf-8'))
        output_path = _get_first_page(hashed)
        for attempt in range(1, API_MAX_RETRY + 1):
            try:
                file = await client.files.create(
                    file=open(output_path, "rb"),
                    purpose="user_data"
                )
                response = await client.responses.parse(
                    model=KEYWORD_PARSER_MODEL,
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_file", "file_id": file.id},
                                {"type": "input_text", "text": KEYWORD_SYSTEM_PROMPT},
                            ],
                        },
                    ],
                    text_format=Keywords
                )
                extracted_keywords = [keyword.strip() for keyword in response.output_parsed.keywords]
                extracted_keywords = [keyword for keyword in extracted_keywords if keyword in str(parsed_paper)]
                parsed_paper[KEYWORD_KEY] = extracted_keywords
                logger.info(f"Extracted keywords: {extracted_keywords}")
                json.dump(parsed_paper, open(PARSED_DIR / f"{hashed}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=2)
                return extracted_keywords

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < API_MAX_RETRY:
                    await asyncio.sleep(1.0 * attempt)
                else:
                    parsed_paper[KEYWORD_KEY] = []
                    return

async def parse_keywords(use_cache: bool=False):
    parse_pdfs(use_cache=True)

    parsed_paper_paths = glob.glob(str(PARSED_DIR / '*.json'))
    tasks = []
    for parsed_paper_path in parsed_paper_paths:
        hashed = Path(parsed_paper_path).stem
        if use_cache and (PARSED_DIR / f"{hashed}.json").exists():
            continue
        tasks.append(asyncio.create_task(_parse_keywords(hashed)))
    await tqdm.gather(*tasks)
    shutil.rmtree(TMP_DIR / "pdf")
