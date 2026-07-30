import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework.exceptions import PermissionDenied, NotFound
from .models import Recording, RecordingAnalytics
from db_connection import db

recordings_collection = db['recordings']


class RecordingService:

    @staticmethod
    def generate_playback_token(user, recording: Recording):
        """Generates a secure signed JWT playback token valid for 2 hours."""
        if recording.status != 'Ready':
            raise PermissionDenied("Recording is not ready for playback.")

        # Batch access check logic hook
        user_batch = getattr(user, 'batch_id', None) if user else None
        user_role = str(getattr(user, 'role', '')).title() if user else 'Student'

        if recording.visibility == 'Public Batch' and user_batch and user_batch != recording.batch_id:
            if not (getattr(user, 'is_staff', False) or user_role == 'Admin'):
                raise PermissionDenied("You are not enrolled in this batch.")

        payload = {
            'recording_id': str(recording.id),
            'user_id': str(user.id) if user else 'anonymous',
            'download_enabled': recording.download_enabled,
            'exp': datetime.now(timezone.utc) + timedelta(hours=2)
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token

    @staticmethod
    def track_view(user, recording: Recording, watch_seconds: int = 0):
        """Tracks playback events in relational DB and MongoDB simultaneously."""
        recording.playback_count += 1
        recording.save(update_fields=['playback_count'])

        # 1. Update Django Relational Analytics
        if user:
            analytics_obj, created = RecordingAnalytics.objects.get_or_create(
                recording=recording,
                user=user,
                defaults={'watch_duration': watch_seconds}
            )
            if not created:
                analytics_obj.watch_duration += watch_seconds
                analytics_obj.save()

        # 2. 🌟 Sync Analytics to MongoDB Collection (Requirement 5)
        try:
            user_email = getattr(user, 'email', 'anonymous@ai-edu.com') if user else 'anonymous@ai-edu.com'
            recordings_collection.update_one(
                {"_id": str(recording.id)},
                {
                    "$inc": {"playback_count": 1, "total_watch_duration": watch_seconds},
                    "$addToSet": {"unique_viewers": user_email},
                    "$set": {"last_viewed_at": datetime.now(timezone.utc).isoformat()}
                }
            )
        except Exception as e:
            print(f"MongoDB analytics sync error: {e}")

    @staticmethod
    def track_download(user, recording: Recording):
        """🌟 Tracks download count in MongoDB and Relational DB (Requirement 5)."""
        if not recording.download_enabled:
            raise PermissionDenied("Downloads are not enabled for this recording.")

        if user:
            analytics_obj, _ = RecordingAnalytics.objects.get_or_create(recording=recording, user=user)
            analytics_obj.download_count = getattr(analytics_obj, 'download_count', 0) + 1
            analytics_obj.save()

        try:
            recordings_collection.update_one(
                {"_id": str(recording.id)},
                {"$inc": {"download_count": 1}}
            )
        except Exception as e:
            print(f"MongoDB download count update error: {e}")