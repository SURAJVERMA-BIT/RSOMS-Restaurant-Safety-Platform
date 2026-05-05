import os
import json
from datetime import datetime, date
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, flash,
                   request, jsonify, abort, session)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import config
from models import (db, User, Restaurant, MenuItem, Order, OrderItem,
                    HygieneChecklist, StaffTraining, Feedback,
                    DAILY_TASKS, WEEKLY_TASKS)
from forms import (LoginForm, RegisterForm, RestaurantProfileForm, FSSAIUploadForm,
                   MenuItemForm, OrderForm, HygieneChecklistForm,
                   StaffTrainingForm, FeedbackForm)


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'warning'
    login_manager.login_message = 'Please login to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    return app


app = create_app()


# ─── Helpers & Decorators ────────────────────────────────────────────────────

def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def staff_or_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'staff'):
            flash('Staff access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_restaurant():
    """Get restaurant for current admin user."""
    return Restaurant.query.filter_by(owner_id=current_user.id).first()


def get_notifications(restaurant):
    """Build notification list for a restaurant."""
    notes = []
    if restaurant:
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
            restaurant_id=restaurant.id, checklist_type='daily',
            date=date.today()
        ).first()
        if not today_checklist:
            notes.append({'type': 'warning', 'icon': 'fa-clipboard-list',
                          'msg': "Today's daily hygiene checklist not submitted."})

        expiring_training = StaffTraining.query.filter_by(
            restaurant_id=restaurant.id, status='expiring_soon'
        ).count()
        if expiring_training:
            notes.append({'type': 'info', 'icon': 'fa-user-graduate',
                          'msg': f'{expiring_training} staff training record(s) expiring soon.'})

        expired_training = StaffTraining.query.filter_by(
            restaurant_id=restaurant.id, status='expired'
        ).count()
        if expired_training:
            notes.append({'type': 'danger', 'icon': 'fa-user-times',
                          'msg': f'{expired_training} staff training record(s) EXPIRED.'})
    return notes


# ─── Public / Auth Routes ─────────────────────────────────────────────────────

@app.route('/')
def index():
    restaurants = Restaurant.query.filter_by(is_public=True).order_by(
        Restaurant.safety_score.desc()
    ).all()
    return render_template('index.html', restaurants=restaurants)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            nxt = request.args.get('next')
            return redirect(nxt or url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if form.role.data == 'admin':
            restaurant = Restaurant(owner_id=user.id, name=f"{user.username}'s Restaurant")
            db.session.add(restaurant)

        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    restaurant = get_restaurant()
    if current_user.role == 'consumer':
        return redirect(url_for('index'))

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
            'feedback_count': len(restaurant.feedback_list)
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
            restaurant_id=restaurant.id, checklist_type='daily',
            date=date.today()
        ).first()

    return render_template('dashboard.html',
                           restaurant=restaurant,
                           notifications=notifications,
                           stats=stats,
                           recent_orders=recent_orders,
                           score_history=json.dumps(score_history),
                           today_checklist=today_checklist)


# ─── Restaurant Profile ───────────────────────────────────────────────────────

@app.route('/restaurant/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def restaurant_profile():
    restaurant = get_restaurant()
    form = RestaurantProfileForm(obj=restaurant)
    upload_form = FSSAIUploadForm()

    if form.validate_on_submit():
        restaurant.name = form.name.data
        restaurant.address = form.address.data
        restaurant.cuisine = form.cuisine.data
        restaurant.contact = form.contact.data
        restaurant.description = form.description.data
        restaurant.fssai_number = form.fssai_number.data
        restaurant.fssai_issue_date = form.fssai_issue_date.data
        restaurant.fssai_expiry_date = form.fssai_expiry_date.data
        restaurant.is_public = form.is_public.data
        db.session.commit()
        flash('Restaurant profile updated!', 'success')
        return redirect(url_for('restaurant_profile'))

    notifications = get_notifications(restaurant)
    return render_template('restaurant_profile.html',
                           restaurant=restaurant,
                           form=form,
                           upload_form=upload_form,
                           notifications=notifications)


@app.route('/restaurant/fssai-upload', methods=['POST'])
@login_required
@admin_required
def fssai_upload():
    restaurant = get_restaurant()
    upload_form = FSSAIUploadForm()
    if upload_form.validate_on_submit():
        f = upload_form.certificate.data
        if f and allowed_file(f.filename):
            filename = secure_filename(f'fssai_{restaurant.id}_{f.filename}')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)
            restaurant.fssai_cert_path = filename
            db.session.commit()
            flash('FSSAI certificate uploaded successfully!', 'success')
        else:
            flash('Invalid file type. PDF, JPG, PNG only.', 'danger')
    return redirect(url_for('restaurant_profile'))


# ─── Menu Management ──────────────────────────────────────────────────────────

@app.route('/menu')
@login_required
@admin_required
def menu():
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


@app.route('/menu/add', methods=['POST'])
@login_required
@admin_required
def menu_add():
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
        db.session.commit()
        flash(f'"{item.name}" added to menu!', 'success')
    else:
        flash('Error adding item. Check all fields.', 'danger')
    return redirect(url_for('menu'))


@app.route('/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@admin_required
def menu_edit(item_id):
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
        db.session.commit()
        flash(f'"{item.name}" updated!', 'success')
    return redirect(url_for('menu'))


@app.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def menu_delete(item_id):
    restaurant = get_restaurant()
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.name}" removed from menu.', 'info')
    return redirect(url_for('menu'))


@app.route('/menu/<int:item_id>/toggle', methods=['POST'])
@login_required
@admin_required
def menu_toggle(item_id):
    restaurant = get_restaurant()
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    item.available = not item.available
    db.session.commit()
    return jsonify({'status': 'ok', 'available': item.available})


# ─── Order Management ─────────────────────────────────────────────────────────

@app.route('/orders')
@login_required
@staff_or_admin
def orders():
    restaurant = get_restaurant()
    if not restaurant and current_user.role == 'staff':
        flash('No restaurant assigned. Contact your admin.', 'warning')
        return redirect(url_for('dashboard'))

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


@app.route('/orders/create', methods=['POST'])
@login_required
@staff_or_admin
def order_create():
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
                menu_item = MenuItem.query.get(int(item_id))
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
    return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@staff_or_admin
def order_status(order_id):
    restaurant = get_restaurant()
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    new_status = request.form.get('status')
    if new_status in Order.STATUS_FLOW:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status → {new_status.title()}', 'success')
    return redirect(url_for('orders'))


@app.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
@staff_or_admin
def order_payment(order_id):
    restaurant = get_restaurant()
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    order.payment_status = 'paid'
    db.session.commit()
    flash(f'Order #{order.id} marked as paid.', 'success')
    return redirect(url_for('orders'))


@app.route('/orders/kds')
@login_required
@staff_or_admin
def order_kds():
    restaurant = get_restaurant()
    active = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['placed', 'preparing'])
    ).order_by(Order.created_at).all()
    ready = Order.query.filter_by(restaurant_id=restaurant.id, status='ready').order_by(
        Order.created_at
    ).all()
    return render_template('order_kds.html', restaurant=restaurant,
                           active=active, ready=ready)


# ─── Hygiene Checklist ────────────────────────────────────────────────────────

@app.route('/hygiene')
@login_required
@staff_or_admin
def hygiene():
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


@app.route('/hygiene/submit', methods=['POST'])
@login_required
@staff_or_admin
def hygiene_submit():
    restaurant = get_restaurant()
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
    restaurant.calculate_and_update_score()
    db.session.commit()
    flash(f'{ctype.title()} checklist submitted! Score: {checklist.score_pct}%', 'success')
    return redirect(url_for('hygiene'))


# ─── Staff Training ───────────────────────────────────────────────────────────

@app.route('/staff/training')
@login_required
@admin_required
def staff_training():
    restaurant = get_restaurant()
    for rec in restaurant.training_records:
        rec.update_status()
    db.session.commit()

    records = StaffTraining.query.filter_by(restaurant_id=restaurant.id).order_by(
        StaffTraining.expiry_date
    ).all()
    form = StaffTrainingForm()
    notifications = get_notifications(restaurant)
    return render_template('staff_training.html', restaurant=restaurant,
                           records=records, form=form, notifications=notifications)


@app.route('/staff/training/add', methods=['POST'])
@login_required
@admin_required
def staff_training_add():
    restaurant = get_restaurant()
    form = StaffTrainingForm()
    if form.validate_on_submit():
        rec = StaffTraining(
            restaurant_id=restaurant.id,
            staff_name=form.staff_name.data,
            training_type=form.training_type.data,
            completion_date=form.completion_date.data,
            expiry_date=form.expiry_date.data
        )
        rec.update_status()
        db.session.add(rec)
        restaurant.calculate_and_update_score()
        db.session.commit()
        flash(f'Training record added for {rec.staff_name}.', 'success')
    else:
        flash('Error adding training record.', 'danger')
    return redirect(url_for('staff_training'))


@app.route('/staff/training/<int:rec_id>/delete', methods=['POST'])
@login_required
@admin_required
def staff_training_delete(rec_id):
    restaurant = get_restaurant()
    rec = StaffTraining.query.filter_by(id=rec_id, restaurant_id=restaurant.id).first_or_404()
    db.session.delete(rec)
    db.session.commit()
    flash('Training record deleted.', 'info')
    return redirect(url_for('staff_training'))


# ─── Analytics ────────────────────────────────────────────────────────────────

@app.route('/analytics')
@login_required
@admin_required
def analytics():
    restaurant = get_restaurant()
    from sqlalchemy import extract

    checklists_30 = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id, checklist_type='daily'
    ).order_by(HygieneChecklist.date).all()
    score_labels = [str(c.date) for c in checklists_30]
    score_data = [c.score_pct for c in checklists_30]

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


# ─── Notifications ────────────────────────────────────────────────────────────

@app.route('/notifications')
@login_required
@staff_or_admin
def notifications():
    restaurant = get_restaurant()
    notes = get_notifications(restaurant)
    return render_template('notifications.html', restaurant=restaurant, notifications=notes)


# ─── Public Safety Page ───────────────────────────────────────────────────────

@app.route('/restaurant/<int:restaurant_id>/public')
def public_restaurant(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_public=True).first_or_404()
    form = FeedbackForm()
    recent_feedback = Feedback.query.filter_by(restaurant_id=restaurant.id).order_by(
        Feedback.created_at.desc()
    ).limit(10).all()
    recent_checklist = HygieneChecklist.query.filter_by(
        restaurant_id=restaurant.id, checklist_type='daily'
    ).order_by(HygieneChecklist.date.desc()).first()
    return render_template('public_restaurant.html',
                           restaurant=restaurant,
                           form=form,
                           recent_feedback=recent_feedback,
                           recent_checklist=recent_checklist)


@app.route('/restaurant/<int:restaurant_id>/feedback', methods=['POST'])
def submit_feedback(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_public=True).first_or_404()
    form = FeedbackForm()
    if form.validate_on_submit():
        fb = Feedback(
            restaurant_id=restaurant.id,
            customer_name=form.customer_name.data,
            rating=int(form.rating.data),
            comment=form.comment.data
        )
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
    return redirect(url_for('public_restaurant', restaurant_id=restaurant.id))


# ─── API Endpoints (JSON) ─────────────────────────────────────────────────────

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
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
        'fssai_days': restaurant.fssai_days_to_expiry
    })


@app.route('/api/orders')
@login_required
def api_orders():
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
        'time': o.created_at.strftime('%H:%M')
    } for o in active])


@app.route('/api/hygiene/score')
@login_required
def api_hygiene_score():
    restaurant = get_restaurant()
    restaurant.calculate_and_update_score()
    db.session.commit()
    return jsonify({'score': restaurant.safety_score, 'badge': restaurant.badge_status})


@app.route('/api/menu')
@login_required
def api_menu():
    restaurant = get_restaurant()
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return jsonify([{
        'id': i.id, 'name': i.name, 'price': i.price,
        'category': i.category, 'available': i.available, 'is_veg': i.is_veg
    } for i in items])


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ─── Context Processors ───────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    restaurant = None
    notification_count = 0
    if current_user.is_authenticated and current_user.role in ('admin', 'staff'):
        restaurant = get_restaurant()
        if restaurant:
            notification_count = len(get_notifications(restaurant))
    return dict(
        g_restaurant=restaurant,
        notification_count=notification_count,
        current_year=datetime.now().year
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
