from docling.document_converter import DocumentConverter
import tqdm
from util.process_paper.fetch_pdf import fetch_pdfs
from util.process_paper.common import extract_sections_with_content
from util.process_paper.const import PARSED_DIR, PDF_DIR
import json
import logging
import glob
from pathlib import Path

logger = logging.getLogger(__name__)


def _parse_pdf(converter: DocumentConverter, hashed: str) -> None:
    try:
        parsed = converter.convert(PDF_DIR / f"{hashed}.pdf").document
        section_contents = extract_sections_with_content(parsed.export_to_dict())
        with open(PARSED_DIR / f"{hashed}.json", "w", encoding="utf-8") as f:
            json.dump(section_contents, f)
    except Exception as e:
        logger.info(f"Parse error {hashed}: {e}")


def parse_pdfs(use_cache: bool = False):
    fetch_pdfs(use_cache=True)

    pdf_paths = glob.glob(str(PDF_DIR / "*.pdf"))
    converter = DocumentConverter()
    for pdf_path in tqdm.tqdm(pdf_paths, total=len(pdf_paths)):
        hashed = Path(pdf_path).stem
        if use_cache and (PARSED_DIR / f"{hashed}.json").exists():
            continue
        _parse_pdf(converter, hashed)
