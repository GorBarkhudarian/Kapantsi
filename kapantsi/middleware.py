"""
Custom middleware for the Kapantsi platform.

Included:
    RequestLoggingMiddleware   — logs method, path, status code, and duration
    ActiveUserMiddleware       — tracks last-seen timestamp for authenticated users
    HealthCheckMiddleware      — fast-path response for /health/ without hitting views
    SecurityHeadersMiddleware  — adds security-related HTTP response headers
"""
import time
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('kapantsi.requests')


# ---------------------------------------------------------------------------
# 1. Request Logging Middleware
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware:
    """
    Logs every HTTP request with method, path, status code, and response time.
    Skips static and media file paths to keep logs clean.

    Log format:
        [METHOD] /path/ → STATUS  (Xms)  [user: username_or_anon]
    """

    SKIP_PREFIXES = ('/static/', '/media/', '/favicon.ico')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip noisy static/media paths
        if any(request.path.startswith(p) for p in self.SKIP_PREFIXES):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        user = getattr(request, 'user', None)
        username = user.username if (user and user.is_authenticated) else 'anon'

        logger.info(
            '[%s] %s → %s  (%dms)  [user: %s]',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            username,
        )
        return response


# ---------------------------------------------------------------------------
# 2. Active User Middleware
# ---------------------------------------------------------------------------

class ActiveUserMiddleware:
    """
    Updates a `last_seen` field on the authenticated User model
    at most once per 5 minutes per session, to avoid excessive DB writes.

    Requires the User model to have a `last_seen` DateTimeField.
    If the field does not exist the middleware silently skips the update.
    """

    UPDATE_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._update_last_seen(request)
        return response

    def _update_last_seen(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return
        if not hasattr(user, 'last_seen'):
            return
        now = timezone.now()
        last = user.last_seen
        if last is None or (now - last).total_seconds() > self.UPDATE_INTERVAL_SECONDS:
            try:
                type(user).objects.filter(pk=user.pk).update(last_seen=now)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 3. Health Check Middleware
# ---------------------------------------------------------------------------

class HealthCheckMiddleware:
    """
    Intercepts requests to /health/ and returns a JSON response immediately,
    bypassing the full Django view layer.  Useful for load balancer checks.

    Response: 200 {"status": "ok", "service": "kapantsi"}
    """

    HEALTH_PATH = '/health/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.HEALTH_PATH:
            return JsonResponse({'status': 'ok', 'service': 'kapantsi'})
        return self.get_response(request)


# ---------------------------------------------------------------------------
# 4. Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware:
    """
    Adds a set of security-related HTTP response headers to every response.

    Headers added:
        X-Content-Type-Options: nosniff
        X-Frame-Options: DENY
        Referrer-Policy: strict-origin-when-cross-origin
        Permissions-Policy: camera=(), microphone=(), geolocation=(self)
        X-Kapantsi-Version: 1.0
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('X-Frame-Options', 'DENY')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(self)',
        )
        response.setdefault('X-Kapantsi-Version', '1.0')
        return response
