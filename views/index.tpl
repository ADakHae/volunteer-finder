% rebase('base.tpl', page_title='봉사활동 찾기', nav='search')

<section class="ai-search-section">
    <form action="/api/ai-search" method="post" class="ai-search-form">
        <label for="ai-query">AI 추천 검색</label>
        <div class="ai-search-row">
            <input type="text" id="ai-query" name="query"
                   placeholder="예: 서울에서 주말에 할 수 있는 환경 봉사">
            <button type="submit" class="btn btn-ai">AI 검색</button>
        </div>
    </form>
</section>

<section class="search-section">
    <form action="/search" method="get" class="filter-form">
        <div class="filter-grid">
            <div class="filter-group">
                <label for="region">시/도</label>
                <select id="region" name="region">
                    <option value="">전체</option>
                    % for code, name in regions.items():
                        <option value="{{code}}" {{'selected' if filters.get('region') == code else ''}}>{{name}}</option>
                    % end
                </select>
            </div>

            <div class="filter-group">
                <label for="district">시/군/구</label>
                <select id="district" name="district" data-selected="{{filters.get('district', '')}}">
                    <option value="">전체</option>
                </select>
            </div>

            <div class="filter-group">
                <label for="category">봉사분야</label>
                <select id="category" name="category">
                    <option value="">전체</option>
                    % for code, name in categories.items():
                        <option value="{{code}}" {{'selected' if filters.get('category') == code else ''}}>{{name}}</option>
                    % end
                </select>
            </div>

            <div class="filter-group">
                <label for="activity_type">활동구분</label>
                <select id="activity_type" name="activity_type">
                    <option value="">전체</option>
                    % for code, name in activity_types.items():
                        <option value="{{code}}" {{'selected' if filters.get('activity_type') == code else ''}}>{{name}}</option>
                    % end
                </select>
            </div>

            <div class="filter-group">
                <label for="target">봉사대상</label>
                <select id="target" name="target">
                    <option value="">전체</option>
                    % for code, name in targets.items():
                        <option value="{{code}}" {{'selected' if filters.get('target') == code else ''}}>{{name}}</option>
                    % end
                </select>
            </div>

            <div class="filter-group">
                <label for="status">모집상태</label>
                <select id="status" name="status">
                    <option value="0" {{'selected' if filters.get('status', '0') == '0' else ''}}>모집중</option>
                    <option value="1" {{'selected' if filters.get('status') == '1' else ''}}>모집완료</option>
                    <option value="3" {{'selected' if filters.get('status') == '3' else ''}}>전체</option>
                </select>
            </div>

            <div class="filter-group">
                <label for="date_start">시작일</label>
                <input type="date" id="date_start" name="date_start"
                       value="{{filters.get('date_start', today)}}">
            </div>

            <div class="filter-group">
                <label for="date_end">종료일</label>
                <input type="date" id="date_end" name="date_end"
                       value="{{filters.get('date_end', end_date)}}">
            </div>

            <div class="filter-group">
                <label for="keyword">검색어</label>
                <input type="text" id="keyword" name="keyword"
                       value="{{filters.get('keyword', '')}}" placeholder="봉사활동명">
            </div>
        </div>

        <div class="filter-actions">
            <button type="submit" class="btn btn-primary">검색</button>
            <a href="/" class="btn btn-secondary">초기화</a>
        </div>
    </form>
</section>

% if error:
<div class="error-msg">{{error}}</div>
% end

% if results is not None:
<section class="results-section">
    <div class="results-header">
        <span class="results-count">검색결과 <strong>{{total}}</strong>건</span>
    </div>

    % if groups:
        % for group_key, items in groups.items():
            % if len(items) > 1:
            <div class="group-card">
                <div class="group-header">
                    <span class="group-badge">{{len(items)}}건 묶음</span>
                    <span class="group-title">{{group_key}}</span>
                </div>
                <div class="group-items">
                    % for act in items:
                        <a href="/activity/{{act['program_id']}}" class="activity-card">
                            <div class="card-badges">
                                <span class="badge badge-status {{'badge-open' if act['recruit_status'] == '모집중' else 'badge-closed'}}">{{act['recruit_status']}}</span>
                                <span class="badge badge-type">{{act['activity_type']}}</span>
                                <span class="badge badge-category">{{act['category']}}</span>
                            </div>
                            <h3 class="card-title">{{act['title']}}</h3>
                            <div class="card-meta">
                                <span>{{act['location']}}</span>
                                <span>{{act['organization']}}</span>
                            </div>
                            <div class="card-info">
                                <span>{{act['period_start']}} ~ {{act['period_end']}}</span>
                                <span>{{act['recognized_hours']}}</span>
                            </div>
                        </a>
                    % end
                </div>
            </div>
            % else:
                % act = items[0]
                <a href="/activity/{{act['program_id']}}" class="activity-card">
                    <div class="card-badges">
                        <span class="badge badge-status {{'badge-open' if act['recruit_status'] == '모집중' else 'badge-closed'}}">{{act['recruit_status']}}</span>
                        <span class="badge badge-type">{{act['activity_type']}}</span>
                        <span class="badge badge-category">{{act['category']}}</span>
                    </div>
                    <h3 class="card-title">{{act['title']}}</h3>
                    <div class="card-meta">
                        <span>{{act['location']}}</span>
                        <span>{{act['organization']}}</span>
                    </div>
                    <div class="card-info">
                        <span>{{act['period_start']}} ~ {{act['period_end']}}</span>
                        <span>{{act['recognized_hours']}}</span>
                    </div>
                </a>
            % end
        % end
    % elif results is not None and len(results) == 0:
        <div class="empty-state">검색 결과가 없습니다.</div>
    % end

    % if total > 10:
    <div class="pagination">
        % pages = (total + 9) // 10
        % current = page
        % import urllib.parse as _up
        <%
        base_params = {k: v for k, v in filters.items() if v}
        %>
        % for p in range(1, min(pages + 1, 20)):
            <%
            base_params['page'] = str(p)
            qs = _up.urlencode(base_params)
            %>
            % if p == current:
                <span class="page-btn active">{{p}}</span>
            % else:
                <a href="/search?{{qs}}" class="page-btn">{{p}}</a>
            % end
        % end
    </div>
    % end
</section>
% end
