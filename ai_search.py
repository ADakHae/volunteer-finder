import subprocess
import json
import glob
import os

CLAUDE_BINARY_PATTERN = os.path.expanduser(
    "~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude"
)

SYSTEM_PROMPT = """너는 1365 자원봉사포털 검색 파라미터 변환기야.
사용자의 자연어 입력을 아래 코드 매핑에 맞춰 JSON으로 변환해.
반드시 코드값(숫자)을 반환해야 해. 이름이 아닌 코드를 반환해.
해당 없는 필드는 빈 문자열("")로.

[지역코드]
서울=6110000, 부산=6260000, 대구=6270000, 인천=6280000, 광주=6290000,
대전=6300000, 울산=6310000, 세종=5690000, 경기=6410000, 강원=6420000,
충북=6430000, 충남=6440000, 전북=6450000, 전남=6460000, 경북=6470000,
경남=6480000, 제주=6500000

[봉사분야코드]
생활편의=0100, 주거환경=0200, 상담/멘토링=0300, 교육=0400, 보건/의료=0500,
문화/체육/예술/관광=0700, 환경/생태계보호=0800, 사무행정=0900,
지역안전/보호=1000, 인권/공익=1100, 재난/재해=1200, 국제협력/해외봉사=1300,
기타=1500, 자원봉사기본교육=1700

[활동구분코드]
온라인=1, 오프라인=2, 온라인+오프라인=3

[봉사대상코드]
아동/청소년=1, 장애인=2, 노인=3, 쪽방촌=4, 다문화가정=5, 여성=6,
환경=7, 사회적기업=8, 고향봉사=9, 기타=99

[모집상태코드]
모집중=0, 모집완료=1, 전체=3
기본값은 모집중(0)으로 해.

[keyword]
지역/분야/대상/활동구분/모집상태에 해당하지 않는 구체적 검색어가 있으면 keyword에 넣어."""

JSON_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "region": {"type": "string", "description": "지역코드 숫자 (예: 6110000). 없으면 빈 문자열"},
        "district": {"type": "string", "description": "시군구코드. 보통 빈 문자열"},
        "category": {"type": "string", "description": "봉사분야코드 (예: 0800). 없으면 빈 문자열"},
        "activity_type": {"type": "string", "description": "1,2,3 중 하나. 없으면 빈 문자열"},
        "target": {"type": "string", "description": "봉사대상코드. 없으면 빈 문자열"},
        "status": {"type": "string", "description": "0=모집중,1=모집완료,3=전체. 기본 0"},
        "keyword": {"type": "string", "description": "추가 검색 키워드. 없으면 빈 문자열"},
    },
    "required": ["region", "category", "status", "keyword", "activity_type", "target", "district"],
})


def find_claude_binary():
    matches = sorted(glob.glob(CLAUDE_BINARY_PATTERN), reverse=True)
    if matches:
        return matches[0]
    return None


def parse_natural_query(query):
    claude_bin = find_claude_binary()
    if not claude_bin:
        return None, "Claude CLI를 찾을 수 없습니다."

    cmd = [
        claude_bin,
        "-p",
        "--model", "haiku",
        "--output-format", "json",
        "--json-schema", JSON_SCHEMA,
        "--append-system-prompt", SYSTEM_PROMPT,
        "--no-session-persistence",
        "--dangerously-skip-permissions",
    ]

    try:
        result = subprocess.run(
            cmd,
            input=query,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return None, f"Claude CLI 오류: {result.stderr[:200]}"

        data = json.loads(result.stdout)
        params = data.get("structured_output")
        if not params:
            return None, "AI가 검색 파라미터를 생성하지 못했습니다."

        return params, None

    except subprocess.TimeoutExpired:
        return None, "AI 응답 시간이 초과되었습니다."
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"AI 응답 파싱 오류: {e}"


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "서울에서 주말에 할 수 있는 환경 봉사"
    print(f"쿼리: {query}")
    params, error = parse_natural_query(query)
    if error:
        print(f"오류: {error}")
    else:
        print(f"파라미터: {json.dumps(params, ensure_ascii=False, indent=2)}")
