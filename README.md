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

## 기능

- 지역/분야/대상/날짜/모집상태 필터 검색
- 봉사활동 상세 조회
- 활동 저장(북마크)
- 리뷰 작성 (별점 + 텍스트)
- 유사 활동 자동 그룹핑

## 기술 스택

- Python 3.9+
- Bottle (웹 프레임워크)
- BeautifulSoup4 (HTML 파싱)
- SQLite (데이터 저장)
