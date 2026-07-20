from django.urls import path
from .views import (
    MarkAttendanceView,
    GetSessionAttendanceView,
    GetStudentAttendanceView,
    UpdateAttendanceView,
    GetSessionAttendanceReportView,
    GetStudentAttendanceReportView
)

urlpatterns = [
    path('mark', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('session/<str:session_id>', GetSessionAttendanceView.as_view(), name='session-attendance'),
    path('student/<str:student_id>', GetStudentAttendanceView.as_view(), name='student-attendance'),
    path('update', UpdateAttendanceView.as_view(), name='update-attendance'),
    path('report/<str:session_id>', GetSessionAttendanceReportView.as_view(), name='session-report'),
    path('student-report/<str:student_id>', GetStudentAttendanceReportView.as_view(), name='student-report'),
]