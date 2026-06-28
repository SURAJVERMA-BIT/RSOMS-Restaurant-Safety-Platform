import json
import os
from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import HygieneChecklist, DAILY_TASKS, WEEKLY_TASKS
from forms import HygieneChecklistForm
from blueprints.utils import get_restaurant, get_notifications, allowed_file, staff_or_admin

hygiene_bp = Blueprint('hygiene', __name__)


@hygiene_bp.route('/hygiene')
@login_required
@staff_or_admin
def index():
    restaurant = get_restaurant()
    form = HygieneChecklistForm()
    today_daily = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id, checklist_type='daily', date=date.today()
    ).first()
    history = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id
    ).order_by(HygieneChecklist.date.desc(), HygieneChecklist.id.desc()).limit(20).all()
    notifications = get_notifications(restaurant)
    return render_template('hygiene_checklist.html',
                           restaurant=restaurant,
                           form=form,
                           daily_tasks=DAILY_TASKS,
                           weekly_tasks=WEEKLY_TASKS,
                           today_daily=today_daily,
                           history=history,
                           notifications=notifications)


@hygiene_bp.route('/hygiene/submit', methods=['POST'])
@login_required
@staff_or_admin
def submit():
    restaurant = get_restaurant()
    form = HygieneChecklistForm()
    ctype = request.form.get('checklist_type', 'daily')
    tasks_template = DAILY_TASKS if ctype == 'daily' else WEEKLY_TASKS
    tasks_result = {}
    completed = 0
    for task in tasks_template:
        checked = request.form.get(f'task_{task["key"]}') == 'on'
        tasks_result[task['key']] = checked
        if checked:
            completed += 1

    checklist = HygieneChecklist(
        restaurant_id=restaurant.id,
        staff_id=current_user.id,
        checklist_type=ctype,
        date=date.today(),
        tasks_json=json.dumps(tasks_result),
        completed_count=completed,
        total_count=len(tasks_template),
        notes=request.form.get('notes', '')
    )
    db.session.add(checklist)
    db.session.flush()

    if form.validate_on_submit():
        if form.kitchen_photo.data:
            f = form.kitchen_photo.data
            if allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'kitchen_{restaurant.id}_{checklist.id}.{ext}')
                f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                checklist.kitchen_photo = filename

        if form.restaurant_photo.data:
            f = form.restaurant_photo.data
            if allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'restaurant_{restaurant.id}_{checklist.id}.{ext}')
                f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                checklist.restaurant_photo = filename

    restaurant.calculate_and_update_score()
    db.session.commit()
    flash(f'{ctype.title()} checklist submitted! Score: {checklist.score_pct}%', 'success')
    return redirect(url_for('hygiene.index'))
