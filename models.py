from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='consumer')  # admin, staff, consumer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship('Restaurant', backref='owner', uselist=False,
                                 foreign_keys='Restaurant.owner_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    __table_args__ = (
        db.Index('ix_restaurants_owner_id', 'owner_id'),
        db.Index('ix_restaurants_safety_score', 'safety_score'),
    )
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, default='')
    cuisine = db.Column(db.String(100), default='')
    contact = db.Column(db.String(20), default='')
    description = db.Column(db.Text, default='')
    fssai_number = db.Column(db.String(50), default='')
    fssai_cert_path = db.Column(db.String(255), default='')
    fssai_issue_date = db.Column(db.Date, nullable=True)
    fssai_expiry_date = db.Column(db.Date, nullable=True)
    safety_score = db.Column(db.Float, default=0.0)
    badge_status = db.Column(db.String(20), default='unrated')
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True,
                                 cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='restaurant', lazy=True,
                             cascade='all, delete-orphan')
    checklists = db.relationship('HygieneChecklist', backref='restaurant', lazy=True,
                                 cascade='all, delete-orphan')
    training_records = db.relationship('StaffTraining', backref='restaurant', lazy=True,
                                       cascade='all, delete-orphan')
    feedback_list = db.relationship('Feedback', backref='restaurant', lazy=True,
                                    cascade='all, delete-orphan')

    @property
    def fssai_days_to_expiry(self):
        if self.fssai_expiry_date:
            delta = self.fssai_expiry_date - date.today()
            return delta.days
        return None

    @property
    def fssai_status(self):
        days = self.fssai_days_to_expiry
        if days is None:
            return 'not_uploaded'
        if days < 0:
            return 'expired'
        if days <= 7:
            return 'critical'
        if days <= 15:
            return 'warning'
        if days <= 30:
            return 'notice'
        return 'valid'

    def update_badge(self):
        score = self.safety_score
        if score >= 90:
            self.badge_status = 'gold'
        elif score >= 75:
            self.badge_status = 'silver'
        elif score >= 60:
            self.badge_status = 'bronze'
        elif score > 0:
            self.badge_status = 'red'
        else:
            self.badge_status = 'unrated'

    def calculate_and_update_score(self):
        from sqlalchemy import func
        today = date.today()
        seven_days_ago = date(today.year, today.month, max(1, today.day - 7))

        daily = HygieneChecklist.query.filter_by(
            restaurant_id=self.id, checklist_type='daily'
        ).filter(HygieneChecklist.date >= seven_days_ago).all()

        weekly = HygieneChecklist.query.filter_by(
            restaurant_id=self.id, checklist_type='weekly'
        ).order_by(HygieneChecklist.date.desc()).first()

        total_staff = StaffTraining.query.filter_by(restaurant_id=self.id).count()
        valid_training = StaffTraining.query.filter_by(
            restaurant_id=self.id, status='valid'
        ).count()

        daily_score = 0.0
        if daily:
            avg = sum(
                (c.completed_count / c.total_count * 100) if c.total_count > 0 else 0
                for c in daily
            ) / len(daily)
            daily_score = avg

        weekly_score = 0.0
        if weekly and weekly.total_count > 0:
            weekly_score = (weekly.completed_count / weekly.total_count) * 100

        training_score = 0.0
        if total_staff > 0:
            training_score = (valid_training / total_staff) * 100

        self.safety_score = round(
            (daily_score * 0.6) + (weekly_score * 0.2) + (training_score * 0.2), 1
        )
        self.update_badge()

    @property
    def average_rating(self):
        if not self.feedback_list:
            return 0
        return round(sum(f.rating for f in self.feedback_list) / len(self.feedback_list), 1)

    def __repr__(self):
        return f'<Restaurant {self.name}>'


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), default='Main Course')
    available = db.Column(db.Boolean, default=True)
    is_veg = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

    def __repr__(self):
        return f'<MenuItem {self.name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.Index('ix_orders_restaurant_id', 'restaurant_id'),
        db.Index('ix_orders_status', 'status'),
        db.Index('ix_orders_created_at', 'created_at'),
    )
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), default='')
    table_number = db.Column(db.String(20), default='')
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='placed')  # placed, preparing, ready, served
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True,
                            cascade='all, delete-orphan')

    STATUS_FLOW = ['placed', 'preparing', 'ready', 'served']

    def next_status(self):
        try:
            idx = self.STATUS_FLOW.index(self.status)
            if idx < len(self.STATUS_FLOW) - 1:
                return self.STATUS_FLOW[idx + 1]
        except ValueError:
            pass
        return self.status

    def __repr__(self):
        return f'<Order #{self.id} {self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

    def subtotal(self):
        return self.quantity * self.price


DAILY_TASKS = [
    {'key': 'hand_washing', 'label': 'Staff hand-washing logs verified'},
    {'key': 'surface_cleaning', 'label': 'Kitchen surfaces cleaned & sanitized'},
    {'key': 'fridge_temp', 'label': 'Refrigerator temperature checked (1–4°C)'},
    {'key': 'waste_disposal', 'label': 'Waste bins emptied and sanitized'},
    {'key': 'pest_check', 'label': 'Pest control check done'},
    {'key': 'uniform_gloves', 'label': 'All staff in uniform and gloves'},
    {'key': 'food_storage', 'label': 'Raw/cooked food stored separately'},
    {'key': 'water_quality', 'label': 'Drinking water quality confirmed safe'},
]

WEEKLY_TASKS = [
    {'key': 'deep_clean_kitchen', 'label': 'Deep kitchen cleaning completed'},
    {'key': 'exhaust_cleaning', 'label': 'Exhaust fans and vents cleaned'},
    {'key': 'fridge_deep_clean', 'label': 'Refrigerator deep cleaned and defrosted'},
    {'key': 'drain_cleaning', 'label': 'Drains and sinks disinfected'},
    {'key': 'pest_control_spray', 'label': 'Pest control spray done'},
    {'key': 'equipment_inspection', 'label': 'All kitchen equipment inspected'},
    {'key': 'staff_hygiene_review', 'label': 'Staff hygiene standards reviewed'},
    {'key': 'storage_area_clean', 'label': 'Dry storage area cleaned and organized'},
    {'key': 'fire_safety_check', 'label': 'Fire extinguisher and safety check done'},
    {'key': 'first_aid_check', 'label': 'First aid kit stocked and verified'},
]


class HygieneChecklist(db.Model):
    __tablename__ = 'hygiene_checklists'
    __table_args__ = (
        db.Index('ix_hygiene_restaurant_date', 'restaurant_id', 'date'),
        db.Index('ix_hygiene_type', 'checklist_type'),
    )
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    checklist_type = db.Column(db.String(20), default='daily')  # daily, weekly
    date = db.Column(db.Date, default=date.today)
    tasks_json = db.Column(db.Text, default='{}')
    completed_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=8)
    notes = db.Column(db.Text, default='')
    kitchen_photo = db.Column(db.String(255), default='')
    restaurant_photo = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship('User', foreign_keys=[staff_id])

    @property
    def tasks(self):
        try:
            return json.loads(self.tasks_json)
        except Exception:
            return {}

    @property
    def score_pct(self):
        if self.total_count == 0:
            return 0
        return round((self.completed_count / self.total_count) * 100, 1)

    def __repr__(self):
        return f'<Checklist {self.checklist_type} {self.date}>'


class StaffTraining(db.Model):
    __tablename__ = 'staff_training'
    __table_args__ = (
        db.Index('ix_training_restaurant_id', 'restaurant_id'),
        db.Index('ix_training_status', 'status'),
    )
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    training_type = db.Column(db.String(100), nullable=False)
    completion_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='valid')  # valid, expired, expiring_soon
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def update_status(self):
        if not self.expiry_date:
            self.status = 'valid'
            return
        today = date.today()
        if self.expiry_date < today:
            self.status = 'expired'
        elif (self.expiry_date - today).days <= 30:
            self.status = 'expiring_soon'
        else:
            self.status = 'valid'

    def __repr__(self):
        return f'<Training {self.staff_name} - {self.training_type}>'


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Feedback {self.customer_name} {self.rating}★>'
