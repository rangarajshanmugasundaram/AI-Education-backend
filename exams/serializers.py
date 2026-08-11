from rest_framework import serializers

class QuestionOptionSerializer(serializers.Serializer):
    option_id = serializers.CharField(required=False)
    option_text = serializers.CharField(required=True)

class QuestionSerializer(serializers.Serializer):
    question_id = serializers.CharField(required=False)
    question_text = serializers.CharField(required=True)
    options = serializers.ListField(child=serializers.CharField(), required=True)
    correct_option_index = serializers.IntegerField(required=True)
    marks = serializers.IntegerField(default=1)

class ExamCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    course_name = serializers.CharField(max_length=255, required=False, default="General Curriculum")
    batch_code = serializers.CharField(max_length=100, required=True)
    duration_minutes = serializers.IntegerField(default=60)
    total_marks = serializers.IntegerField(default=100)
    passing_marks = serializers.IntegerField(default=40)
    scheduled_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['Draft', 'Published', 'Ongoing', 'Completed', 'Unpublished'],
        default='Draft'
    )
    questions = serializers.ListField(child=QuestionSerializer(), required=False, default=[])

class ExamStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['Draft', 'Published', 'Ongoing', 'Completed', 'Unpublished'])

class StudentExamSubmissionSerializer(serializers.Serializer):
    student_name = serializers.CharField(max_length=255, required=True)
    student_email = serializers.EmailField(required=True)
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Key: question_id/index, Value: selected_option_index"
    )