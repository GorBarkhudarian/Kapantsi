from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from issues.models import Issue
from voting.models import Vote
from notifications.models import Notification
from accounts.permissions import admin_required, citizen_required


class DashboardStatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        total_issues = Issue.objects.count()
        by_status = {}
        for s, label in Issue.STATUS_CHOICES:
            by_status[s] = Issue.objects.filter(status=s).count()
        by_category = {}
        for c, label in Issue.CATEGORY_CHOICES:
            by_category[c] = Issue.objects.filter(category=c).count()
        return Response({
            'total_issues': total_issues,
            'total_users': User.objects.count(),
            'total_votes': Vote.objects.count(),
            'by_status': by_status,
            'by_category': by_category,
        })


@citizen_required
def citizen_dashboard_view(request):
    user = request.user
    my_issues = Issue.objects.filter(created_by=user).order_by('-created_at')
    my_votes = Vote.objects.filter(user=user).select_related('issue').order_by('-created_at')
    notifications = Notification.objects.filter(user=user, read=False)[:10]
    unread_count = Notification.objects.filter(user=user, read=False).count()
    return render(request, 'dashboard/citizen.html', {
        'my_issues': my_issues,
        'my_votes': my_votes,
        'notifications': notifications,
        'unread_count': unread_count,
    })


@admin_required
def admin_dashboard_view(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    issues = Issue.objects.select_related('created_by').order_by('-created_at')
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        new_status = request.POST.get('status')
        if issue_id and new_status:
            try:
                issue = Issue.objects.get(pk=issue_id)
                old_status = issue.status
                if old_status != new_status:
                    issue.status = new_status
                    issue.admin_notes = request.POST.get('admin_notes', issue.admin_notes)
                    issue.save()
                    from issues.utils import record_status_change
                    record_status_change(issue, old_status, new_status, request.user,
                                        note=request.POST.get('admin_notes', ''))
                    from django.contrib import messages
                    messages.success(request, f'Issue #{issue_id} status updated.')
            except Issue.DoesNotExist:
                pass
        from django.shortcuts import redirect
        return redirect('admin_dashboard')

    from issues.views import _CATEGORY_LABELS, _STATUS_LABELS, _AREA_LABELS
    from django.utils.translation import get_language
    lang = (get_language() or 'en')[:2]

    stats = {
        'total': Issue.objects.count(),
        'pending': Issue.objects.filter(status='pending').count(),
        'under_review': Issue.objects.filter(status='under_review').count(),
        'in_progress': Issue.objects.filter(status='in_progress').count(),
        'completed': Issue.objects.filter(status='completed').count(),
        'rejected': Issue.objects.filter(status='rejected').count(),
        'total_users': User.objects.count(),
        'total_votes': Vote.objects.count(),
        'by_category': {c: Issue.objects.filter(category=c).count() for c, _ in Issue.CATEGORY_CHOICES},
    }
    return render(request, 'dashboard/admin.html', {
        'issues': issues,
        'stats': stats,
        'status_choices': Issue.STATUS_CHOICES,
        'category_choices': Issue.CATEGORY_CHOICES,
        'category_labels': _CATEGORY_LABELS.get(lang, _CATEGORY_LABELS['en']),
        'status_labels': _STATUS_LABELS.get(lang, _STATUS_LABELS['en']),
        'area_labels': _AREA_LABELS.get(lang, _AREA_LABELS['en']),
    })


@admin_required
def admin_delete_issue_view(request, pk):
    """Admin-only: permanently delete a reported issue."""
    if request.method == 'POST':
        issue = get_object_or_404(Issue, pk=pk)
        issue.delete()
        messages.success(request, f'Issue #{pk} has been deleted.')
    return redirect('admin_dashboard')
