from django.db import models


class Batch(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Upcoming', 'Upcoming'),
        ('Completed', 'Completed'),
        ('Archived', 'Archived'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    course_id = models.CharField(max_length=100, blank=True, null=True)
    trainer_id = models.CharField(max_length=100, blank=True, null=True)
    max_capacity = models.IntegerField(default=30)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"