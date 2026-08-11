from django.contrib import admin
from db_connection import db


class ExamMongoAdminSite:
    """Provides MongoDB summary inspection inside Django Admin custom dashboard."""
    pass


# Optional SQLite ORM model registration if using Django ORM alongside MongoDB
try:
    from .models import ExamModel


    @admin.register(ExamModel)
    class ExamAdmin(admin.ModelAdmin):
        list_display = ('title', 'batch_code', 'duration_minutes', 'total_marks', 'status', 'created_at')
        list_filter = ('status', 'batch_code')
        search_fields = ('title', 'batch_code')
except ImportError:
    # If using MongoDB exclusively without SQLite ORM models
    pass