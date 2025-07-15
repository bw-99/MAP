import tqdm
from util.process_paper.parse_pdf import parse_pdfs
from util.process_paper.common import extract_sections_with_content
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
import glob
from util.process_paper.const import PARSED_DIR, PDF_DIR, TMP_DIR, REFERENCE_KEY
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


def _parse_references(hashed: str) -> None:
    parsed_paper = json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding='utf-8'))
    refer_key = [item for item in parsed_paper.keys() if item.lower().startswith("reference")]
    refer_key = refer_key[0] if refer_key else None
    references = parsed_paper.get(refer_key, "")
    parsed_paper[REFERENCE_KEY] = references
    json.dump(parsed_paper, open(PARSED_DIR / f"{hashed}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=2)

def parse_references(use_cache: bool=False):
    parse_pdfs(use_cache=True)

    parsed_paper_paths = glob.glob(str(PARSED_DIR / '*.json'))
    for parsed_paper_path in tqdm.tqdm(parsed_paper_paths, total=len(parsed_paper_paths)):
        hashed = Path(parsed_paper_path).stem
        if use_cache and (PARSED_DIR / f"{hashed}.json").exists() and REFERENCE_KEY in json.load(open(PARSED_DIR / f"{hashed}.json", "r", encoding='utf-8')).keys():
            continue
        _parse_references(hashed)
