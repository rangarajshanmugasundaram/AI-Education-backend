from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(max_length=50, default="Student", required=False)

    def validate_email(self, value):
        return value.strip().lower()


class AttendanceSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100, error_messages={"required": "User ID is required."})
    session_id = serializers.CharField(max_length=100, error_messages={"required": "Session ID is required."})
    join_time = serializers.CharField(required=False, allow_blank=True, default=None)
    leave_time = serializers.CharField(required=False, allow_blank=True, default=None)
    status = serializers.ChoiceField(choices=["Present", "Absent", "Late"], default="Present")