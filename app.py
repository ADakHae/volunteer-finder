import os
import json
import urllib.parse
import threading
from datetime import datetime, timedelta
from bottle import Bottle, request, response, redirect, static_file, template, TEMPLATE_PATH

import db
import scraper
from categorizer import compute_group_key, group_activities
from ai_search import parse_natural_query

app = Bottle()

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_PATH.insert(0, os.path.join(BASE_DIR, "views"))

# DB 연결
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
conn = db.get_conn()
db.init_db(conn)

# 동기화 상태
sync_state = {"running": False, "page": 0, "total_pages": 0, "fetched": 0, "error": None}


# --- 페이지 라우트 ---

@app.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    sync_stats = db.get_sync_stats(conn)
    return template("index",
                     regions=scraper.REGION_CODES,
                     categories=scraper.CATEGORY_CODES,
                     activity_types=scraper.ACTIVITY_TYPE_CODES,
                     targets=scraper.TARGET_CODES,
                     results=None,
                     groups=None,
                     total=0,
                     page=1,
                     filters={},
                     today=today,
                     end_date=end,
                     error=None,
                     sync_stats=sync_stats)


@app.route("/search")
def search_page():
    region = request.params.get("region", "")
    district = request.params.get("district", "")
    category = request.params.get("category", "")
    activity_type = request.params.get("activity_type", "")
    target = request.params.get("target", "")
    status = request.params.get("status", "0")
    date_start = request.params.get("date_start", "")
    date_end = request.params.get("date_end", "")
    keyword = request.params.get("keyword", "")
    page = int(request.params.get("page", "1"))

    filters = {
        "region": region, "district": district, "category": category,
        "activity_type": activity_type, "target": target, "status": status,
        "date_start": date_start, "date_end": date_end, "keyword": keyword,
    }

    # 코드값을 텍스트로 변환하여 DB 검색
    db_filters = {}
    if keyword:
        db_filters["keyword"] = keyword
    if category:
        db_filters["category"] = scraper.CATEGORY_CODES.get(category, category)
    if activity_type:
        db_filters["activity_type"] = scraper.ACTIVITY_TYPE_CODES.get(activity_type, activity_type)
    if target:
        db_filters["target"] = scraper.TARGET_CODES.get(target, target)
    if status == "0":
        db_filters["recruit_status"] = "모집중"
    elif status == "1":
        db_filters["recruit_status"] = "모집완료"
    if region:
        region_name = scraper.REGION_CODES.get(region, "")
        if region_name:
            db_filters["location"] = region_name
    if date_start:
        db_filters["date_start"] = date_start
    if date_end:
        db_filters["date_end"] = date_end

    error = None
    items = []
    total = 0
    groups = {}

    try:
        result = db.search_activities(conn, db_filters, page=page, per_page=10)
        items = result["items"]
        total = result["total"]
        groups = group_activities(items)
    except Exception as e:
        error = f"검색 중 오류가 발생했습니다: {e}"

    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    sync_stats = db.get_sync_stats(conn)

    return template("index",
                     regions=scraper.REGION_CODES,
                     categories=scraper.CATEGORY_CODES,
                     activity_types=scraper.ACTIVITY_TYPE_CODES,
                     targets=scraper.TARGET_CODES,
                     results=items,
                     groups=groups,
                     total=total,
                     page=page,
                     filters=filters,
                     today=today,
                     end_date=end,
                     error=error,
                     sync_stats=sync_stats)


@app.route("/activity/<program_id>")
def activity_detail(program_id):
    # DB에 없으면 빈 레코드 생성
    now = datetime.now().isoformat()
    db.ensure_activity_exists(conn, program_id, now)

    # 상세 정보를 아직 안 가져왔으면 API 호출
    activity = db.get_activity(conn, program_id)
    error = None
    if not activity.get("detail_fetched"):
        try:
            detail = scraper.fetch_detail(program_id)
            if detail:
                db.update_activity_detail(conn, detail)
                activity = db.get_activity(conn, program_id)
        except Exception as e:
            error = f"상세 정보 조회 중 오류: {e}"

    reviews = db.get_reviews(conn, program_id)
    stats = db.get_review_stats(conn, program_id)
    saved = db.is_saved(conn, program_id)
    related = db.get_grouped_activities(conn, activity["group_key"]) if activity.get("group_key") else []
    related = [r for r in related if r["program_id"] != program_id]

    return template("detail", activity=activity, reviews=reviews, stats=stats,
                     saved=saved, related=related, error=error)


@app.route("/saved")
def saved_page():
    activities = db.get_saved_activities(conn)
    return template("saved", activities=activities)


# --- API 라우트 ---

@app.post("/api/review")
def api_review():
    program_id = request.forms.get("program_id", "")
    rating = int(request.forms.get("rating", "3"))
    content = request.forms.get("content", "").strip()
    author = request.forms.get("author_name", "익명").strip()

    if not program_id or not content:
        response.status = 400
        return json.dumps({"error": "program_id와 content는 필수입니다."})

    db.add_review(conn, program_id, rating, content, author)
    redirect(f"/activity/{program_id}")


@app.post("/api/save/<program_id>")
def api_save(program_id):
    result = db.save_activity(conn, program_id)
    response.content_type = "application/json"
    return json.dumps({"saved": result})


@app.post("/api/ai-search")
def api_ai_search():
    query = request.forms.getunicode("query", "").strip()
    if not query:
        redirect("/")
        return

    print(f"[AI 검색] 쿼리: {query}")

    params, error = parse_natural_query(query)
    if error:
        print(f"[AI 검색] 오류: {error}")
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        sync_stats = db.get_sync_stats(conn)
        return template("index",
                         regions=scraper.REGION_CODES,
                         categories=scraper.CATEGORY_CODES,
                         activity_types=scraper.ACTIVITY_TYPE_CODES,
                         targets=scraper.TARGET_CODES,
                         results=None, groups=None, total=0, page=1,
                         filters={}, today=today, end_date=end,
                         error=f"AI 검색 오류: {error}",
                         sync_stats=sync_stats)

    # 날짜 기본값 추가
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    params.setdefault("date_start", today)
    params.setdefault("date_end", end)

    print(f"[AI 검색] 결과: {params}")

    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    redirect(f"/search?{qs}")


@app.post("/api/sync")
def api_sync():
    global sync_state
    print("[동기화] 요청 수신", flush=True)

    if sync_state["running"]:
        print("[동기화] 이미 진행 중 — 무시", flush=True)
        response.content_type = "application/json"
        return json.dumps({"error": "동기화가 이미 진행 중입니다."})

    # 필터 파라미터 수신
    filters = {
        "region": request.forms.get("region", ""),
        "district": request.forms.get("district", ""),
        "category": request.forms.get("category", ""),
        "activity_type": request.forms.get("activity_type", ""),
        "target": request.forms.get("target", ""),
        "status": request.forms.get("status", "0"),
        "date_start": request.forms.get("date_start", ""),
        "date_end": request.forms.get("date_end", ""),
        "keyword": request.forms.get("keyword", ""),
    }
    print(f"[동기화] 필터: {filters}", flush=True)

    sync_state = {"running": True, "page": 0, "total_pages": 0, "fetched": 0, "error": None}

    def run_sync():
        global sync_state
        sync_conn = db.get_conn()
        try:
            print("[동기화] 스레드 시작", flush=True)
            before_count = db.get_sync_stats(sync_conn)["count"]

            def on_progress(page, total_pages, fetched):
                sync_state["page"] = page
                sync_state["total_pages"] = total_pages
                sync_state["fetched"] = fetched
                print(f"[동기화] 페이지 {page}/{total_pages} ({fetched}건)", flush=True)

            result = scraper.sync_filtered(
                region=filters["region"],
                district=filters["district"],
                category=filters["category"],
                activity_type=filters["activity_type"],
                target=filters["target"],
                status=filters["status"],
                date_start=filters["date_start"],
                date_end=filters["date_end"],
                keyword=filters["keyword"],
                progress_callback=on_progress,
            )
            if result["items"]:
                db.upsert_activities(sync_conn, result["items"])

            after_count = db.get_sync_stats(sync_conn)["count"]
            new_count = after_count - before_count
            print(f"[동기화] 완료: API {len(result['items'])}건 중 신규 {new_count}건 추가 (DB 총 {after_count}건)", flush=True)
        except Exception as e:
            sync_state["error"] = str(e)
            import traceback
            print(f"[동기화] 오류: {e}", flush=True)
            traceback.print_exc()
        finally:
            sync_conn.close()
            sync_state["running"] = False

    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()
    print("[동기화] 스레드 시작됨 — 응답 반환", flush=True)

    response.content_type = "application/json"
    return json.dumps({"started": True})


@app.route("/api/sync-status")
def api_sync_status():
    response.content_type = "application/json"
    stats = db.get_sync_stats(conn)
    return json.dumps({
        "running": sync_state["running"],
        "page": sync_state["page"],
        "total_pages": sync_state["total_pages"],
        "fetched": sync_state["fetched"],
        "error": sync_state["error"],
        "db_count": stats["count"],
        "last_sync": stats["last_sync"],
    })


@app.route("/api/districts/<city_code>")
def api_districts(city_code):
    # 1365 포털에서 시군구 목록을 가져와 반환
    response.content_type = "application/json"
    try:
        districts = scraper.fetch_districts(city_code)
        return json.dumps(districts, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- 정적 파일 ---

@app.route("/static/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root=os.path.join(BASE_DIR, "static"))


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True, reloader=True, quiet=True)
