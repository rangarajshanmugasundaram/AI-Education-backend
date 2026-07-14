from django.urls import path
from .views import MarkAttendanceView, GetSessionAttendanceView, GetStudentAttendanceView, UpdateAttendanceView

urlpatterns = [
    path('mark', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('session/<str:session_id>', GetSessionAttendanceView.as_view(), name='session-attendance'),
    path('student/<str:student_id>', GetStudentAttendanceView.as_view(), name='student-attendance'),
    path('update', UpdateAttendanceView.as_view(), name='update-attendance'),
]