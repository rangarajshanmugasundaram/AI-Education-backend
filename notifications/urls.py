from django.urls import path
from .views import (
    MarkNotificationReadView,
    MyNotificationsView,
    NotificationDetailView,
    NotificationListCreateView,
)

urlpatterns = [
    # API Endpoints
    path('', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('my/', MyNotificationsView.as_view(), name='my-notifications'),
    path('<str:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<str:pk>/read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
]