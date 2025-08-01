## GraphRAG Developments

### Dev dependency
1. Install pre-commit on your dev environment (not docker, terminal you choose to use `git commit`) via `pip install pre-commit`

### Tutorial
0. 프로젝트 폴더에 example 폴더 생성
1. (플젝 초기화) `python -m graphrag init --root example`
2. (환경설정 가져오기) onepiece_rag 폴더 안에 prompts, setting.yml을 example 안에 같은 파일/폴더 덮어씌우기
3. (API key) example 폴더 아래에 .env 생성 & 개인적으로 전달받은 내용 작성
4. (논문 데이터 준비하기) **data/parsed 아래에 데이터가 있을 경우 시행할 필요없다**
   1) (논문 가져오고 기본적인 파싱) `python -m util.process_paper --function parse_pdfs`
   2) (핵심 키워드 추출) `python -m util.process_paper --function parse_keywords`
   3) (레퍼런스 목록 추출) `python -m util.process_paper --function parse_references`
5. (논문 데이터 최종 전처리) `python -m util.preprocess --root example --num_example 10`
6. (인덱싱) `python3 -m graphrag index --root example`
7. (결과) example/output/create_final_viztree 파일 pandas로 열기

## How to Run (use deploy version)
1. cd to workspace
2. `docker pull bb1702/onepiece:main`
3. `docker run --name con_exec --shm-size=20g -v .:/workspace bb1702/onepiece:main`
