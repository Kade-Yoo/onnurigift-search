## 온누리 가맹점 검색 API (FastAPI + SQLite)

공공데이터포털의 온누리상품권 가맹점 파일데이터(CSV)를 로컬 DB로 적재하고,
간단한 검색 API를 제공합니다. 데이터 출처는 공공데이터포털입니다. 참고: [소상공인시장진흥공단_전국 온누리상품권 가맹점 현황](https://www.data.go.kr/data/3060079/fileData.do?recommendDataYn=Y#/API%20%EB%AA%A9%EB%A1%9D/getuddi%3A0e9db925-b81a-4d7b-9cf5-f55007706d7e)

### 1) 준비
- Python 3.10+
- 가상환경 권장
- CSV 파일 다운로드 후 절대 경로 확인

### 2) 설치
```bash
pip install -r requirements.txt
```

### 3) 환경변수 설정
`.env` 파일 생성 후 아래 값을 설정하세요.
```bash
CSV_SOURCE_PATH=/absolute/path/to/onnuri_stores.csv
DATABASE_PATH=/absolute/path/to/data/onnuri.db
```

### 4) 데이터 적재
```bash
python scripts/seed.py
```

### 5) 서버 실행
```bash
uvicorn app.main:app --reload
```

### 6) API
- 헬스체크: `GET /health`
- 가맹점 검색: `GET /stores`
  - 쿼리 파라미터
    - `q`: 통합검색(가맹점명/주소/취급품목)
    - `market`, `address`, `category`
    - `card`, `paper`, `mobile` (true/false)
    - `year` (숫자), `page`(기본 1), `size`(기본 20, 최대 200)

예시:
```
GET /stores?q=정육&address=서울&card=true&page=1&size=20
```

### 비고
- CSV 스키마는 다음 컬럼을 기대합니다: `가맹점명, 소속 시장명(또는 상점가), 소재지, 취급품목, 충전식 카드 취급여부, 지류 취급여부, 모바일 취급여부, 등록년도`
- 데이터 출처: `공공데이터포털` [링크](https://www.data.go.kr/data/3060079/fileData.do?recommendDataYn=Y#/API%20%EB%AA%A9%EB%A1%9D/getuddi%3A0e9db925-b81a-4d7b-9cf5-f55007706d7e)