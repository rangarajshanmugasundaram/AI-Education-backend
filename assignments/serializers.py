from rest_framework import serializers


class AssignmentCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    course_name = serializers.CharField(max_length=255, required=False, default="General Curriculum")
    batch_code = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    total_marks = serializers.IntegerField(default=100)
    passing_marks = serializers.IntegerField(default=40)
    due_date = serializers.CharField(required=True)
    status = serializers.ChoiceField(
        choices=['Draft', 'Published', 'Open', 'Closed', 'Completed'],
        default='Draft'
    )
    instructions = serializers.CharField(required=False, allow_blank=True, default="")
    attachments = serializers.ListField(child=serializers.CharField(), required=False, default=[])


class AssignmentStatusToggleSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['Draft', 'Published', 'Open', 'Closed', 'Completed'])


class StudentAssignmentSubmissionSerializer(serializers.Serializer):
    student_name = serializers.CharField(max_length=255, required=True)
    student_email = serializers.EmailField(required=True)
    submission_text = serializers.CharField(required=False, allow_blank=True, default="")
    file_urls = serializers.ListField(child=serializers.CharField(), required=False, default=[])


class GradeSubmissionSerializer(serializers.Serializer):
    obtained_marks = serializers.IntegerField(required=True, min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")