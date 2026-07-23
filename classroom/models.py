import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ClassroomSession(models.Model):
    id = models.CharField(max_length=100, primary_key=True, default="session_101")
    title = models.CharField(max_length=255, default="Live Interactive Class")
    is_live = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    allow_unmute = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.id})"


class Participant(models.Model):
    ROLE_CHOICES = (
        ('Trainer', 'Trainer'),
        ('Student', 'Student'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Disconnected', 'Disconnected'),
        ('Removed', 'Removed'),
    )

    session = models.ForeignKey(ClassroomSession, related_name="participants", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Student')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    is_muted = models.BooleanField(default=True)
    is_camera_on = models.BooleanField(default=False)
    has_raised_hand = models.BooleanField(default=False)

    # Permissions stored as JSON
    can_speak = models.BooleanField(default=True)
    can_chat = models.BooleanField(default=True)
    can_screen_share = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'email')

    def __str__(self):
        return f"{self.name} - {self.session.id}"


class WaitingRoomUser(models.Model):
    session = models.ForeignKey(ClassroomSession, related_name="waiting_users", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} waiting for {self.session.id}"


class ActivityLog(models.Model):
    session = models.ForeignKey(ClassroomSession, related_name="logs", on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']