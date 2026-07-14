from rest_framework import serializers

class AttendanceSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100, error_messages={"required": "User ID is required."})
    student_name = serializers.CharField(max_length=200, required=False, allow_blank=True) # Added this
    session_id = serializers.CharField(max_length=100, error_messages={"required": "Session ID is required."})
    join_time = serializers.CharField(required=False, allow_blank=True, default=None)
    leave_time = serializers.CharField(required=False, allow_blank=True, default=None)
    status = serializers.ChoiceField(choices=["Present", "Absent", "Late"], default="Present")