from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('issues/', views.issue_list_view, name='issue_list'),
    path('issues/new/', views.issue_new_view, name='issue_new'),
    path('issues/<int:pk>/', views.issue_detail_view, name='issue_detail'),
    path('map/', views.map_view, name='map'),
]
