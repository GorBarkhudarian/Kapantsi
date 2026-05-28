from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from accounts.permissions import IsAdminRoleUser, citizen_required
from .models import Issue, IssueComment, IssueImage
from .serializers import (
    IssueListSerializer, IssueDetailSerializer,
    IssueCreateSerializer, IssueStatusUpdateSerializer,
    IssueCommentSerializer
)
from .forms import IssueForm, IssueCommentForm


class IssueListCreateAPIView(generics.ListCreateAPIView):
    queryset = Issue.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title_hy', 'title_en', 'description_hy', 'location_address']
    ordering_fields = ['upvote_count', 'created_at', 'status']
    ordering = ['-upvote_count', '-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IssueCreateSerializer
        return IssueListSerializer

    def get_queryset(self):
        qs = Issue.objects.all()
        cat = self.request.query_params.get('category')
        stat = self.request.query_params.get('status')
        area = self.request.query_params.get('area')
        if cat:
            qs = qs.filter(category=cat)
        if stat:
            qs = qs.filter(status=stat)
        if area:
            qs = qs.filter(area=area)
        return qs


class IssueDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Issue.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return IssueStatusUpdateSerializer
        return IssueDetailSerializer

    def update(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_admin_user', False):
            return Response({'detail': 'Admin access required.'}, status=403)
        return super().update(request, *args, **kwargs)


class VoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        issue = get_object_or_404(Issue, pk=pk)
        user = request.user
        if not user.verified:
            return Response({'detail': 'Only verified citizens can vote.'}, status=403)
        from voting.models import Vote
        vote, created = Vote.objects.get_or_create(user=user, issue=issue)
        if not created:
            issue.refresh_from_db()
            return Response({'detail': 'You already voted.', 'upvote_count': issue.upvote_count}, status=400)
        issue.refresh_from_db()
        return Response({'detail': 'Vote cast.', 'upvote_count': issue.upvote_count}, status=201)

    def delete(self, request, pk):
        issue = get_object_or_404(Issue, pk=pk)
        from voting.models import Vote
        votes = list(Vote.objects.filter(user=request.user, issue=issue))
        if not votes:
            return Response({'detail': 'You have not voted on this issue.'}, status=400)
        for v in votes:
            v.delete()
        issue.refresh_from_db()
        return Response({'detail': 'Vote removed.', 'upvote_count': issue.upvote_count})


class VoteLogAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        issue = get_object_or_404(Issue, pk=pk)
        from voting.models import Vote
        votes = Vote.objects.filter(issue=issue).select_related('blockchain_log')
        logs = []
        for v in votes:
            try:
                bl = v.blockchain_log
                logs.append({
                    'vote_id': v.id,
                    'voter': v.user.username,
                    'timestamp': str(v.created_at),
                    'vote_hash': bl.vote_hash,
                    'previous_hash': bl.previous_hash,
                })
            except Exception:
                pass
        return Response({'issue_id': pk, 'vote_count': issue.upvote_count, 'blockchain_log': logs})


class CommentAPIView(generics.CreateAPIView):
    serializer_class = IssueCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        issue = get_object_or_404(Issue, pk=self.kwargs['pk'])
        serializer.save(author=self.request.user, issue=issue)


_CATEGORY_LABELS = {
    'hy': {'road': 'Ճանապարհ', 'water': 'Ջուր', 'electricity': 'Էլեկտրաէներգիա',
           'waste': 'Աղբ', 'safety': 'Անվտանգություն', 'other': 'Այլ'},
    'en': {'road': 'Road', 'water': 'Water', 'electricity': 'Electricity',
           'waste': 'Waste', 'safety': 'Safety', 'other': 'Other'},
    'fr': {'road': 'Route', 'water': 'Eau', 'electricity': 'Électricité',
           'waste': 'Déchets', 'safety': 'Sécurité', 'other': 'Autre'},
}
_STATUS_LABELS = {
    'hy': {'pending': 'Սպասվում է', 'under_review': 'Քննության փուլ',
           'in_progress': 'Ընթացքի մեջ', 'completed': 'Ավարտված', 'rejected': 'Մերժված'},
    'en': {'pending': 'Pending', 'under_review': 'Under Review',
           'in_progress': 'In Progress', 'completed': 'Completed', 'rejected': 'Rejected'},
    'fr': {'pending': 'En attente', 'under_review': 'En cours d\'examen',
           'in_progress': 'En cours', 'completed': 'Terminé', 'rejected': 'Rejeté'},
}
_AREA_LABELS = {
    'hy': {'city': 'Կապան քաղաք', 'village': 'Գյուղ'},
    'en': {'city': 'Kapan City', 'village': 'Village'},
    'fr': {'city': 'Ville de Kapan', 'village': 'Village'},
}


def _localized_choices(lang, choices, label_map):
    m = label_map.get(lang, label_map['en'])
    return [(val, m.get(val, val)) for val, _ in choices]


def issue_list_view(request):
    issues = Issue.objects.all()
    category = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    area = request.GET.get('area', '')
    search = request.GET.get('search', '')
    ordering = request.GET.get('ordering', '-created_at')
    if category:
        issues = issues.filter(category=category)
    if status_filter:
        issues = issues.filter(status=status_filter)
    if area:
        issues = issues.filter(area=area)
    if search:
        from django.db.models import Q
        issues = issues.filter(
            Q(title_hy__icontains=search) | Q(title_en__icontains=search) |
            Q(description_hy__icontains=search)
        )
    allowed_orderings = ['-created_at', 'created_at', '-upvote_count', 'upvote_count']
    if ordering in allowed_orderings:
        issues = issues.order_by(ordering)
    lang = (getattr(request, 'LANGUAGE_CODE', 'en') or 'en')[:2]
    context = {
        'issues': issues,
        'category_choices': _localized_choices(lang, Issue.CATEGORY_CHOICES, _CATEGORY_LABELS),
        'status_choices': _localized_choices(lang, Issue.STATUS_CHOICES, _STATUS_LABELS),
        'area_choices': _localized_choices(lang, Issue.AREA_CHOICES, _AREA_LABELS),
        'category_labels': _CATEGORY_LABELS.get(lang, _CATEGORY_LABELS['en']),
        'status_labels': _STATUS_LABELS.get(lang, _STATUS_LABELS['en']),
        'area_labels': _AREA_LABELS.get(lang, _AREA_LABELS['en']),
        'selected_category': category,
        'selected_status': status_filter,
        'selected_area': area,
        'search': search,
    }
    return render(request, 'issues/list.html', context)


def issue_detail_view(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    from voting.models import Vote
    user_voted = False
    if request.user.is_authenticated:
        user_voted = Vote.objects.filter(user=request.user, issue=issue).exists()
    comment_form = IssueCommentForm()
    if request.method == 'POST' and request.user.is_authenticated:
        action = request.POST.get('action')
        if action == 'vote':
            if not request.user.verified:
                messages.error(request, 'Only verified citizens can vote.')
            elif user_voted:
                messages.warning(request, 'You already voted on this issue.')
            else:
                Vote.objects.create(user=request.user, issue=issue)
                messages.success(request, 'Your vote has been recorded.')
                return redirect('issue_detail', pk=pk)
        elif action == 'unvote':
            vote_qs = Vote.objects.filter(user=request.user, issue=issue)
            for v in vote_qs:
                v.delete()
            messages.success(request, 'Your vote has been removed.')
            return redirect('issue_detail', pk=pk)
        elif action == 'comment':
            comment_form = IssueCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.author = request.user
                comment.issue = issue
                comment.save()
                messages.success(request, 'Comment added.')
                return redirect('issue_detail', pk=pk)
    lang = (getattr(request, 'LANGUAGE_CODE', 'en') or 'en')[:2]
    # Localize comment placeholder
    _CPH = {
        'hy': 'Թողնել մեկնաբանություն...',
        'fr': 'Écrire un commentaire...',
        'en': 'Write a comment...',
    }
    comment_form.fields['body'].widget.attrs['placeholder'] = _CPH.get(lang, _CPH['en'])
    # Localized status choices for timeline
    status_choices_localized = _localized_choices(lang, Issue.STATUS_CHOICES, _STATUS_LABELS)
    context = {
        'issue': issue,
        'user_voted': user_voted,
        'comment_form': comment_form,
        'status_history': issue.status_history.all(),
        'comments': issue.comments.all(),
        'status_choices_localized': status_choices_localized,
        'category_labels': _CATEGORY_LABELS.get(lang, _CATEGORY_LABELS['en']),
        'status_labels': _STATUS_LABELS.get(lang, _STATUS_LABELS['en']),
        'area_labels': _AREA_LABELS.get(lang, _AREA_LABELS['en']),
    }
    return render(request, 'issues/detail.html', context)


@citizen_required
def issue_new_view(request):
    lang = (getattr(request, 'LANGUAGE_CODE', 'en') or 'en')[:2]
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            # Save additional uploaded images
            for img_file in request.FILES.getlist('extra_images'):
                IssueImage.objects.create(issue=issue, image=img_file)
            messages.success(request, 'Issue reported successfully!')
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = IssueForm()
    # Localize area dropdown choices
    area_labels = _AREA_LABELS.get(lang, _AREA_LABELS['en'])
    form.fields['area'].choices = [('', '---')] + [
        (val, area_labels.get(val, val)) for val, _ in Issue.AREA_CHOICES
    ]
    # Localize form placeholders
    _PH = {
        'hy': {
            'title':    'Վերնագիր...',
            'desc':     'Նկարագրություն...',
            'address':  'Նշեք հասցեն...',
            'village':  'Բնակավայրի անվանումը...',
        },
        'en': {
            'title':    'Title the issue...',
            'desc':     'Describe the issue in detail...',
            'address':  'Enter street address or landmark...',
            'village':  'Village name...',
        },
        'fr': {
            'title':    'Donnez un titre au problème...',
            'desc':     'Décrivez le problème en détail...',
            'address':  'Adresse ou point de repère...',
            'village':  'Nom du village...',
        },
    }
    ph = _PH.get(lang, _PH['en'])
    form.fields['title_hy'].widget.attrs['placeholder'] = ph['title']
    form.fields['description_hy'].widget.attrs['placeholder'] = ph['desc']
    form.fields['location_address'].widget.attrs['placeholder'] = ph['address']
    form.fields['village_name'].widget.attrs['placeholder'] = ph['village']
    return render(request, 'issues/new.html', {'form': form})


def map_view(request):
    lang = (getattr(request, 'LANGUAGE_CODE', 'en') or 'en')[:2]
    return render(request, 'issues/map.html', {
        'category_choices': _localized_choices(lang, Issue.CATEGORY_CHOICES, _CATEGORY_LABELS),
        'status_choices': _localized_choices(lang, Issue.STATUS_CHOICES, _STATUS_LABELS),
        'area_choices': _localized_choices(lang, Issue.AREA_CHOICES, _AREA_LABELS),
    })


def home_view(request):
    recent_issues = Issue.objects.order_by('-created_at')[:6]
    top_issues = Issue.objects.order_by('-upvote_count')[:6]
    total_issues = Issue.objects.count()
    resolved_issues = Issue.objects.filter(status='completed').count()
    lang = (getattr(request, 'LANGUAGE_CODE', 'en') or 'en')[:2]
    context = {
        'recent_issues': recent_issues,
        'top_issues': top_issues,
        'total_issues': total_issues,
        'resolved_issues': resolved_issues,
        'category_choices': _localized_choices(lang, Issue.CATEGORY_CHOICES, _CATEGORY_LABELS),
        'status_choices': _localized_choices(lang, Issue.STATUS_CHOICES, _STATUS_LABELS),
    }
    return render(request, 'home.html', context)
