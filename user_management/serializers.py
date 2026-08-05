from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    id = serializers.CharField(source='_id', read_only=True)
    name = serializers.CharField(max_length=255, required=False)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField()
    role = serializers.CharField(max_length=50, default='Student')
    isActive = serializers.BooleanField(default=True)
    createdAt = serializers.CharField(read_only=True)
    updatedAt = serializers.CharField(read_only=True)

class UserCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=['Student', 'Teacher', 'Trainer', 'Admin'], default='Student')
    isActive = serializers.BooleanField(default=True)

class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['Student', 'Teacher', 'Trainer', 'Admin'], required=False)
    isActive = serializers.BooleanField(required=False)

class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6, write_only=True)