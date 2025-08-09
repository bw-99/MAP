import base64


def decode_paper_title(paper_path: str) -> str:
    return base64.urlsafe_b64decode(paper_path.encode()).decode()


def encode_paper_title(paper_title: str) -> str:
    return base64.urlsafe_b64encode(paper_title.encode()).decode()
