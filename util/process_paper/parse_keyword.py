import tqdm
from util.process_paper.parse_pdf import parse_pdfs
from util.process_paper.common import extract_sections_with_content
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
import glob
from util.process_paper.const import PARSED_DIR, PDF_DIR, TMP_DIR, KEYWORD_KEY
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
        keyword_key = keyword_key[0] if keyword_key else None

        with open(PARSED_DIR / f"{hashed}.json", 'r+', encoding='utf-8') as f:
            prev_parsed = json.load(f)
            prev_parsed_key = [key for key in prev_parsed.keys() if 'keyword' in key.lower()]
            prev_parsed_key = prev_parsed_key[0] if prev_parsed_key else None

            if not prev_parsed_key:
                prev_parsed[KEYWORD_KEY] = ["None"]
                f.seek(0)
                f.truncate()
                json.dump(prev_parsed, f, ensure_ascii=False, indent=2)
                return

            # 네 가지 경우가 있을 수 있는데, 이 중 split 해서 가장 긴 배열을 키워드로 인정한다.
            # 1. 키워드가 이미 전 단계에서 뽑힌 경우
            #   1. 콤마로 구분되는 문자열
            #   2. 세미콜론으로 구분되는 문자열
            # 2. VLM으로 뽑은 경우
            #   1. 콤마로 구분되는 문자열
            #   2. 세미콜론으로 구분되는 문자열
            keyword_candidates = [
                prev_parsed.get(prev_parsed_key, "").split(","),
                prev_parsed.get(prev_parsed_key, "").split(";"),
                [item.strip() for item in section_contents[keyword_key].split(',')],
                [item.strip() for item in section_contents[keyword_key].split(';')],
            ]
            keyword_lengths = [len(item) for item in keyword_candidates]
            keyword_index = keyword_lengths.index(max(keyword_lengths))
            # 조건에 부합하는 키워드가 없다면 None으로 처리한다.
            prev_parsed[KEYWORD_KEY] = keyword_candidates[keyword_index] if max(keyword_lengths) > 1 else ["None"]
            f.seek(0)
            f.truncate()
            json.dump(prev_parsed, f, ensure_ascii=False, indent=2)

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
