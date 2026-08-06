from django.urls import path
from .views import (
    CourseListCreateView,
    CourseDetailView,
    CourseAssignTrainerView,
    CourseArchiveView,
    CourseStatsView
)

urlpatterns = [
    path('', CourseListCreateView.as_view(), name='course-list-create'),
    path('stats/', CourseStatsView.as_view(), name='course-stats-global'),
    path('<str:course_id>/', CourseDetailView.as_view(), name='course-detail'),
    path('<str:course_id>/assign-trainer/', CourseAssignTrainerView.as_view(), name='course-assign-trainer'),
    path('<str:course_id>/archive/', CourseArchiveView.as_view(), name='course-archive'),
    path('<str:course_id>/stats/', CourseStatsView.as_view(), name='course-stats'),
]