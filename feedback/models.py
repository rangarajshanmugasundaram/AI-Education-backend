from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class SessionFeedback(models.Model):
    TAG_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('Poor', 'Poor'),
    ]

    session_id = models.CharField(max_length=100, db_index=True)
    student_id = models.CharField(max_length=100, db_index=True)
    trainer_id = models.CharField(max_length=100, db_index=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=50, choices=TAG_CHOICES, blank=True, default='Good')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_feedback'
        # 🌟 Prevents duplicate feedback from the same student for the same session
        unique_together = ('session_id', 'student_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_id} - {self.session_id} - Rating: {self.rating}"