from django.db import models


# If using PyMongo directly with db_connection.py, MongoDB handles collections dynamically.
# Optional ORM Model fallback:
class Notification(models.Model):
  title = models.CharField(max_length=255)
  message = models.TextField()
  sender_id = models.EmailField()
  sender_role = models.CharField(max_length=50, default='Trainer')
  recipient_type = models.CharField(
      max_length=20,
      choices=[('All', 'All'), ('Batch', 'Batch'), ('User', 'User')],
      default='All',
  )
  recipient_id = models.CharField(max_length=255, null=True, blank=True)
  batch_id = models.CharField(max_length=255, null=True, blank=True)
  priority = models.CharField(
      max_length=10,
      choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
      default='Medium',
  )
  read_status = models.BooleanField(default=False)
  is_deleted = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.title} - {self.recipient_type}'