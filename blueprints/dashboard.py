import json
from datetime import date

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from extensions import db
from models import Order, MenuItem, HygieneChecklist, StaffTraining
from blueprints.utils import get_restaurant, get_notifications

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'consumer':
        return redirect(url_for('public.index'))

    restaurant = get_restaurant()
    notifications = []
    stats = {}
    recent_orders = []
    score_history = []
    today_checklist = None

    if restaurant:
        notifications = get_notifications(restaurant)
        restaurant.calculate_and_update_score()
        db.session.commit()

        total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
        today_orders = Order.query.filter_by(restaurant_id=restaurant.id).filter(
            db.func.date(Order.created_at) == date.today()
        ).count()
        active_orders = Order.query.filter_by(
            restaurant_id=restaurant.id
        ).filter(Order.status.in_(['placed', 'preparing', 'ready'])).count()
        total_revenue = db.session.query(
            db.func.sum(Order.total_amount)
        ).filter_by(restaurant_id=restaurant.id, payment_status='paid').scalar() or 0

        stats = {
            'total_orders': total_orders,
            'today_orders': today_orders,
            'active_orders': active_orders,
            'total_revenue': round(total_revenue, 2),
            'menu_count': MenuItem.query.filter_by(restaurant_id=restaurant.id).count(),
            'staff_count': StaffTraining.query.filter_by(restaurant_id=restaurant.id).count(),
            'safety_score': restaurant.safety_score,
            'badge': restaurant.badge_status,
            'avg_rating': restaurant.average_rating,
            'feedback_count': len(restaurant.feedback_list),
        }

        recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(
            Order.created_at.desc()
        ).limit(5).all()

        checklists = HygieneChecklist.query.filter_by(
            restaurant_id=restaurant.id, checklist_type='daily'
        ).order_by(HygieneChecklist.date.desc()).limit(7).all()
        score_history = [
            {'date': str(c.date), 'score': c.score_pct} for c in reversed(checklists)
        ]

        today_checklist = HygieneChecklist.query.filter_by(
            restaurant_id=restaurant.id, checklist_type='daily', date=date.today()
        ).first()

    return render_template('dashboard.html',
                           restaurant=restaurant,
                           notifications=notifications,
                           stats=stats,
                           recent_orders=recent_orders,
                           score_history=json.dumps(score_history),
                           today_checklist=today_checklist)
