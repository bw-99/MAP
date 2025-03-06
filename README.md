## GraphRAG Developments

### Docker Prep
1. cd to workspace
2. `docker pull bb1702/onepiece:main`
3. `docker run -dit --name con --shm-size=20g -v .:/workspace bb1702/onepiece:main`

### Run GraphRAG
1. Enter the container via `docker attach con`
2. `python3 -m graphrag ${command}` [command](https://microsoft.github.io/graphrag/get_started/)

### Dev dependency
1. Install pre-commit on your dev environment (not docker, terminal you choose to use `git commit`) via `pip install pre-commit`

### Tutorial
0. 프로젝트 폴더에 example 폴더 생성
1. (플젝 초기화) `python3 -m graphrag init --root ./example`
2. (환경설정 가져오기) onepiece_rag 폴더 안에 prompts, setting.yml을 example 안에 같은 파일/폴더 덮어씌우기
3. (API key) example 폴더 아래에 .env 생성 & 개인적으로 전달받은 내용 작성
4. (디버깅용 데이터 준비하기) `python3 util/debugging_data.py --root example --num_example 1`
5. (인덱싱) `python3 -m graphrag index --root ./example`
6. (결과) example/output/create_final_viztree 파일 pandas로 열기

## Data Preperations

### Install & Run GROBOID Docker Container
1. docker run --rm --gpus all --init --ulimit core=0 -p 8070:8070 grobid/grobid:${latest_grobid_version}

### Install scipdf parser librarary
1. pip install git+https://github.com/titipata/scipdf_parser
2. python -m spacy download en_core_web_sm

### Scripts
1. Run `python3 -m util.arxiv` to fetch relavant research papers and corresponding meta-data from arxiv.org
2. Run `python3 -m util.parse` to download the whole paper and parse the paper
3. Run `python3 -m util.debugging_data --root onepiece_rag --num_example 1` to generate the data for debugging

## How to Run (use deploy version)
1. cd to workspace
2. `docker pull bb1702/onepiece:main`
3. `docker run --name con_exec --shm-size=20g -v .:/workspace bb1702/onepiece:main`
