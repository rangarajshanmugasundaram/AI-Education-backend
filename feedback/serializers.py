from rest_framework import serializers
from .models import SessionFeedback

class SessionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFeedback
        fields = ['id', 'session_id', 'student_id', 'trainer_id', 'rating', 'review', 'tags', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be an integer between 1 and 5.")
        return value