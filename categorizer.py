import re

# 제목에서 제거할 변동 패턴 (날짜, 회차, 시간대 등)
STRIP_PATTERNS = [
    r"\d+일차\s*",                     # "13일차 "
    r"\d+회차\s*",                     # "3회차 "
    r"제?\d+차\s*",                    # "제5차 ", "5차 "
    r"제?\d+기\s*",                    # "제3기 "
    r"\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2}\s*",  # "2026.02.11 " (날짜 전체를 먼저)
    r"\d{4}년?\s*",                    # "2026년 ", "2026 "
    r"\d{1,2}월\s*\d{0,2}일?\s*",     # "2월 ", "2월15일 "
    r"\(\d{1,2}[/월]\d{0,2}[일]?\)\s*",       # "(2/15)", "(2월15일)"
    r"\[\d{1,2}:\d{2}~?\d{0,2}:?\d{0,2}\]\s*", # "[09:00~13:00]", "[14:00~18:00]"
    r"\(\s*오전\s*\)\s*",              # "(오전)"
    r"\(\s*오후\s*\)\s*",              # "(오후)"
    r"오전\s*",                        # "오전 "
    r"오후\s*",                        # "오후 "
    r"^\d+\.\s*",                      # "3. " at start
    r"\s*-\s*\d+$",                    # "- 3" at end
]

_compiled = [re.compile(p) for p in STRIP_PATTERNS]


def compute_group_key(title):
    key = title.strip()
    for pattern in _compiled:
        key = pattern.sub("", key)
    key = re.sub(r"\s+", " ", key).strip()
    # 빈 문자열이 되면 원래 제목 사용
    return key if key else title.strip()


def group_activities(activities):
    groups = {}
    for act in activities:
        key = act.get("group_key") or compute_group_key(act.get("title", ""))
        groups.setdefault(key, []).append(act)
    return groups


if __name__ == "__main__":
    test_titles = [
        "13일차 유적지 봉사활동",
        "14일차 유적지 봉사활동",
        "2026년 설맞이 구로 직거래장터 행사장 운영 지원(오후)",
        "2026년 설맞이 구로 직거래장터 행사장 운영 지원(오전)",
        "청소년문화공유놀이터 이용 청소년 활동 보조 및 콘텐츠 관리[09:00~13:00]",
        "청소년문화공유놀이터 이용 청소년 활동 보조 및 콘텐츠 관리 [14:00~18:00]",
        "청소년문화공유놀이터 이용 청소년 활동 보조 및 콘텐츠 관리[12:00~15:00]",
        "제3기 환경정화 봉사",
        "제4기 환경정화 봉사",
        "2026.02.11 환경정화 활동",
        "2026.02.12 환경정화 활동",
    ]

    print("=== 그룹키 테스트 ===")
    for t in test_titles:
        key = compute_group_key(t)
        print(f"  {t}")
        print(f"    -> [{key}]")
        print()

    print("=== 그룹핑 테스트 ===")
    acts = [{"title": t, "group_key": compute_group_key(t)} for t in test_titles]
    groups = group_activities(acts)
    for key, items in groups.items():
        print(f"\n[{key}] ({len(items)}건)")
        for item in items:
            print(f"  - {item['title']}")
