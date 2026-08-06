from django.db import models


class Course(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Upcoming', 'Upcoming'),
        ('Completed', 'Completed'),
        ('Archived', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, default='General')
    description = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    prerequisites = models.TextField(blank=True, null=True)
    trainer_id = models.CharField(max_length=100, blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.title}"