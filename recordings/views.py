from rest_framework import viewsets, status, filters
from db_connection import db
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Max
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Recording, RecordingAnalytics
from .serializers import RecordingSerializer, RecordingUpdateSerializer, RecordingStatusUpdateSerializer
from .permissions import IsTrainerOrAdminForWrite
from .services import RecordingService

User = get_user_model()
recordings_collection = db['recordings']


class RecordingViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.filter(is_deleted=False)
    serializer_class = RecordingSerializer
    permission_classes = [IsTrainerOrAdminForWrite]

    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'duration', 'playback_count']
    ordering = ['-created_at']

    def _get_request_user(self, request):
        if request.user and request.user.is_authenticated:
            return request.user
        email_header = request.headers.get('X-User-Email')
        if email_header:
            return User.objects.filter(email__iexact=email_header.strip()).first()
        return None

    def get_queryset(self):
        qs = super().get_queryset()
        user = self._get_request_user(self.request)
        role = str(getattr(user, 'role', 'Student')).title() if user else 'Student'

        # Query Filters
        batch_id = self.request.query_params.get('batch_id')
        trainer_id = self.request.query_params.get('trainer_id')
        session_id = self.request.query_params.get('session_id')
        rec_status = self.request.query_params.get('status')

        if batch_id:
            qs = qs.filter(batch_id=batch_id)
        if trainer_id:
            qs = qs.filter(trainer_id=trainer_id)
        if session_id:
            qs = qs.filter(session_id=session_id)
        if rec_status:
            qs = qs.filter(status=rec_status)

        # RBAC Visibility Rules for Students
        if role == 'Student':
            qs = qs.filter(visibility='Public Batch', status='Ready')

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self._get_request_user(self.request) or User.objects.first()
        recording_instance = serializer.save(trainer=user)

        # Write to MongoDB
        try:
            recordings_collection.insert_one({
                "_id": str(recording_instance.id),
                "session_id": str(recording_instance.session.id) if recording_instance.session else None,
                "batch_id": recording_instance.batch_id,
                "trainer_id": str(getattr(user, 'id', '')),
                "trainer_email": getattr(user, 'email', ''),
                "title": recording_instance.title,
                "description": recording_instance.description,
                "video_url": recording_instance.video_url,
                "thumbnail_url": recording_instance.thumbnail_url,
                "duration": recording_instance.duration,
                "file_size": recording_instance.file_size,
                "status": recording_instance.status,
                "visibility": recording_instance.visibility,
                "download_enabled": recording_instance.download_enabled,
                "playback_count": 0,
                "is_deleted": False,
                "created_at": recording_instance.created_at.isoformat(),
            })
            print("🟢 Document successfully saved to MongoDB!")
        except Exception as e:
            print(f"⚠️ MongoDB write error: {e}")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Sync update to MongoDB
        try:
            recordings_collection.update_one(
                {"_id": str(instance.id)},
                {"$set": {
                    "title": instance.title,
                    "description": instance.description,
                    "visibility": instance.visibility,
                    "thumbnail_url": instance.thumbnail_url,
                    "download_enabled": instance.download_enabled,
                    "updated_at": timezone.now().isoformat()
                }}
            )
        except Exception as e:
            print(f"MongoDB update sync error: {e}")

        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RecordingUpdateSerializer
        return RecordingSerializer

    def destroy(self, request, *args, **kwargs):
        recording = self.get_object()
        permanent = request.query_params.get('permanent', 'false').lower() == 'true'

        if permanent:
            try:
                recordings_collection.delete_one({"_id": str(recording.id)})
            except Exception as e:
                print(f"MongoDB delete error: {e}")
            recording.delete()
            return Response({"detail": "Recording permanently deleted."}, status=status.HTTP_204_NO_CONTENT)

        recording.is_deleted = True
        recording.deleted_at = timezone.now()
        recording.save()

        try:
            recordings_collection.update_one(
                {"_id": str(recording.id)},
                {"$set": {"is_deleted": True, "deleted_at": recording.deleted_at.isoformat()}}
            )
        except Exception as e:
            print(f"MongoDB soft-delete update error: {e}")

        return Response({"detail": "Recording soft deleted."}, status=status.HTTP_200_OK)

    # 🌟 Workflow status update
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        recording = self.get_object()
        serializer = RecordingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        recording.status = new_status
        recording.save(update_fields=['status', 'updated_at'])

        try:
            recordings_collection.update_one(
                {"_id": str(recording.id)},
                {"$set": {"status": new_status}}
            )
        except Exception as e:
            print(f"MongoDB status update error: {e}")

        return Response({'status': recording.status, 'detail': 'Workflow status updated successfully.'})

    # 🌟 Secure Playback Token Generation
    @action(detail=True, methods=['get'], url_path='playback-token')
    def get_playback_token(self, request, pk=None):
        recording = self.get_object()
        user = self._get_request_user(request)
        token = RecordingService.generate_playback_token(user, recording)

        watch_seconds = int(request.query_params.get('watch_seconds', 0))
        RecordingService.track_view(user, recording, watch_seconds=watch_seconds)

        return Response({
            'recording_id': str(recording.id),
            'token': token,
            'playback_url': recording.video_url,
            'download_enabled': recording.download_enabled,
            'expires_in_seconds': 7200
        }, status=status.HTTP_200_OK)

    # 🌟 Track Download API
    @action(detail=True, methods=['post'], url_path='track-download')
    def track_download(self, request, pk=None):
        recording = self.get_object()
        if not recording.download_enabled:
            return Response({'error': 'Downloads are disabled for this recording.'}, status=status.HTTP_403_FORBIDDEN)

        user = self._get_request_user(request)
        RecordingService.track_download(user, recording)
        return Response({'detail': 'Download recorded successfully.'}, status=status.HTTP_200_OK)

    # 🌟 Recording Analytics Endpoint
    @action(detail=True, methods=['get'], url_path='analytics')
    def get_recording_analytics(self, request, pk=None):
        recording = self.get_object()
        analytics_qs = RecordingAnalytics.objects.filter(recording=recording)

        unique_viewers = analytics_qs.count()
        total_duration = analytics_qs.aggregate(Sum('watch_duration'))['watch_duration__sum'] or 0
        total_downloads = analytics_qs.aggregate(Sum('download_count'))['download_count__sum'] or 0
        last_viewed = analytics_qs.aggregate(Max('last_viewed_at'))['last_viewed_at__max']

        return Response({
            'recording_id': str(recording.id),
            'total_views': recording.playback_count,
            'unique_viewers': unique_viewers,
            'total_watch_duration_seconds': total_duration,
            'download_count': total_downloads,
            'last_viewed_at': last_viewed.isoformat() if last_viewed else None
        }, status=status.HTTP_200_OK)

    # 🌟 Most Viewed Recording API
    @action(detail=False, methods=['get'], url_path='most-viewed')
    def get_most_viewed(self, request):
        most_viewed = Recording.objects.filter(is_deleted=False).order_by('-playback_count').first()
        if not most_viewed:
            return Response({'detail': 'No recordings found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(most_viewed)
        return Response(serializer.data, status=status.HTTP_200_OK)