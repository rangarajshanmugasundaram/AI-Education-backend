from django.urls import path
from .views import (
    UserListCreateView,
    UserDetailView,
    UserToggleStatusView,
    UserResetPasswordView
)

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('<str:user_id>/toggle-status/', UserToggleStatusView.as_view(), name='user-toggle-status'),
    path('<str:user_id>/reset-password/', UserResetPasswordView.as_view(), name='user-reset-password'),
]