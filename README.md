# volunteer-finder

1365 자원봉사포털 봉사활동 검색/저장/리뷰 로컬 웹앱

## 실행 방법

```bash
# 1. 가상환경 생성 및 패키지 설치 (최초 1회)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 서버 실행 (venv 활성화 후)
source venv/bin/activate
python3 app.py
```

브라우저에서 http://localhost:8080 접속

## 주요 기능

- **동기화**: 1365 포털에서 봉사활동 데이터를 로컬 DB로 가져오기 (3스레드 병렬)
- **필터 검색**: 지역/분야/대상/날짜/모집상태/키워드로 로컬 DB 검색
- **AI 검색**: 자연어 입력을 Claude가 해석하여 자동 검색
- **상세 조회**: 봉사활동 상세 정보 (최초 조회 시 API에서 가져옴)
- **저장/리뷰**: 활동 북마크, 별점 + 텍스트 리뷰
- **그룹핑**: 유사 활동(반복 일정) 자동 그룹화

## 구조

```
app.py           # 웹 서버 (Bottle)
scraper.py       # 1365 API 호출 + HTML 파싱
db.py            # SQLite 스키마/쿼리
categorizer.py   # 활동 그룹핑
ai_search.py     # Claude CLI 연동 (AI 검색)
static/          # CSS, JS
views/           # 템플릿 (index, detail, saved)
docs/            # 상세 문서 (검색, 동기화)
```

## 기술 스택

- Python 3.9+ / Bottle / BeautifulSoup4 / SQLite

## 문서

- [검색 기능](docs/search.md)
- [동기화 기능](docs/sync.md)
