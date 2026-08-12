from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🛡️ Authentication Routes
    path('api/', include('authentication.urls')),

    # 📊 Admin Dashboard Route 
    path('api/admin/', include('admin_dashboard.urls')),

    # 👥 User Management Routes
    path('api/users/', include('user_management.urls')),

    # 📚 Course Management Routes
    path('api/courses/', include('course_management.urls')),

    # 🎓 Batch Management Routes
    path('api/batches/', include('batch_management.urls')),

    # 📝 Exam Management Routes
    path('api/exams/', include('exams.urls')),

    # 📌 Assignment Management Routes
    path('api/assignments/', include('assignments.urls')),

    # 📝 Attendance Routes
    path('api/attendance/', include('attendance.urls')),

    # 💬 Chat System Routes
    path('api/chat/', include('chat.urls')),

    # 🎨 Whiteboard Collaboration Routes
    path('api/whiteboard/', include('whiteboard.urls')),

    # 🏫 Live Classroom Engine Routes
    path('api/classroom/', include('classroom.urls')),

    # 📢 Notification Management System Routes
    path('api/notifications/', include('notifications.urls')),

    # ⭐ Session Feedback & Rating System Routes
    path('api/feedback/', include('feedback.urls')),

    # 🎬 Session Recording Management & Playback Routes
    path('api/recordings/', include('recordings.urls')),
]