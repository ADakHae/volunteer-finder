% rebase('base.tpl', page_title='저장된 활동', nav='saved')

<section class="saved-section">
    <h2>저장된 활동</h2>

    % if activities:
    <div class="saved-list">
        % for act in activities:
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
            <div class="card-saved-at">저장일: {{act['saved_at']}}</div>
        </a>
        % end
    </div>
    % else:
    <div class="empty-state">저장된 활동이 없습니다.</div>
    % end
</section>
