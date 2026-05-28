from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.DashboardStatsAPIView.as_view(), name='api_dashboard_stats'),
]
