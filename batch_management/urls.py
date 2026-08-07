from django.urls import path
from .views import (
    BatchListCreateView,
    BatchDetailView,
    AllocateStudentsView,
    AllocateTrainerView,
    BatchStatsView
)

urlpatterns = [
    path('', BatchListCreateView.as_view(), name='batch-list-create'),
    path('stats/', BatchStatsView.as_view(), name='batch-stats-global'),
    path('<str:batch_id>/', BatchDetailView.as_view(), name='batch-detail'),
    path('<str:batch_id>/allocate-students/', AllocateStudentsView.as_view(), name='batch-allocate-students'),
    path('<str:batch_id>/allocate-trainer/', AllocateTrainerView.as_view(), name='batch-allocate-trainer'),
]