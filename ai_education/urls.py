from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🛡️ Authentication Routes
    path('api/auth/', include('authentication.urls')),

    # 📝 Attendance Routes
    path('api/attendance/', include('attendance.urls')),
]