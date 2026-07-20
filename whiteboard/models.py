# whiteboard/models.py
from django.db import models

class Whiteboard(models.Model):
    class Meta:
        managed = False  # Tells Django to ignore this in SQLite migrations