import os
import json
import urllib.parse
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


# --- 페이지 라우트 ---

@app.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
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
                     error=None)


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

    error = None
    items = []
    total = 0
    groups = {}

    try:
        result = scraper.search(
            region=region, district=district, category=category,
            activity_type=activity_type, target=target, status=status,
            date_start=date_start, date_end=date_end,
            keyword=keyword, page=page
        )
        items = result["items"]
        total = result["total"]

        # group_key 계산 및 fetched_at 추가
        now = datetime.now().isoformat()
        for item in items:
            item["group_key"] = compute_group_key(item["title"])
            item["fetched_at"] = now

        # DB에 캐시
        if items:
            db.upsert_activities(conn, items)

        groups = group_activities(items)

    except Exception as e:
        error = f"검색 중 오류가 발생했습니다: {e}"

    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

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
                     error=error)


@app.route("/activity/<program_id>")
def activity_detail(program_id):
    activity = db.get_activity(conn, program_id)
    if not activity:
        return template("detail", activity=None, reviews=[], stats=None, saved=False,
                         related=[], error="활동 정보를 찾을 수 없습니다.")

    reviews = db.get_reviews(conn, program_id)
    stats = db.get_review_stats(conn, program_id)
    saved = db.is_saved(conn, program_id)
    related = db.get_grouped_activities(conn, activity["group_key"]) if activity.get("group_key") else []
    # 자기 자신 제외
    related = [r for r in related if r["program_id"] != program_id]

    return template("detail", activity=activity, reviews=reviews, stats=stats,
                     saved=saved, related=related, error=None)


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
        return template("index",
                         regions=scraper.REGION_CODES,
                         categories=scraper.CATEGORY_CODES,
                         activity_types=scraper.ACTIVITY_TYPE_CODES,
                         targets=scraper.TARGET_CODES,
                         results=None, groups=None, total=0, page=1,
                         filters={}, today=today, end_date=end,
                         error=f"AI 검색 오류: {error}")

    # 날짜 기본값 추가
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    params.setdefault("date_start", today)
    params.setdefault("date_end", end)

    print(f"[AI 검색] 결과: {params}")

    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    redirect(f"/search?{qs}")


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
