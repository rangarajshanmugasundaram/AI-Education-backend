from django.contrib import admin
from .models import ClassroomSession, Participant, WaitingRoomUser, ActivityLog


@admin.register(ClassroomSession)
class ClassroomSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_live', 'is_locked', 'created_at')
    list_filter = ('is_live', 'is_locked')
    search_fields = ('id', 'title')


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'status', 'session', 'is_muted', 'is_camera_on', 'has_raised_hand')
    list_filter = ('role', 'status', 'is_muted', 'is_camera_on', 'has_raised_hand')
    search_fields = ('name', 'email')


@admin.register(WaitingRoomUser)
class WaitingRoomUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'session', 'requested_at')
    search_fields = ('name', 'email')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('session', 'action', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('action',)