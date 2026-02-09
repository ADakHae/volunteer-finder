<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{get('page_title', '봉사활동 찾기')}}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <div class="header-inner">
            <h1><a href="/">봉사활동 찾기</a></h1>
            <nav>
                <a href="/" class="{{'active' if get('nav', '') == 'search' else ''}}">검색</a>
                <a href="/saved" class="{{'active' if get('nav', '') == 'saved' else ''}}">저장됨</a>
            </nav>
        </div>
    </header>
    <main>
        {{!base}}
    </main>
    <script src="/static/main.js"></script>
</body>
</html>
