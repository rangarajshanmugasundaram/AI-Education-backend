from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🛡️ Authentication Routes
    path('api/', include('authentication.urls')),

    # 📝 Attendance Routes
    path('api/attendance/', include('attendance.urls')),

    # 💬 Chat System Routes
    path('api/chat/', include('chat.urls')),

    # 🎨 Whiteboard Collaboration Routes
    path('api/whiteboard/', include('whiteboard.urls')),

    # 🏫 Live Classroom Engine Routes (Tasks 1-10)
    path('api/classroom/', include('classroom.urls')),

    # 📢 Notification Management System Routes
    path('api/notifications/', include('notifications.urls')),
]