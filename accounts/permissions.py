# -*- coding: utf-8 -*-
"""
Centralised RBAC helpers for Kapantsi.

Web views   → use @admin_required / @citizen_required decorators
DRF views   → use IsAdminRoleUser / IsCitizenUser permission classes
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission


# ── Web-view decorators ────────────────────────────────────────────────────

def admin_required(view_func):
    """Allow access only to admin-role or staff users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not getattr(request.user, 'is_admin_user', False):
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def citizen_required(view_func):
    """Allow access only to authenticated non-admin (citizen) users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if getattr(request.user, 'is_admin_user', False):
            # Admins land on the admin dashboard instead
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── DRF permission classes ─────────────────────────────────────────────────

class IsAdminRoleUser(BasePermission):
    """Grant access only to admin-role or staff users."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_admin_user', False)
        )


class IsCitizenUser(BasePermission):
    """Grant access only to verified citizen users."""
    message = 'Citizen access required.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_citizen', False)
        )
