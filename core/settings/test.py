"""
تنظیمات اجرای تست‌های واحد: از SQLite در حافظه استفاده می‌کند و Celery را در
حالت Eager اجرا می‌کند تا نیازی به Redis/Worker واقعی در محیط CI نباشد.
اجرا: DJANGO_SETTINGS_MODULE=core.settings.test python manage.py test
"""
from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
