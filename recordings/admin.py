from django.contrib import admin
from .models import Recording, RecordingAnalytics


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'trainer',
        'batch_id',
        'status',
        'visibility',
        'playback_count',
        'download_enabled',
        'is_deleted',
        'created_at',
    )
    list_filter = (
        'status',
        'visibility',
        'download_enabled',
        'is_deleted',
        'created_at',
    )
    search_fields = (
        'title',
        'description',
        'batch_id',
        'trainer__username',
        'trainer__email',
    )
    readonly_fields = ('id', 'playback_count', 'deleted_at', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'session', 'batch_id', 'trainer', 'title', 'description')
        }),
        ('Media Files', {
            'fields': ('video_url', 'thumbnail_url', 'duration', 'file_size')
        }),
        ('Workflow & Visibility', {
            'fields': ('status', 'visibility', 'download_enabled', 'playback_count')
        }),
        ('Timestamps & Soft Delete', {
            'fields': ('recording_start_time', 'recording_end_time', 'recording_date', 'is_deleted', 'deleted_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(RecordingAnalytics)
class RecordingAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'recording',
        'user',
        'watch_duration',
        'download_count',
        'last_viewed_at',
    )
    search_fields = (
        'recording__title',
        'user__username',
        'user__email',
    )
    readonly_fields = ('last_viewed_at',)
    ordering = ('-last_viewed_at',)