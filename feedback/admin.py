from django.contrib import admin
from .models import SessionFeedback

@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'student_id', 'trainer_id', 'rating', 'tags', 'created_at')
    list_filter = ('rating', 'tags', 'created_at')
    search_fields = ('session_id', 'student_id', 'trainer_id', 'review')