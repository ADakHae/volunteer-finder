# 동기화 기능

## 개요

1365 자원봉사포털 API에서 봉사활동 목록을 가져와 로컬 SQLite DB에 저장한다. 검색은 로컬 DB에서 수행하므로 동기화가 선행되어야 한다.

## 동기화 흐름

```
동기화 버튼 클릭
  → POST /api/sync (필터 파라미터 포함)
  → 백그라운드 스레드 시작
  → 1페이지 순차 요청 (total_pages 파악)
  → 나머지 페이지 3개 스레드 병렬 요청
  → DB INSERT OR IGNORE
  → 완료
```

### 상세 단계

1. **필터 수집**: JS에서 현재 필터 폼의 값을 `FormData`로 수집하여 POST 전송
2. **백그라운드 스레드**: Bottle은 단일 스레드이므로 `threading.Thread`로 동기화 실행
3. **페이지 순회**: 1365 API는 페이지당 10건 반환. 첫 페이지에서 전체 건수 파악 후 나머지 병렬 요청
4. **DB 저장**: `INSERT OR IGNORE`로 신규 활동만 추가, 기존 데이터 보존
5. **진행률 폴링**: JS가 2초마다 `GET /api/sync-status` 호출하여 UI 업데이트

## 병렬 요청

`ThreadPoolExecutor(max_workers=3)`으로 동시 3개 HTTP 요청을 보낸다.

```python
# scraper.py sync_filtered()
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(fetch_one, pg): pg for pg in range(2, total_pages + 1)}
    for future in as_completed(futures):
        pg, res = future.result()
        # ... 결과 처리
```

- 1페이지: 순차 (전체 페이지 수 파악)
- 2페이지~: 3개 스레드 병렬
- 효과: 100페이지 기준 ~100초 → ~35초 (약 3배 빠름)
- 정부 포털이므로 과도한 병렬 요청 자제 (3개가 적정)

## DB 저장 전략

```sql
INSERT OR IGNORE INTO activities (...) VALUES (...)
```

- **PRIMARY KEY**: `program_id`
- **이미 존재하면**: 무시 (기존 데이터 보존)
- **신규면**: 추가
- **상세 페이지에서 가져온 데이터**: 덮어쓰지 않음 (detail_fetched로 관리)

### 재동기화 시

같은 필터로 다시 동기화하면:
- HTTP 요청 시간은 동일 (API가 변경분만 제공하지 않음)
- DB 저장은 대부분 IGNORE → 신규 활동만 추가됨

## 동기화 상태 관리

```python
# app.py
sync_state = {
    "running": False,     # 동기화 진행 중 여부
    "page": 0,            # 현재 페이지
    "total_pages": 0,     # 전체 페이지 수
    "fetched": 0,         # 가져온 건수
    "error": None,        # 오류 메시지
}
```

- `POST /api/sync` → 동기화 시작, `{"started": true}` 반환
- `GET /api/sync-status` → 현재 상태 반환 (진행률, DB 통계 포함)
- 중복 실행 방지: `sync_state["running"]`이 True면 거부

## SQLite 스레드 안전

SQLite 객체는 스레드 간 공유 불가. 동기화 스레드에서 별도 연결을 생성한다.

```python
def run_sync():
    sync_conn = db.get_conn()  # 별도 연결
    try:
        # ... 동기화 로직
    finally:
        sync_conn.close()
```

## 프론트엔드 연동

```javascript
// main.js
syncBtn.click → fetch POST /api/sync (필터 폼 값 포함)
  → pollSync() 시작 (2초 간격)
  → 진행률 표시: "동기화 중... 45%"
  → 완료 시: "150건 완료!" → 1초 후 페이지 새로고침
```

## 데이터 규모 참고

| 조건 | 예상 페이지 수 | 예상 시간 (3스레드) |
|------|-------------|------------------|
| 서울 전체 | ~185 | ~65초 |
| 서울 + 분야 지정 | ~20-50 | ~10-20초 |
| 특정 시군구 + 분야 | ~5-15 | ~3-7초 |

필터를 좁힐수록 동기화가 빨라진다.

## 관련 파일

- `scraper.py` — `sync_filtered()` 병렬 페이지 수집
- `app.py` — `api_sync()`, `api_sync_status()` 라우트
- `db.py` — `upsert_activities()`, `get_sync_stats()`
- `static/main.js` — 동기화 버튼 + 폴링 로직
