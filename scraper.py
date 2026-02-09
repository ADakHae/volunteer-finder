import urllib.request
import urllib.parse
import re
import ssl
from bs4 import BeautifulSoup

API_URL = "https://www.1365.go.kr/vols/1572247904127/partcptn/timeCptn.do"
DISTRICT_URL = "https://www.1365.go.kr/vols/P9210/mber/volsMberJson.do"

REGION_CODES = {
    "6110000": "서울특별시",
    "6260000": "부산광역시",
    "6270000": "대구광역시",
    "6280000": "인천광역시",
    "6290000": "광주광역시",
    "6300000": "대전광역시",
    "6310000": "울산광역시",
    "5690000": "세종특별자치시",
    "6410000": "경기도",
    "6420000": "강원특별자치도",
    "6430000": "충청북도",
    "6440000": "충청남도",
    "6450000": "전북특별자치도",
    "6460000": "전라남도",
    "6470000": "경상북도",
    "6480000": "경상남도",
    "6500000": "제주특별자치도",
}

CATEGORY_CODES = {
    "0100": "생활편의",
    "0200": "주거환경",
    "0300": "상담·멘토링",
    "0400": "교육",
    "0500": "보건·의료",
    "0700": "문화·체육·예술·관광",
    "0800": "환경·생태계보호",
    "0900": "사무행정",
    "1000": "지역안전·보호",
    "1100": "인권·공익",
    "1200": "재난·재해",
    "1300": "국제협력·해외봉사",
    "1500": "기타",
    "1700": "자원봉사 기본교육",
}

ACTIVITY_TYPE_CODES = {
    "1": "온라인",
    "2": "오프라인",
    "3": "온라인+오프라인",
}

TARGET_CODES = {
    "1": "아동·청소년",
    "2": "장애인",
    "3": "노인",
    "4": "쪽방촌",
    "5": "다문화가정",
    "6": "여성",
    "7": "환경",
    "8": "사회적기업",
    "9": "고향봉사",
    "99": "기타",
}


def fetch_page(params):
    data = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        return resp.read().decode("utf-8")


def build_params(region="", district="", category="", activity_type="",
                 target="", status="0", date_start="", date_end="",
                 keyword="", page=1):
    params = {
        "cPage": str(page),
        "searchFlag": "search",
        "searchHopeArea1": region,
        "searchHopeArea2": district,
        "searchSrvcStts": status,
        "searchProgrmBgnde": date_start,
        "searchProgrmEndde": date_end,
        "adultPosblAt": "Y",
        "yngbgsPosblAt": "Y",
    }
    if category:
        params["searchHopeSrvc1"] = category
    if activity_type:
        params["searchActOnline"] = activity_type
    if target:
        params["searchSrvcTarget"] = target
    if keyword:
        params["searchKeyword"] = keyword
    return params


def parse_total_count(html):
    match = re.search(r'전체\s*<em>([\d,]+)</em>\s*건', html)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def parse_activities(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    list_wrap = soup.select_one("ul.list_wrap.wrap2")
    if not list_wrap:
        return results

    for li in list_wrap.find_all("li", recursive=False):
        item = {}

        # 프로그램 ID
        hidden = li.find("input", {"name": "progrmRegistNo"})
        if not hidden:
            continue
        item["program_id"] = hidden.get("value", "")

        # 분야 뱃지 (시간인증, 온/오프라인, 분야명)
        badges = []
        badge_ul = li.select_one("div.ing.blue ul")
        if badge_ul:
            badges = [b.get_text(strip=True) for b in badge_ul.find_all("li")]

        # 활동구분 파싱
        activity_type = ""
        for b in badges:
            if "온라인" in b and "오프라인" in b:
                activity_type = "온라인+오프라인"
                break
            elif "오프라인" in b:
                activity_type = "오프라인"
                break
            elif "온라인" in b:
                activity_type = "온라인"
                break
        item["activity_type"] = activity_type

        # 분야 (시간인증, 온라인/오프라인 제외한 나머지)
        skip = {"시간인증", "온라인", "오프라인", "온라인+오프라인"}
        category_badges = [b for b in badges if b not in skip]
        item["category"] = category_badges[0] if category_badges else ""

        # 제목
        title_div = li.select_one("div.tit_board_list")
        item["title"] = title_div.get_text(strip=True) if title_div else ""

        # 위치, 기관
        loc_div = li.select_one("div.vols-location")
        if loc_div:
            spans = loc_div.find_all("span")
            item["location"] = spans[0].get_text(strip=True) if len(spans) > 0 else ""
            item["organization"] = spans[1].get_text(strip=True) if len(spans) > 1 else ""
        else:
            item["location"] = ""
            item["organization"] = ""

        # 모집상태
        status_div = li.select_one("div.close_dDay div.end")
        item["recruit_status"] = status_div.get_text(strip=True) if status_div else ""

        # PC용 상세정보 영역에서 기간/시간 파싱 (모바일 중복 무시)
        pc_section = li.select_one("div.txts_pc_ver")
        item["period_start"] = ""
        item["period_end"] = ""
        item["volunteer_time"] = ""
        item["recruit_start"] = ""
        item["recruit_end"] = ""
        item["recognized_hours"] = ""

        if pc_section:
            for div in pc_section.find_all("div", recursive=True):
                p = div.find("p")
                span = div.find("span")
                if not p or not span:
                    continue
                label = p.get_text(strip=True)
                value = span.get_text(strip=True)

                if label == "봉사기간":
                    dates = re.findall(r"(\d{4}\.\d{2}\.\d{2})", value)
                    if len(dates) >= 2:
                        item["period_start"] = dates[0].replace(".", "-")
                        item["period_end"] = dates[1].replace(".", "-")
                elif label == "봉사시간":
                    item["volunteer_time"] = re.sub(r"\s+", " ", value)
                elif label == "모집기간":
                    dates = re.findall(r"(\d{4}\.\d{2}\.\d{2})", value)
                    if len(dates) >= 2:
                        item["recruit_start"] = dates[0].replace(".", "-")
                        item["recruit_end"] = dates[1].replace(".", "-")
                elif label == "인정시간":
                    item["recognized_hours"] = value

        results.append(item)

    return results


def fetch_districts(city_code):
    import json as _json
    data = urllib.parse.urlencode({
        "type": "hopeAreaList",
        "upper": city_code,
        "engnSe": "4",
    }).encode("utf-8")
    req = urllib.request.Request(DISTRICT_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        result = _json.loads(resp.read().decode("utf-8"))
    return {item["code"]: item["codeNm"] for item in result.get("list", [])}


def fetch_detail(program_id):
    """상세 페이지 HTML을 가져와 파싱한다."""
    url = API_URL + "?" + urllib.parse.urlencode({
        "type": "show",
        "progrmRegistNo": program_id,
    })
    params = {
        "cPage": "1",
        "actType": "A01",
        "searchSrvcStts": "0",
        "adultPosblAt": "Y",
        "yngbgsPosblAt": "Y",
        "searchFlag": "search",
        "progrmRegistNo": program_id,
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        html = resp.read().decode("utf-8")
    return parse_detail(html, program_id)


def parse_detail(html, program_id):
    """상세 페이지 HTML에서 봉사활동 정보를 추출한다."""
    soup = BeautifulSoup(html, "html.parser")

    board_view = soup.select_one("div.board_view")
    if not board_view:
        return None

    item = {"program_id": program_id}

    # 제목 + 모집상태
    tit = board_view.select_one("h3.tit_board_view")
    if tit:
        full = tit.get_text(strip=True)
        m = re.search(r"\(([^)]+)\)\s*$", full)
        if m:
            item["recruit_status"] = m.group(1)
            item["title"] = full[:m.start()].strip()
        else:
            item["title"] = full
            item["recruit_status"] = ""
    else:
        item["title"] = ""
        item["recruit_status"] = ""

    # dl > dt + dd 쌍 파싱
    data_show = board_view.select_one("div.board_data_show")
    fields = {}
    if data_show:
        for dl in data_show.select("dl"):
            dt = dl.find("dt")
            dd = dl.find("dd")
            if dt and dd:
                fields[dt.get_text(strip=True)] = dd

    # 봉사기간
    period_dd = fields.get("봉사기간")
    if period_dd:
        dates = re.findall(r"(\d{4}\.\d{2}\.\d{2})", period_dd.get_text())
        item["period_start"] = dates[0].replace(".", "-") if len(dates) >= 1 else ""
        item["period_end"] = dates[1].replace(".", "-") if len(dates) >= 2 else ""
    else:
        item["period_start"] = ""
        item["period_end"] = ""

    # 봉사시간
    time_dd = fields.get("봉사시간")
    item["volunteer_time"] = re.sub(r"\s+", " ", time_dd.get_text(strip=True)) if time_dd else ""

    # 모집기간
    recruit_dd = fields.get("모집기간")
    if recruit_dd:
        dates = re.findall(r"(\d{4}\.\d{2}\.\d{2})", recruit_dd.get_text())
        item["recruit_start"] = dates[0].replace(".", "-") if len(dates) >= 1 else ""
        item["recruit_end"] = dates[1].replace(".", "-") if len(dates) >= 2 else ""
    else:
        item["recruit_start"] = ""
        item["recruit_end"] = ""

    # 단순 텍스트 필드들
    for key, label in [
        ("active_days", "활동요일"),
        ("recruit_count", "모집인원"),
        ("apply_count", "신청인원"),
        ("category", "봉사분야"),
        ("volunteer_type", "봉사자유형"),
        ("target", "봉사대상"),
        ("activity_type", "활동구분"),
    ]:
        dd = fields.get(label)
        item[key] = re.sub(r"\s+", " ", dd.get_text(strip=True)) if dd else ""

    # 모집기관 (span.text-l 에 이름)
    org_dd = fields.get("모집기관")
    if org_dd:
        span = org_dd.select_one("span.text-l")
        item["organization"] = span.get_text(strip=True) if span else org_dd.get_text(strip=True)
    else:
        item["organization"] = ""

    # 등록기관
    reg_dd = fields.get("등록기관")
    item["register_org"] = reg_dd.get_text(strip=True) if reg_dd else ""

    # 봉사장소
    place_dd = fields.get("봉사장소")
    item["location"] = place_dd.get_text(strip=True) if place_dd else ""

    # 인정시간 (봉사시간 텍스트에서 추출)
    hours_match = re.search(r"최대\s*(\d+)시간\s*인정", item.get("volunteer_time", ""))
    item["recognized_hours"] = f"{hours_match.group(1)}시간" if hours_match else ""

    # 활동 설명
    board_body = board_view.select_one("div.board_body")
    item["description"] = board_body.get_text(strip=True) if board_body else ""

    return item


def search(region="", district="", category="", activity_type="",
           target="", status="0", date_start="", date_end="",
           keyword="", page=1):
    params = build_params(region, district, category, activity_type,
                          target, status, date_start, date_end, keyword, page)
    html = fetch_page(params)
    total = parse_total_count(html)
    activities = parse_activities(html)
    return {"items": activities, "total": total, "page": page}


if __name__ == "__main__":
    import json
    result = search(region="6110000", district="3160000", category="0700",
                    date_start="2026-02-09", date_end="2026-05-09")
    print(f"총 {result['total']}건")
    for act in result["items"]:
        print(f"\n[{act['recruit_status']}] {act['title']}")
        print(f"  위치: {act['location']} | 기관: {act['organization']}")
        print(f"  분야: {act['category']} | 구분: {act['activity_type']}")
        print(f"  봉사기간: {act['period_start']} ~ {act['period_end']}")
        print(f"  봉사시간: {act['volunteer_time']}")
        print(f"  인정시간: {act['recognized_hours']}")
