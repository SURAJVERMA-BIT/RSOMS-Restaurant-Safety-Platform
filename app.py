import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, flash, jsonify
from flask_login import current_user
from flask_talisman import Talisman

load_dotenv()

from config import config
from extensions import db, login_manager, limiter, migrate
from models import User
from blueprints.utils import get_restaurant, get_notifications
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.restaurant import restaurant_bp
from blueprints.menu import menu_bp
from blueprints.orders import orders_bp
from blueprints.hygiene import hygiene_bp
from blueprints.staff import staff_bp
from blueprints.analytics import analytics_bp
from blueprints.notifications import notifications_bp
from blueprints.public import public_bp
from blueprints.api import api_bp

CSP = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
        'https://fonts.googleapis.com',
    ],
    'font-src': [
        "'self'",
        'https://cdnjs.cloudflare.com',
        'https://fonts.gstatic.com',
    ],
    'img-src': ["'self'", 'data:'],
    'connect-src': ["'self'"],
    'frame-ancestors': ["'none'"],
}


def configure_logging(app):
    level = logging.DEBUG if app.debug else logging.INFO
    fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(fmt)
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    logging.getLogger('werkzeug').setLevel(logging.WARNING if not app.debug else logging.INFO)


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    Talisman(
        app,
        force_https=app.config.get('FORCE_HTTPS', False),
        strict_transport_security=app.config.get('FORCE_HTTPS', False),
        content_security_policy=CSP,
        content_security_policy_nonce_in=['script-src'],
        x_content_type_options=True,
        x_xss_protection=True,
        referrer_policy='strict-origin-when-cross-origin',
    )
    configure_logging(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.login_message = 'Please login to access this page.'

    @login_manager.user_loader
    def load_user(user_id):  # noqa: used by Flask-Login via decorator
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ok', 'db': 'connected'}), 200
        except Exception:
            return jsonify({'status': 'error', 'db': 'unreachable'}), 503

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(hygiene_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(_):
        return render_template('404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(_):
        flash('Too many requests. Please slow down and try again shortly.', 'danger')
        return render_template('429.html'), 429

    @app.errorhandler(500)
    def server_error(exc):
        app.logger.exception('Unhandled server error: %s', exc)
        return render_template('500.html'), 500

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
            current_year=datetime.now().year,
        )

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
