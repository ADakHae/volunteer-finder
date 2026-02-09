% rebase('base.tpl', page_title=activity['title'] if activity else '활동 상세', nav='search')

% if error:
<div class="error-msg">{{error}}</div>
% end

% if activity:
<section class="detail-section">
    <div class="detail-header">
        <div class="detail-badges">
            <span class="badge badge-status {{'badge-open' if activity['recruit_status'] == '모집중' else 'badge-closed'}}">{{activity['recruit_status']}}</span>
            <span class="badge badge-type">{{activity['activity_type']}}</span>
            <span class="badge badge-category">{{activity['category']}}</span>
        </div>
        <h2>{{activity['title']}}</h2>
        <button class="btn btn-save" id="saveBtn" data-id="{{activity['program_id']}}" data-saved="{{'1' if saved else '0'}}">
            {{'저장됨' if saved else '저장하기'}}
        </button>
    </div>

    <div class="detail-info">
        <table class="info-table">
            <tr><th>봉사기간</th><td>{{activity['period_start']}} ~ {{activity['period_end']}}</td></tr>
            <tr><th>봉사시간</th><td>{{activity['volunteer_time']}}</td></tr>
            <tr><th>인정시간</th><td>{{activity['recognized_hours']}}</td></tr>
            <tr><th>모집기간</th><td>{{activity['recruit_start']}} ~ {{activity['recruit_end']}}</td></tr>
            % if activity.get('active_days'):
            <tr><th>활동요일</th><td>{{activity['active_days']}}</td></tr>
            % end
            % if activity.get('recruit_count'):
            <tr><th>모집인원</th><td>{{activity['recruit_count']}}</td></tr>
            % end
            % if activity.get('apply_count'):
            <tr><th>신청인원</th><td>{{activity['apply_count']}}</td></tr>
            % end
            <tr><th>봉사장소</th><td>{{activity['location']}}</td></tr>
            <tr><th>활동기관</th><td>{{activity['organization']}}</td></tr>
            % if activity.get('register_org'):
            <tr><th>등록기관</th><td>{{activity['register_org']}}</td></tr>
            % end
            <tr><th>분야</th><td>{{activity['category']}}</td></tr>
            % if activity.get('target'):
            <tr><th>봉사대상</th><td>{{activity['target']}}</td></tr>
            % end
            % if activity.get('volunteer_type'):
            <tr><th>봉사자유형</th><td>{{activity['volunteer_type']}}</td></tr>
            % end
        </table>
    </div>

    % if activity.get('description'):
    <div class="detail-description">
        <h3>활동 상세</h3>
        <div class="description-content">{{activity['description']}}</div>
    </div>
    % end

    % if related:
    <div class="related-section">
        <h3>같은 그룹의 활동 ({{len(related)}}건)</h3>
        <div class="related-list">
            % for r in related:
            <a href="/activity/{{r['program_id']}}" class="related-card">
                <span class="badge badge-status {{'badge-open' if r['recruit_status'] == '모집중' else 'badge-closed'}}">{{r['recruit_status']}}</span>
                <span>{{r['title']}}</span>
                <span class="related-period">{{r['period_start']}} ~ {{r['period_end']}}</span>
            </a>
            % end
        </div>
    </div>
    % end

    <div class="reviews-section">
        <h3>리뷰
            % if stats and stats['count'] > 0:
                <span class="review-stats">({{stats['count']}}개, 평균 {{stats['avg_rating']}}점)</span>
            % end
        </h3>

        <form action="/api/review" method="post" class="review-form">
            <input type="hidden" name="program_id" value="{{activity['program_id']}}">
            <div class="form-row">
                <label for="author_name">이름</label>
                <input type="text" id="author_name" name="author_name" placeholder="익명" maxlength="30">
            </div>
            <div class="form-row">
                <label for="rating">평점</label>
                <div class="rating-input" id="ratingInput">
                    % for i in range(1, 6):
                    <label class="star-label">
                        <input type="radio" name="rating" value="{{i}}" {{'checked' if i == 3 else ''}}>
                        <span class="star">{{i}}</span>
                    </label>
                    % end
                </div>
            </div>
            <div class="form-row">
                <label for="content">내용</label>
                <textarea id="content" name="content" rows="3" required placeholder="봉사활동 후기를 남겨주세요"></textarea>
            </div>
            <button type="submit" class="btn btn-primary">리뷰 작성</button>
        </form>

        % if reviews:
        <div class="review-list">
            % for review in reviews:
            <div class="review-card">
                <div class="review-header">
                    <span class="review-author">{{review['author_name']}}</span>
                    <span class="review-rating">{{'★' * review['rating']}}{{'☆' * (5 - review['rating'])}}</span>
                    <span class="review-date">{{review['created_at']}}</span>
                </div>
                <p class="review-content">{{review['content']}}</p>
            </div>
            % end
        </div>
        % else:
        <p class="empty-state">아직 리뷰가 없습니다.</p>
        % end
    </div>
</section>
% end
