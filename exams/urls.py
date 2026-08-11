from django.urls import path
from .views import (
    ExamListCreateView,
    ExamDetailView,
    ExamPublishToggleView,
    ExamSubmitView,
    ExamResultsSummaryView,
    ExamAnalyticsView
)

urlpatterns = [
    # Exam CRUD
    path('', ExamListCreateView.as_view(), name='exam-list-create'),
    path('<str:exam_id>/', ExamDetailView.as_view(), name='exam-detail'),

    # Status & Publishing Toggles
    path('<str:exam_id>/publish/', ExamPublishToggleView.as_view(), name='exam-publish-toggle'),

    # Student Submissions
    path('<str:exam_id>/submit/', ExamSubmitView.as_view(), name='exam-submit'),

    # Analytics & Results
    path('<str:exam_id>/results/', ExamResultsSummaryView.as_view(), name='exam-results-summary'),
    path('<str:exam_id>/analytics/', ExamAnalyticsView.as_view(), name='exam-analytics'),
]