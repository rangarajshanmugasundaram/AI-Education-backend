from django.contrib import admin
from db_connection import db


@admin.register
class AssignmentMongoAdmin(admin.ModelAdmin):
    """Custom Administrative Interface for inspecting MongoDB assignments collection."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Pure MongoDB Admin Dashboard Integration
try:
    from .models import AssignmentModel

    @admin.register(AssignmentModel)
    class AssignmentAdmin(admin.ModelAdmin):
        list_display = ('title', 'batch_code', 'due_date', 'total_marks', 'status', 'created_at')
        list_filter = ('status', 'batch_code')
        search_fields = ('title', 'batch_code', 'course_name')
except ImportError:
    # Using PyMongo directly without SQLite ORM models
    pass