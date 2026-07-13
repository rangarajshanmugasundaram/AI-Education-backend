from rest_framework import serializers
from datetime import datetime

class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(max_length=50, default="Student", required=False)

    def validate_email(self, value):
        return value.strip().lower()

# ==================== ADDED FOR ATTENDANCE ====================
class AttendanceSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    session_id = serializers.CharField(max_length=100)
    join_time = serializers.CharField(required=False, allow_blank=True)
    leave_time = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["Present", "Absent", "Late"], default="Present")