from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from .models import Recording, RecordingAnalytics
from classroom.models import ClassroomSession
from django.contrib.auth import get_user_model

User = get_user_model()


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A duplicate resource already exists.'
    default_code = 'conflict'


class RecordingSerializer(serializers.ModelSerializer):
    trainer_name = serializers.ReadOnlyField(source='trainer.get_full_name')

    class Meta:
        model = Recording
        fields = [
            'id', 'session', 'batch_id', 'trainer', 'trainer_name', 'title',
            'description', 'video_url', 'thumbnail_url', 'duration', 'file_size',
            'status', 'recording_start_time', 'recording_end_time', 'recording_date',
            'playback_count', 'download_enabled', 'visibility', 'is_deleted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'trainer', 'playback_count', 'is_deleted', 'created_at', 'updated_at']

    def validate_session(self, value):
        if value and not ClassroomSession.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Referenced Classroom Session does not exist.")
        return value

    def validate_trainer(self, value):
        if value and not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Referenced Trainer does not exist.")
        return value

    def validate(self, attrs):
        session = attrs.get('session')
        title = attrs.get('title')

        # 🌟 Duplicate check per session & title (Requirement 6 - HTTP 409 Conflict)
        if self.instance is None and session:
            if Recording.objects.filter(session=session, title=title, is_deleted=False).exists():
                raise ConflictException({"detail": "A recording with this title already exists for this session."})

        return attrs


class RecordingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recording
        fields = ['title', 'description', 'visibility', 'thumbnail_url', 'download_enabled']


class RecordingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['Pending Upload', 'Processing', 'Encoding Completed', 'Ready', 'Failed'])


class PlaybackTokenSerializer(serializers.Serializer):
    recording_id = serializers.UUIDField()
    token = serializers.CharField()
    playback_url = serializers.CharField()
    download_enabled = serializers.BooleanField()
    expires_in_seconds = serializers.IntegerField()


class AnalyticsSummarySerializer(serializers.Serializer):
    recording_id = serializers.UUIDField()
    total_views = serializers.IntegerField()
    unique_viewers = serializers.IntegerField()
    total_watch_duration = serializers.IntegerField()
    download_count = serializers.IntegerField()
    most_viewed_recording = serializers.DictField(required=False)