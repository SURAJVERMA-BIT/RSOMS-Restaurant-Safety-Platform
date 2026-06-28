from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import StaffTraining
from forms import StaffTrainingForm
from blueprints.utils import get_restaurant, get_notifications, admin_required

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/staff/training')
@login_required
@admin_required
def training():
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


@staff_bp.route('/staff/training/add', methods=['POST'])
@login_required
@admin_required
def training_add():
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
    return redirect(url_for('staff.training'))


@staff_bp.route('/staff/training/<int:rec_id>/delete', methods=['POST'])
@login_required
@admin_required
def training_delete(rec_id):
    restaurant = get_restaurant()
    rec = StaffTraining.query.filter_by(id=rec_id, restaurant_id=restaurant.id).first_or_404()
    db.session.delete(rec)
    db.session.commit()
    flash('Training record deleted.', 'info')
    return redirect(url_for('staff.training'))
