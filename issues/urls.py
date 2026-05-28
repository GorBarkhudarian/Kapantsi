from django.urls import path
from . import views

urlpatterns = [
    path('', views.IssueListCreateAPIView.as_view(), name='api_issues'),
    path('<int:pk>/', views.IssueDetailAPIView.as_view(), name='api_issue_detail'),
    path('<int:pk>/vote/', views.VoteAPIView.as_view(), name='api_vote'),
    path('<int:pk>/votes/', views.VoteLogAPIView.as_view(), name='api_vote_log'),
    path('<int:pk>/comment/', views.CommentAPIView.as_view(), name='api_comment'),
]
