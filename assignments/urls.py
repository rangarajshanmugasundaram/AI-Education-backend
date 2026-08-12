from django.urls import path
from .views import (
    AssignmentListCreateView,
    AssignmentDetailView,
    AssignmentStatusToggleView,
    AssignmentSubmitView,
    AssignmentSubmissionsRosterView,
    GradeSubmissionView,
    AssignmentAnalyticsView
)

urlpatterns = [
    # Assignment Management Endpoints
    path('', AssignmentListCreateView.as_view(), name='assignment-list-create'),
    path('<str:assignment_id>/', AssignmentDetailView.as_view(), name='assignment-detail'),

    # Status Toggles (Draft, Published, Open, Closed)
    path('<str:assignment_id>/status/', AssignmentStatusToggleView.as_view(), name='assignment-status-toggle'),

    # Student Submissions & Automated Late Checks
    path('<str:assignment_id>/submit/', AssignmentSubmitView.as_view(), name='assignment-submit'),

    # Submissions Roster & Manual Evaluation
    path('<str:assignment_id>/submissions/', AssignmentSubmissionsRosterView.as_view(),
         name='assignment-submissions-roster'),
    path('submissions/<str:submission_id>/grade/', GradeSubmissionView.as_view(), name='grade-submission'),

    # Performance Analytics
    path('<str:assignment_id>/analytics/', AssignmentAnalyticsView.as_view(), name='assignment-analytics'),
]