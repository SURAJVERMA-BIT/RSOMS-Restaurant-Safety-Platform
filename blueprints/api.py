from flask import Blueprint, jsonify
from flask_login import login_required

from extensions import db
from models import Order, MenuItem
from blueprints.utils import get_restaurant

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    restaurant = get_restaurant()
    if not restaurant:
        return jsonify({'error': 'No restaurant'}), 404
    restaurant.calculate_and_update_score()
    db.session.commit()
    return jsonify({
        'safety_score': restaurant.safety_score,
        'badge': restaurant.badge_status,
        'active_orders': Order.query.filter_by(
            restaurant_id=restaurant.id
        ).filter(Order.status.in_(['placed', 'preparing', 'ready'])).count(),
        'fssai_status': restaurant.fssai_status,
        'fssai_days': restaurant.fssai_days_to_expiry,
    })


@api_bp.route('/orders')
@login_required
def orders():
    restaurant = get_restaurant()
    active = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['placed', 'preparing', 'ready'])
    ).order_by(Order.created_at).all()
    return jsonify([{
        'id': o.id,
        'customer': o.customer_name,
        'table': o.table_number,
        'status': o.status,
        'total': o.total_amount,
        'time': o.created_at.strftime('%H:%M'),
    } for o in active])


@api_bp.route('/hygiene/score')
@login_required
def hygiene_score():
    restaurant = get_restaurant()
    restaurant.calculate_and_update_score()
    db.session.commit()
    return jsonify({'score': restaurant.safety_score, 'badge': restaurant.badge_status})


@api_bp.route('/menu')
@login_required
def menu():
    restaurant = get_restaurant()
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return jsonify([{
        'id': i.id, 'name': i.name, 'price': i.price,
        'category': i.category, 'available': i.available, 'is_veg': i.is_veg,
    } for i in items])
