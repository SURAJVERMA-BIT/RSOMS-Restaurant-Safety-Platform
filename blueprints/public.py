from flask import Blueprint, render_template, redirect, url_for, flash

from extensions import db, limiter
from models import Restaurant, Feedback, HygieneChecklist
from forms import FeedbackForm

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    restaurants = Restaurant.query.filter_by(is_public=True).order_by(
        Restaurant.safety_score.desc()
    ).all()
    return render_template('index.html', restaurants=restaurants)


@public_bp.route('/restaurant/<int:restaurant_id>/public')
def restaurant(restaurant_id):
    rest = Restaurant.query.filter_by(id=restaurant_id, is_public=True).first_or_404()
    form = FeedbackForm()
    recent_feedback = Feedback.query.filter_by(restaurant_id=rest.id).order_by(
        Feedback.created_at.desc()
    ).limit(10).all()
    recent_checklist = HygieneChecklist.query.filter_by(
        restaurant_id=rest.id, checklist_type='daily'
    ).order_by(HygieneChecklist.date.desc()).first()
    return render_template('public_restaurant.html',
                           restaurant=rest,
                           form=form,
                           recent_feedback=recent_feedback,
                           recent_checklist=recent_checklist)


@public_bp.route('/restaurant/<int:restaurant_id>/feedback', methods=['POST'])
@limiter.limit('5 per minute; 30 per hour')
def submit_feedback(restaurant_id):
    rest = Restaurant.query.filter_by(id=restaurant_id, is_public=True).first_or_404()
    form = FeedbackForm()
    if form.validate_on_submit():
        fb = Feedback(
            restaurant_id=rest.id,
            customer_name=form.customer_name.data,
            rating=int(form.rating.data),
            comment=form.comment.data
        )
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
    return redirect(url_for('public.restaurant', restaurant_id=rest.id))
