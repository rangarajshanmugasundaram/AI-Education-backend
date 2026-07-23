from rest_framework import serializers
from .models import ClassroomSession, Participant, WaitingRoomUser, ActivityLog

class ParticipantSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'name', 'email', 'role', 'status',
            'is_muted', 'is_camera_on', 'has_raised_hand', 'permissions'
        ]

    def get_permissions(self, obj):
        return {
            "canSpeak": obj.can_speak,
            "canChat": obj.can_chat,
            "canScreenShare": obj.can_screen_share
        }


class WaitingRoomUserSerializer(serializers.ModelSerializer):
    requestedAt = serializers.SerializerMethodField()

    class Meta:
        model = WaitingRoomUser
        fields = ['id', 'name', 'email', 'requestedAt']

    def get_requestedAt(self, obj):
        return obj.requested_at.strftime("%I:%M %p")


class ActivityLogSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'timestamp']

    def get_timestamp(self, obj):
        return obj.timestamp.strftime("%H:%M:%S")


class ClassroomSessionSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    waitingRoom = WaitingRoomUserSerializer(source='waiting_users', many=True, read_only=True)
    activityLogs = ActivityLogSerializer(source='logs', many=True, read_only=True)

    class Meta:
        model = ClassroomSession
        fields = [
            'id', 'title', 'is_live', 'is_locked', 'allow_unmute',
            'participants', 'waitingRoom', 'activityLogs'
        ]