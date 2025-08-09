import argparse
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--function",
        type=str,
        required=True,
        choices=["fetch_titles", "fetch_links", "fetch_pdfs", "parse_pdfs", "parse_keywords", "parse_references"],
    )
    args = parser.parse_args()

    function = globals()[args.function]

    # 비동기 함수인지 확인하고 실행
    if asyncio.iscoroutinefunction(function):
        asyncio.run(function(use_cache=False))
    else:
        function(use_cache=False)
