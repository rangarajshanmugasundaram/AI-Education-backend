from rest_framework import serializers


class GenerateCertificateSerializer(serializers.Serializer):
    student_name = serializers.CharField(max_length=255, required=True)
    student_email = serializers.EmailField(required=True)
    course_name = serializers.CharField(max_length=255, required=True)
    batch_code = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    completion_date = serializers.CharField(required=False, allow_blank=True)
    issue_date = serializers.CharField(required=False, allow_blank=True)
    grade_achieved = serializers.CharField(max_length=50, required=False, default="Pass")


class VerifyCertificateSerializer(serializers.Serializer):
    certificate_id = serializers.CharField(max_length=100, required=True)