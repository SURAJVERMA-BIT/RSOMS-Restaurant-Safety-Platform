from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     FloatField, IntegerField, BooleanField, DateField, HiddenField,
                     SubmitField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(),
                            EqualTo('password', message='Passwords must match')])
    role = SelectField('Register As', choices=[
        ('admin', 'Restaurant Owner / Admin'),
        ('staff', 'Kitchen Staff / Manager'),
        ('consumer', 'Consumer (Browse Only)')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Account')


class RestaurantProfileForm(FlaskForm):
    name = StringField('Restaurant Name', validators=[DataRequired(), Length(max=200)])
    address = TextAreaField('Address', validators=[Optional()])
    cuisine = StringField('Cuisine Type', validators=[Optional(), Length(max=100)])
    contact = StringField('Contact Number', validators=[Optional(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    fssai_number = StringField('FSSAI License Number', validators=[Optional(), Length(max=50)])
    fssai_issue_date = DateField('FSSAI Issue Date', validators=[Optional()])
    fssai_expiry_date = DateField('FSSAI Expiry Date', validators=[Optional()])
    is_public = BooleanField('Make restaurant publicly visible')
    submit = SubmitField('Save Profile')


class FSSAIUploadForm(FlaskForm):
    certificate = FileField('FSSAI Certificate', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF or image files only!')
    ])
    submit = SubmitField('Upload Certificate')


class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('Starter', 'Starter'), ('Main Course', 'Main Course'),
        ('Dessert', 'Dessert'), ('Beverage', 'Beverage'),
        ('Bread', 'Bread'), ('Salad', 'Salad'), ('Soup', 'Soup'), ('Special', 'Special')
    ])
    is_veg = BooleanField('Vegetarian')
    available = BooleanField('Available')
    submit = SubmitField('Save Item')


class OrderForm(FlaskForm):
    customer_name = StringField('Customer Name', validators=[DataRequired(), Length(max=100)])
    customer_phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    table_number = StringField('Table Number', validators=[Optional(), Length(max=20)])
    notes = TextAreaField('Special Notes', validators=[Optional()])
    submit = SubmitField('Create Order')


class HygieneChecklistForm(FlaskForm):
    checklist_type = HiddenField('Type', default='daily')
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Submit Checklist')


class StaffTrainingForm(FlaskForm):
    staff_name = StringField('Staff Name', validators=[DataRequired(), Length(max=100)])
    training_type = SelectField('Training Type', choices=[
        ('Food Safety & Hygiene', 'Food Safety & Hygiene'),
        ('FSSAI Compliance', 'FSSAI Compliance'),
        ('Fire Safety', 'Fire Safety'),
        ('First Aid', 'First Aid'),
        ('Kitchen Safety', 'Kitchen Safety'),
        ('Customer Handling', 'Customer Handling'),
        ('COVID / Infection Control', 'COVID / Infection Control'),
    ])
    completion_date = DateField('Completion Date', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    submit = SubmitField('Add Record')


class FeedbackForm(FlaskForm):
    customer_name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    rating = SelectField('Rating', choices=[
        ('5', '⭐⭐⭐⭐⭐ Excellent'),
        ('4', '⭐⭐⭐⭐ Good'),
        ('3', '⭐⭐⭐ Average'),
        ('2', '⭐⭐ Poor'),
        ('1', '⭐ Very Poor')
    ], validators=[DataRequired()])
    comment = TextAreaField('Your Comment', validators=[Optional()])
    submit = SubmitField('Submit Feedback')
