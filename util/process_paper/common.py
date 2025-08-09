def extract_sections_with_content(parsed_data: dict) -> dict:
    sections = {}
    current_section = None
    current_content = []

    for text in parsed_data.get("texts", []):
        text_content = text.get("text", "")
        label = text.get("label", "")

        # docling은 추출할 때 1. Intro, 3.1 Overview 등을 모두 section_header 이름으로 추출해둔다.
        # 이를 이용해서 섹션 헤더 별 내용을 세분화해서 저장해둔다.
        # 새로운 섹션 헤더를 발견하면 이전 섹션을 저장하고 새로운 섹션을 시작한다.
        if label == "section_header":
            if current_section:
                sections[current_section] = " ".join(current_content).strip()

            current_section = text_content
            current_content = []

        elif current_section:
            current_content.append(text_content)

    if current_section:
        sections[current_section] = " ".join(current_content).strip()

    return sections
