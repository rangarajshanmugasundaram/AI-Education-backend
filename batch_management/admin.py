from django.contrib import admin
from .models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status', 'max_capacity', 'is_archived', 'created_at')
    list_filter = ('status', 'is_archived')
    search_fields = ('name', 'code')
    ordering = ('-created_at',)