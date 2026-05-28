from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.citizen_dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/delete/<int:pk>/', views.admin_delete_issue_view, name='admin_delete_issue'),
]
