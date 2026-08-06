from rest_framework import serializers


class CourseSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=50)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.CharField(max_length=50, required=False, allow_blank=True)
    prerequisites = serializers.CharField(required=False, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    trainer_name = serializers.CharField(required=False, allow_blank=True)
    trainer_email = serializers.CharField(required=False, allow_blank=True)
    isArchived = serializers.BooleanField(default=False)
    status = serializers.CharField(default='Active')
    createdAt = serializers.CharField(read_only=True)


class CourseCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=50)
    category = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.CharField(required=False, allow_blank=True)
    prerequisites = serializers.CharField(required=False, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.CharField(default='Active')


class CourseUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    code = serializers.CharField(max_length=50, required=False)
    category = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.CharField(required=False, allow_blank=True)
    prerequisites = serializers.CharField(required=False, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.CharField(required=False)
    isArchived = serializers.BooleanField(required=False)


class AssignTrainerSerializer(serializers.Serializer):
    trainer_id = serializers.CharField()