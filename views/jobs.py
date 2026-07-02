from flask import Blueprint, render_template, request, current_app, flash
from flask_login import login_required, current_user
from models import JobRun, Schedule
from extensions import db
from utils import format_datetime

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/')
@login_required
def history():
    search = request.args.get('search', '').strip()
    query = JobRun.query

    if not current_user.is_admin:
        query = query.join(Schedule, JobRun.schedule_id == Schedule.id)
        query = query.filter(
            db.or_(
                Schedule.created_by == current_user.id,
                Schedule.viewers.any(id=current_user.id)
            )
        )

    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                JobRun.run_number.ilike(like),
                JobRun.job_name.ilike(like),
                JobRun.status.ilike(like)
            )
        )

    if request.args.get('status'):
        query = query.filter(JobRun.status == request.args['status'])

    sort = request.args.get('sort', 'started_at')
    direction = request.args.get('direction', 'desc')
    sort_col = getattr(JobRun, sort, JobRun.started_at)
    if direction == 'desc':
        sort_col = sort_col.desc()
    query = query.order_by(sort_col)

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=25, error_out=False)
    return render_template('jobs/history.html',
        pagination=pagination, runs=pagination.items,
        format_datetime=format_datetime, sort=sort, direction=direction,
        search=search, is_admin=current_user.is_admin)
