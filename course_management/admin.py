from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'category', 'status', 'is_archived', 'created_at')
    list_filter = ('status', 'is_archived', 'category')
    search_fields = ('title', 'code', 'category', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')