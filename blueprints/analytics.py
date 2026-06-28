import json

from flask import Blueprint, render_template
from flask_login import login_required

from models import HygieneChecklist, Order
from blueprints.utils import get_restaurant, get_notifications, admin_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics')
@login_required
@admin_required
def index():
    restaurant = get_restaurant()

    checklists_all = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id, checklist_type='daily'
    ).order_by(HygieneChecklist.date).all()
    score_labels = [str(c.date) for c in checklists_all]
    score_data = [c.score_pct for c in checklists_all]

    orders_all = Order.query.filter_by(restaurant_id=restaurant.id).all()
    status_counts = {'placed': 0, 'preparing': 0, 'ready': 0, 'served': 0}
    for o in orders_all:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    monthly_revenue = {}
    for o in orders_all:
        if o.payment_status == 'paid':
            key = o.created_at.strftime('%b %Y')
            monthly_revenue[key] = monthly_revenue.get(key, 0) + o.total_amount
    rev_labels = list(monthly_revenue.keys())
    rev_data = [round(v, 2) for v in monthly_revenue.values()]

    category_counts = {}
    for item in restaurant.menu_items:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1

    notifications = get_notifications(restaurant)
    return render_template('analytics.html',
                           restaurant=restaurant,
                           score_labels=json.dumps(score_labels),
                           score_data=json.dumps(score_data),
                           status_counts=json.dumps(list(status_counts.values())),
                           status_labels=json.dumps(list(status_counts.keys())),
                           rev_labels=json.dumps(rev_labels),
                           rev_data=json.dumps(rev_data),
                           cat_labels=json.dumps(list(category_counts.keys())),
                           cat_data=json.dumps(list(category_counts.values())),
                           notifications=notifications)
