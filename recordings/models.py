import uuid
from django.db import models
from django.contrib.auth import get_user_model
from classroom.models import ClassroomSession

User = get_user_model()


class Recording(models.Model):
    STATUS_CHOICES = (
        ('Pending Upload', 'Pending Upload'),
        ('Processing', 'Processing'),
        ('Encoding Completed', 'Encoding Completed'),
        ('Ready', 'Ready for Playback'),
        ('Failed', 'Failed Processing'),
    )

    VISIBILITY_CHOICES = (
        ('Public Batch', 'Public Batch'),
        ('Private Trainer', 'Private Trainer'),
    )

    # Primary Key & References
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ClassroomSession,
        on_delete=models.CASCADE,
        related_name='recordings',
        null=True,
        blank=True
    )
    batch_id = models.CharField(max_length=100, db_index=True)
    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trainer_recordings'
    )

    # Details & Media Metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    video_url = models.URLField(max_length=500, help_text="Video File URL or Storage Path")
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")

    # Workflow & Lifecycle
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending Upload')
    recording_start_time = models.DateTimeField(null=True, blank=True)
    recording_end_time = models.DateTimeField(null=True, blank=True)
    recording_date = models.DateField(auto_now_add=True)

    # Playback Settings & Visibility
    playback_count = models.PositiveIntegerField(default=0)
    download_enabled = models.BooleanField(default=False)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='Public Batch')

    # Soft Delete Support
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"


class RecordingAnalytics(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, related_name='analytics')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    watch_duration = models.PositiveIntegerField(default=0, help_text="Watch duration in seconds")
    last_viewed_at = models.DateTimeField(auto_now=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('recording', 'user')

    def __str__(self):
        return f"{self.user} viewing {self.recording.title}"