from flask import Blueprint, render_template
from flask_login import login_required

from blueprints.utils import get_restaurant, get_notifications, staff_or_admin

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
@staff_or_admin
def index():
    restaurant = get_restaurant()
    notes = get_notifications(restaurant)
    return render_template('notifications.html', restaurant=restaurant, notifications=notes)
