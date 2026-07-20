from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🛡️ Authentication Routes (Updated path from api/auth/ to api/)
    path('api/', include('authentication.urls')),

    # 📝 Attendance Routes
    path('api/attendance/', include('attendance.urls')),

    # 💬 Chat System Routes
    path('api/chat/', include('chat.urls')),

    # 🎨 Whiteboard Collaboration Routes
    path('api/whiteboard/', include('whiteboard.urls')),
]