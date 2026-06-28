from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import Order, OrderItem, MenuItem
from forms import OrderForm
from blueprints.utils import get_restaurant, get_notifications, staff_or_admin

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders')
@login_required
@staff_or_admin
def index():
    restaurant = get_restaurant()
    if not restaurant and current_user.role == 'staff':
        flash('No restaurant assigned. Contact your admin.', 'warning')
        return redirect(url_for('dashboard.index'))

    status_filter = request.args.get('status', 'all')
    query = Order.query.filter_by(restaurant_id=restaurant.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    all_orders = query.order_by(Order.created_at.desc()).all()

    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant.id, available=True).all()
    form = OrderForm()
    notifications = get_notifications(restaurant)
    return render_template('orders.html', restaurant=restaurant, orders=all_orders,
                           menu_items=menu_items, form=form,
                           status_filter=status_filter, notifications=notifications)


@orders_bp.route('/orders/create', methods=['POST'])
@login_required
@staff_or_admin
def create():
    restaurant = get_restaurant()
    form = OrderForm()
    if form.validate_on_submit():
        order = Order(
            restaurant_id=restaurant.id,
            customer_name=form.customer_name.data,
            customer_phone=form.customer_phone.data,
            table_number=form.table_number.data,
            notes=form.notes.data
        )
        db.session.add(order)
        db.session.flush()

        item_ids = request.form.getlist('item_ids[]')
        quantities = request.form.getlist('quantities[]')
        total = 0.0
        for item_id, qty in zip(item_ids, quantities):
            try:
                qty = int(qty)
                if qty <= 0:
                    continue
                menu_item = db.session.get(MenuItem, int(item_id))
                if menu_item and menu_item.restaurant_id == restaurant.id:
                    oi = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item.id,
                        quantity=qty,
                        price=menu_item.price
                    )
                    db.session.add(oi)
                    total += menu_item.price * qty
            except (ValueError, TypeError):
                continue

        order.total_amount = round(total, 2)
        db.session.commit()
        flash(f'Order #{order.id} created for {order.customer_name}!', 'success')
    else:
        flash('Error creating order.', 'danger')
    return redirect(url_for('orders.index'))


@orders_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@staff_or_admin
def status(order_id):
    restaurant = get_restaurant()
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    new_status = request.form.get('status')
    if new_status in Order.STATUS_FLOW:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status → {new_status.title()}', 'success')
    return redirect(url_for('orders.index'))


@orders_bp.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
@staff_or_admin
def payment(order_id):
    restaurant = get_restaurant()
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    order.payment_status = 'paid'
    db.session.commit()
    flash(f'Order #{order.id} marked as paid.', 'success')
    return redirect(url_for('orders.index'))


@orders_bp.route('/orders/kds')
@login_required
@staff_or_admin
def kds():
    restaurant = get_restaurant()
    if not restaurant:
        flash('No restaurant assigned. Ask your admin to link your account.', 'warning')
        return redirect(url_for('dashboard.index'))
    active = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['placed', 'preparing'])
    ).order_by(Order.created_at).all()
    ready = Order.query.filter_by(restaurant_id=restaurant.id, status='ready').order_by(
        Order.created_at
    ).all()
    return render_template('order_kds.html', restaurant=restaurant, active=active, ready=ready)
