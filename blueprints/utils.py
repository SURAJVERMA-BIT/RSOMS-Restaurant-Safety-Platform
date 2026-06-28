from datetime import date
from functools import wraps

from flask import redirect, url_for, flash, current_app
from flask_login import current_user


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])


def get_restaurant():
    from models import Restaurant
    return Restaurant.query.filter_by(owner_id=current_user.id).first()


def get_notifications(restaurant):
    from models import HygieneChecklist, StaffTraining
    notes = []
    if not restaurant:
        return notes

    status = restaurant.fssai_status
    days = restaurant.fssai_days_to_expiry
    if status == 'not_uploaded':
        notes.append({'type': 'warning', 'icon': 'fa-file-certificate',
                      'msg': 'FSSAI certificate not uploaded yet.'})
    elif status == 'expired':
        notes.append({'type': 'danger', 'icon': 'fa-exclamation-triangle',
                      'msg': f'FSSAI certificate EXPIRED {abs(days)} days ago!'})
    elif status == 'critical':
        notes.append({'type': 'danger', 'icon': 'fa-exclamation-triangle',
                      'msg': f'FSSAI certificate expires in {days} days!'})
    elif status == 'warning':
        notes.append({'type': 'warning', 'icon': 'fa-clock',
                      'msg': f'FSSAI certificate expires in {days} days.'})
    elif status == 'notice':
        notes.append({'type': 'info', 'icon': 'fa-info-circle',
                      'msg': f'FSSAI certificate expires in {days} days.'})

    today_checklist = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id, checklist_type='daily', date=date.today()
    ).first()
    if not today_checklist:
        notes.append({'type': 'warning', 'icon': 'fa-clipboard-list',
                      'msg': "Today's daily hygiene checklist not submitted."})

    expiring = StaffTraining.query.filter_by(
        restaurant_id=restaurant.id, status='expiring_soon'
    ).count()
    if expiring:
        notes.append({'type': 'info', 'icon': 'fa-user-graduate',
                      'msg': f'{expiring} staff training record(s) expiring soon.'})

    expired = StaffTraining.query.filter_by(
        restaurant_id=restaurant.id, status='expired'
    ).count()
    if expired:
        notes.append({'type': 'danger', 'icon': 'fa-user-times',
                      'msg': f'{expired} staff training record(s) EXPIRED.'})

    return notes


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def staff_or_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'staff'):
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
