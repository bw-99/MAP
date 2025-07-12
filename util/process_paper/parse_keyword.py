import tqdm
from util.process_paper.parse_pdf import parse_pdfs
from util.process_paper.common import extract_sections_with_content
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
import glob
from util.process_paper.const import PARSED_DIR, PDF_DIR, TMP_DIR
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


def _parse_keywords(converter: DocumentConverter, hashed: str) -> None:
    try:
        parsed = converter.convert(source=PDF_DIR / f"{hashed}.pdf", page_range=(1, 1)).document
        section_contents = extract_sections_with_content(parsed.export_to_dict())
        with open(TMP_DIR / f"{hashed}.json", 'w', encoding='utf-8') as f:
            json.dump(section_contents, f, ensure_ascii=False, indent=2)

        keyword_key = [key for key in section_contents.keys() if 'keyword' in key.lower()]

        if not keyword_key:
            logger.warning(f"No keywords found in {hashed}")
            return

        with open(PARSED_DIR / f"{hashed}.json", 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data['keywords_parsed'] = [item.strip() for item in section_contents[keyword_key[0]].split(',')]
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.info(f"Parse error {hashed}: {e}")

def parse_keywords(use_cache: bool=False):
    parse_pdfs(use_cache=True)

    vlm_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
            ),
        }
    )

    parsed_paper_paths = glob.glob(str(PARSED_DIR / '*.json'))
    for parsed_paper_path in tqdm.tqdm(parsed_paper_paths, total=len(parsed_paper_paths)):
        hashed = Path(parsed_paper_path).stem
        if use_cache and (PARSED_DIR / f"{hashed}.json").exists():
            continue
        _parse_keywords(vlm_converter, hashed)
