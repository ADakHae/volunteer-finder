# 검색 기능

## 개요

1365 자원봉사포털 데이터를 로컬 SQLite DB에서 검색한다. API를 매번 호출하지 않고 동기화된 데이터를 대상으로 빠르게 필터링한다.

## 검색 흐름

```
사용자 → 필터 폼 입력 → GET /search → DB 쿼리 → 결과 렌더링
```

1. 사용자가 필터 폼에서 조건을 선택하고 "검색" 클릭
2. `GET /search`로 쿼리스트링 전달
3. `app.py`에서 코드값을 텍스트로 변환 (예: `6110000` → `서울특별시`)
4. `db.search_activities()`로 SQLite 쿼리 실행
5. 결과를 그룹핑하여 템플릿에 전달

## 필터 항목

| 필터 | DB 컬럼 | 매칭 방식 |
|------|---------|----------|
| 시/도 | `location` | LIKE `%지역명%` |
| 시군구 | (시/도에 포함) | - |
| 봉사분야 | `category` | LIKE `%분야명%` |
| 활동구분 | `activity_type` | LIKE `%구분명%` |
| 봉사대상 | `target` | LIKE `%대상명%` |
| 모집상태 | `recruit_status` | 정확 매칭 (`모집중` / `모집완료`) |
| 봉사기간 시작 | `period_end` | `period_end >= date_start` |
| 봉사기간 종료 | `period_start` | `period_start <= date_end` |
| 키워드 | `title`, `organization` | LIKE `%keyword%` |

## 코드-텍스트 변환

필터 폼은 1365 API 코드값을 사용하고, DB에는 텍스트가 저장되어 있으므로 검색 시 변환이 필요하다.

```python
# app.py search_page()
db_filters["category"] = scraper.CATEGORY_CODES.get(category, category)
# "0800" → "환경·생태계보호"
```

주요 코드 매핑:
- 지역: `scraper.REGION_CODES` (예: `6110000` → `서울특별시`)
- 분야: `scraper.CATEGORY_CODES` (예: `0800` → `환경·생태계보호`)
- 활동구분: `scraper.ACTIVITY_TYPE_CODES` (예: `2` → `오프라인`)
- 대상: `scraper.TARGET_CODES` (예: `1` → `아동·청소년`)

## AI 검색

자연어 입력을 Claude CLI(haiku)가 해석하여 검색 파라미터로 변환한다.

```
"서울에서 주말에 할 수 있는 환경 봉사"
  → { region: "6110000", category: "0800", status: "0", keyword: "주말" }
  → /search?region=6110000&category=0800&status=0&keyword=주말 리다이렉트
```

- 바이너리: VSCode 확장에 포함된 Claude Code CLI
- 모델: haiku (빠르고 저렴)
- 구현: `ai_search.py` → `parse_natural_query()`

## 페이지네이션

- 페이지당 10건
- 최대 20페이지까지 표시
- 쿼리스트링에 `page` 파라미터 추가

## 결과 그룹핑

동일한 봉사활동의 반복 일정(1일차, 2일차 등)을 하나의 그룹으로 묶어 표시한다.

- `categorizer.compute_group_key(title)`: 제목에서 날짜/회차 부분 제거하여 정규화
- `categorizer.group_activities(items)`: group_key 기준으로 그룹핑

## 관련 파일

- `app.py` — `search_page()` 라우트
- `db.py` — `search_activities()` 쿼리
- `categorizer.py` — 그룹핑 로직
- `ai_search.py` — AI 자연어 검색
- `views/index.tpl` — 검색 폼 + 결과 UI
