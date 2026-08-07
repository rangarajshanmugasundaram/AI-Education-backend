from rest_framework import serializers


class BatchSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=50)
    course_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    course_name = serializers.CharField(read_only=True)
    course_code = serializers.CharField(read_only=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    trainer_name = serializers.CharField(read_only=True)
    trainer_email = serializers.CharField(read_only=True)
    max_capacity = serializers.IntegerField(default=30)
    enrolled_students_count = serializers.IntegerField(read_only=True)
    start_date = serializers.CharField(required=False, allow_blank=True)
    end_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(default='Active')
    isArchived = serializers.BooleanField(default=False)
    createdAt = serializers.CharField(read_only=True)


class BatchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=50)
    course_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    max_capacity = serializers.IntegerField(default=30, min_value=1)
    start_date = serializers.CharField(required=False, allow_blank=True)
    end_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(default='Active')


class BatchUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    code = serializers.CharField(max_length=50, required=False)
    course_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    max_capacity = serializers.IntegerField(required=False, min_value=1)
    start_date = serializers.CharField(required=False, allow_blank=True)
    end_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)
    isArchived = serializers.BooleanField(required=False)


class AllocateStudentsSerializer(serializers.Serializer):
    student_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class AllocateTrainerSerializer(serializers.Serializer):
    trainer_id = serializers.CharField()