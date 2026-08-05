from django.db import models
import uuid


class UserRole(models.TextChoices):
    STUDENT = 'Student', 'Student'
    TEACHER = 'Teacher', 'Teacher'
    TRAINER = 'Trainer', 'Trainer'
    ADMIN = 'Admin', 'Admin'


class UserProfile(models.Model):
    """
    Standard Django Model representation of a User Document in MongoDB.
    Serves as an architectural template and supports optional Django ORM features.
    """
    id = models.CharField(max_length=255, primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True, default='')
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(
        max_length=50,
        choices=UserRole.choices,
        default=UserRole.STUDENT
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.full_name} ({self.role}) - {self.email}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()