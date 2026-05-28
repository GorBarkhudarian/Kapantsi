# Try to load Celery; if Redis is not running, skip gracefully
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception:
    pass
