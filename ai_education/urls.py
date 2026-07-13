from django.contrib import admin
from django.urls import path
from users.views import (
    RegisterView, LoginView, ForgotPasswordView, ResetPasswordView,
    MarkAttendanceView, GetSessionAttendanceView, GetStudentAttendanceView, UpdateAttendanceView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🛡️ Authentication Endpoints (Class-Based APIView matching views.py)
    path('api/users/register', RegisterView.as_view(), name='register'),
    path('api/users/login', LoginView.as_view(), name='login'),
    path('api/users/forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/users/reset-password', ResetPasswordView.as_view(), name='reset-password'),

    # 📝 Attendance Endpoints
    path('api/attendance/mark', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('api/attendance/session/<str:session_id>', GetSessionAttendanceView.as_view(), name='session-attendance'),
    path('api/attendance/student/<str:student_id>', GetStudentAttendanceView.as_view(), name='student-attendance'),
    path('api/attendance/update', UpdateAttendanceView.as_view(), name='update-attendance'),
]