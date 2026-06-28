import os

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from extensions import db, limiter
from forms import RestaurantProfileForm, FSSAIUploadForm
from blueprints.utils import get_restaurant, get_notifications, allowed_file, admin_required

restaurant_bp = Blueprint('restaurant', __name__)


@restaurant_bp.route('/restaurant/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
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
        return redirect(url_for('restaurant.profile'))

    notifications = get_notifications(restaurant)
    return render_template('restaurant_profile.html',
                           restaurant=restaurant,
                           form=form,
                           upload_form=upload_form,
                           notifications=notifications)


@restaurant_bp.route('/restaurant/fssai-upload', methods=['POST'])
@login_required
@admin_required
@limiter.limit('10 per hour')
def fssai_upload():
    restaurant = get_restaurant()
    upload_form = FSSAIUploadForm()
    if upload_form.validate_on_submit():
        f = upload_form.certificate.data
        if f and allowed_file(f.filename):
            filename = secure_filename(f'fssai_{restaurant.id}_{f.filename}')
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)
            restaurant.fssai_cert_path = filename
            db.session.commit()
            flash('FSSAI certificate uploaded successfully!', 'success')
        else:
            flash('Invalid file type. PDF, JPG, PNG only.', 'danger')
    return redirect(url_for('restaurant.profile'))
