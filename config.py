import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rsoms-ntcc-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'rsoms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    FORCE_HTTPS = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
