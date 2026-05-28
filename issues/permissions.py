"""
issues/permissions.py — DRF custom permission classes for the Issues app.

These are used in APIView / ViewSet classes via:
    permission_classes = [IsVerifiedCitizen]
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """
    Allow access only to users whose role is 'admin' or who are Django staff.
    """
    message = "Only platform administrators can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )


class IsVerifiedCitizen(BasePermission):
    """
    Allow access only to authenticated users whose identity has been verified.
    """
    message = "Your account must be verified before you can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.verified
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allow owners of an object, or admin users.

    The object must have a ``reporter`` attribute pointing to its owner.
    """
    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        owner = getattr(obj, 'reporter', getattr(obj, 'user', None))
        return owner == request.user


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Read-only for everyone; write access only for owners or admins.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        owner = getattr(obj, 'reporter', getattr(obj, 'user', None))
        return owner == request.user


class CanVote(BasePermission):
    """
    Allow voting only for authenticated, verified citizens.
    Admins are excluded from voting to avoid conflicts of interest.
    """
    message = "Only verified citizens can vote on issues."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return False  # Admins should not vote
        return request.user.verified


class CanChangeIssueStatus(BasePermission):
    """
    Allow issue status updates only to admin users.
    """
    message = "Only administrators can change an issue's status."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )
