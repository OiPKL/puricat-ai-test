## 주요 기능 및 고려 사항

#### 🔹 개발 단계

- FastAPI 서버 개발
- SQLite를 사용한 데이터베이스 구현
- Pandas를 사용한 데이터 전처리 구현
- PyTorch 기반으로 GPU 환경에서 파인튜닝 수행

#### 🔹 배포 단계 (CPU 환경)

- 방법1. HuggingFace API를 통해 호출
- 방법2. PyTorch-CPU 사용해 FastAPI에 내장하여 배포 (진행 중)
- 방법3. ONNX 형식으로 변환 후 FastAPI에 내장하여 배포

#### 🔹 고려 사항

- HuggingFace : sLLM 모델 업로드 후 API 호출 시 토큰제한 확인 필요
- ONNX : CPU 환경에서의 효율적 실행 위한 최적화 및 변환 필요

---

## 빌드 및 배포

```bash
1️⃣ 가상환경 설정
#1-1. pip 사용
python 3.11.11 설치 (https://www.python.org/downloads/release/python-31111/)
python -m venv {가상환경 이름}
# (Linux/MacOS)
source {가상환경 이름}/bin/activate
# (Windows)
{가상환경 이름}\Scripts\activate

#1-2. conda 사용
conda create -n {가상환경 이름} python=3.11.11
conda activate {가상환경 이름}

2️⃣ 패키지 설치
pip install -r requirements.txt

3️⃣ (환경설정 파일 복사 후 API Key 수정)
cp .env.example .env

4️⃣ FastAPI 서버 실행
uvicorn app.main:app --port 8000 --reload
```

---

- **Language**: Python 3.11.11
- **Framework**: FastAPI
- **데이터 전처리**: Pandas
- **데이터베이스**: SQLite, SQLAlchemy
- **sLLM 파인튜닝**: PyTorch 2.5.1+cu121, HuggingFace, Transformers, LoRA
- **sLLM 추론모델**: PyTorch 2.5.1+cpu, LangChain
- **sLLM-base**: google/gemma-2-2b-it
- **한국어데이터셋**: daekeun-ml/naver-news-summarization-ko
- **API 문서화**: Swagger
- **빌드 도구**: Uvicorn
- **배포 도구**: Docker, Kubernetes, AWS

---

```
llm/
│── app/
│   ├── database/
│   │   ├── connection.py       # 데이터베이스 연결 설정
│   │   ├── crud.py             # 데이터베이스 CRUD 연산
│   │   ├── models.py           # 데이터베이스 모델 정의
│   ├── models/
│   │   ├── fine_tuned_model/   # 파인튜닝된 sLLM 모델
│   │   ├── convert_onnx.py     # ONNX 변환 테스트
│   │   ├── fewshot_prompt.py   # 퓨샷러닝용 프롬프트 제작
│   │   ├── inference.py        # 모델 로드 및 추론 수행
│   │   ├── model_test.py       # 모델 테스트
│   ├── routers/
│   │   ├── report.py           # 리포트 생성 API 엔드포인트
│   ├── services/
│   │   ├── json_load.py        # 데이터베이스 조회 후 JSON 로드
│   │   ├── preprocess.py       # 데이터 전처리 후 데이터베이스 저장
│   │   ├── recommendation.py   # sLLM 모델 추론 결과 업데이트
│   ├── __init__.py
│   ├── main.py                 # FastAPI App 실행
│── .gitignore
│── dummy.json
│── README.md
│── requirements.txt
```
