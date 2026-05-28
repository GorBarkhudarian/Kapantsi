from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListAPIView.as_view(), name='api_notifications'),
    path('read/', views.MarkReadAPIView.as_view(), name='api_notifications_read_all'),
    path('<int:pk>/read/', views.MarkReadAPIView.as_view(), name='api_notification_read'),
]
