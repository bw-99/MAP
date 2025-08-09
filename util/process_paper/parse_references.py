from util.process_paper.parse_pdf import parse_pdfs
import glob
from util.process_paper.const import (
    API_MAX_RETRY,
    REFERNCE_PARSER_MODEL,
    API_RATE_GAP,
    MAX_CONCURRENT_REQUESTS,
    PARSED_DIR,
    REFERENCE_KEY,
    REFERENCE_SYSTEM_PROMPT,
)
from pathlib import Path
import json
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
from typing import List
from pydantic import BaseModel
import asyncio
from tqdm.asyncio import tqdm


class Citation(BaseModel):
    ref_id: int
    title: str


class CitationList(BaseModel):
    citations: List[Citation]


logger = logging.getLogger(__name__)

logger.info("Loading OpenAI client")
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("GRAPHRAG_API_KEY"))
semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def _parse_references(hashed: str) -> None:
    parsed_paper = json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding="utf-8"))
    refer_key = [item for item in parsed_paper.keys() if item.lower().startswith("reference")]
    refer_key = refer_key[0] if refer_key else None
    references = parsed_paper.get(refer_key, "")

    async with semaphore:
        logger.info(f"Parsing references for {hashed}...")
        await asyncio.sleep(API_RATE_GAP)
        for attempt in range(1, API_MAX_RETRY + 1):
            try:
                response = await client.responses.parse(
                    model=REFERNCE_PARSER_MODEL,
                    input=[
                        {"role": "system", "content": REFERENCE_SYSTEM_PROMPT},
                        {"role": "user", "content": f"--Real world data--\n\n{references}\n\n--Output--"},
                    ],
                    text_format=CitationList,
                )
                parsed_paper[REFERENCE_KEY] = [
                    {"ref_id": f"b{citation.ref_id}", "title": citation.title}
                    for citation in response.output_parsed.citations
                ]

                json.dump(
                    parsed_paper,
                    open(PARSED_DIR / f"{hashed}.json", "w", encoding="utf-8"),
                    ensure_ascii=False,
                    indent=2,
                )
                return

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < API_MAX_RETRY:
                    await asyncio.sleep(1.0 * attempt)
                else:
                    parsed_paper[REFERENCE_KEY] = []
                    return


async def parse_references(use_cache: bool = False):
    parse_pdfs(use_cache=True)

    parsed_paper_paths = glob.glob(str(PARSED_DIR / "*.json"))
    tasks = []
    for parsed_paper_path in parsed_paper_paths:
        hashed = Path(parsed_paper_path).stem
        if (
            use_cache
            and (PARSED_DIR / f"{hashed}.json").exists()
            and REFERENCE_KEY in json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding="utf-8")).keys()
        ):
            continue
        tasks.append(asyncio.create_task(_parse_references(hashed)))
    await tqdm.gather(*tasks)
