import os

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from extensions import db
from models import MenuItem
from forms import MenuItemForm
from blueprints.utils import get_restaurant, get_notifications, allowed_file, admin_required

menu_bp = Blueprint('menu', __name__)


@menu_bp.route('/menu')
@login_required
@admin_required
def index():
    restaurant = get_restaurant()
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).order_by(
        MenuItem.category, MenuItem.name
    ).all()
    form = MenuItemForm()
    categories = {}
    for item in items:
        categories.setdefault(item.category, []).append(item)
    notifications = get_notifications(restaurant)
    return render_template('menu.html', restaurant=restaurant, categories=categories,
                           items=items, form=form, notifications=notifications)


@menu_bp.route('/menu/add', methods=['POST'])
@login_required
@admin_required
def add():
    restaurant = get_restaurant()
    form = MenuItemForm()
    if form.validate_on_submit():
        item = MenuItem(
            restaurant_id=restaurant.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            is_veg=form.is_veg.data,
            available=form.available.data
        )
        db.session.add(item)
        db.session.flush()

        if form.image.data:
            f = form.image.data
            if allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'menu_{restaurant.id}_{item.id}.{ext}')
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                item.image_path = filename

        db.session.commit()
        flash(f'"{item.name}" added to menu!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                flash(f'{label}: {error}', 'danger')
    return redirect(url_for('menu.index'))


@menu_bp.route('/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit(item_id):
    restaurant = get_restaurant()
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    form = MenuItemForm()
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        item.price = form.price.data
        item.category = form.category.data
        item.is_veg = form.is_veg.data
        item.available = form.available.data

        if form.image.data:
            f = form.image.data
            if allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'menu_{restaurant.id}_{item.id}.{ext}')
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                item.image_path = filename

        db.session.commit()
        flash(f'"{item.name}" updated!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                flash(f'{label}: {error}', 'danger')
    return redirect(url_for('menu.index'))


@menu_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(item_id):
    restaurant = get_restaurant()
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.name}" removed from menu.', 'info')
    return redirect(url_for('menu.index'))


@menu_bp.route('/menu/<int:item_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(item_id):
    restaurant = get_restaurant()
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    item.available = not item.available
    db.session.commit()
    return jsonify({'status': 'ok', 'available': item.available})
