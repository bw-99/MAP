from tqdm.asyncio import tqdm
from util.process_paper.parse_pdf import parse_pdfs
from util.process_paper.common import extract_sections_with_content
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
import glob
from util.process_paper.const import KEYWORD_PARSER_MODEL, KEYWORD_SYSTEM_PROMPT, PARSED_DIR, PDF_DIR, TMP_DIR, KEYWORD_KEY, MAX_CONCURRENT_REQUESTS, API_RATE_GAP, API_MAX_RETRY
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
import base64

class Keywords(BaseModel):
    keywords: List[str]

logger = logging.getLogger(__name__)

logger.info("Loading OpenAI client")
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("GRAPHRAG_API_KEY"))
semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def _get_first_page_text(hashed: str) -> str:
    """PDF의 첫 페이지만 텍스트로 추출"""
    try:
        with open(PDF_DIR / f"{hashed}.pdf", "rb") as f:
            reader = PdfReader(f)
            if len(reader.pages) == 0:
                return ""

            # 첫 페이지만 텍스트 추출
            first_page = reader.pages[0]
            text = first_page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting first page text from {hashed}: {e}")
        return ""

async def _parse_keywords(hashed: str) -> None:
    async with semaphore:
        logger.info(f"Parsing keywords for {hashed}...")
        await asyncio.sleep(API_RATE_GAP)

        try:
            # 첫 페이지만 텍스트 추출
            first_page_text = _get_first_page_text(hashed)
            if not first_page_text:
                logger.warning(f"No text found in first page of {hashed}")
                return

            # 기존 파싱된 데이터 로드
            parsed_paper = json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding='utf-8'))

            for attempt in range(1, API_MAX_RETRY + 1):
                try:
                    response = await client.chat.completions.create(
                        model=KEYWORD_PARSER_MODEL,
                        messages=[
                            {"role": "system", "content": KEYWORD_SYSTEM_PROMPT},
                            {"role": "user", "content": f"다음은 논문의 첫 페이지 내용입니다. 키워드를 추출해주세요:\n\n{first_page_text[:2000]}"}  # 텍스트 길이 제한
                        ],
                        response_format={"type": "json_object"}
                    )

                    # JSON 응답 파싱
                    response_data = json.loads(response.choices[0].message.content)
                    keywords = response_data.get("keywords", ["None"])

                    # 결과 저장
                    parsed_paper[KEYWORD_KEY] = keywords
                    json.dump(parsed_paper, open(PARSED_DIR / f"{hashed}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=2)

                    logger.info(f"Successfully parsed keywords for {hashed}: {keywords}")
                    return

                except Exception as e:
                    logger.warning(f"Attempt {attempt} failed for {hashed}: {e}")
                    if attempt < API_MAX_RETRY:
                        await asyncio.sleep(1.0 * attempt)
                    else:
                        # 최종 실패 시 기본값 설정
                        parsed_paper[KEYWORD_KEY] = ["None"]
                        json.dump(parsed_paper, open(PARSED_DIR / f"{hashed}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=2)
                        return

        except Exception as e:
            logger.error(f"Error parsing keywords for {hashed}: {e}")

async def parse_keywords(use_cache: bool=False):
    parse_pdfs(use_cache=True)

    parsed_paper_paths = glob.glob(str(PARSED_DIR / '*.json'))
    tasks = []
    for parsed_paper_path in parsed_paper_paths:
        hashed = Path(parsed_paper_path).stem
        if use_cache and (PARSED_DIR / f"{hashed}.json").exists():
            try:
                parsed_paper = json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding='utf-8'))
                if KEYWORD_KEY in parsed_paper.keys():
                    continue
            except Exception:
                pass
        tasks.append(asyncio.create_task(_parse_keywords(hashed)))
    await tqdm.gather(*tasks)
