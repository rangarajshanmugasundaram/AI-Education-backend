from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import ExamService
from .serializers import (
    ExamCreateUpdateSerializer,
    ExamStatusSerializer,
    StudentExamSubmissionSerializer
)

class ExamListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_role = request.headers.get('X-User-Role', 'Trainer')
        batch_code = request.query_params.get('batch_code', None)
        status_filter = request.query_params.get('status', 'all')

        exams = ExamService.get_all_exams(
            user_role=user_role,
            batch_code=batch_code,
            status_filter=status_filter
        )
        return Response({'success': True, 'count': len(exams), 'data': exams}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ExamCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            trainer_email = request.headers.get('X-User-Email', 'trainer@aieducation.com')
            exam = ExamService.create_exam(serializer.validated_data, trainer_email=trainer_email)
            return Response({'success': True, 'message': 'Exam created successfully', 'data': exam}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ExamDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, exam_id):
        exam = ExamService.get_exam_by_id(exam_id)
        if exam:
            return Response({'success': True, 'data': exam}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, exam_id):
        serializer = ExamCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = ExamService.update_exam(exam_id, serializer.validated_data)
            if updated:
                return Response({'success': True, 'message': 'Exam updated successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, exam_id):
        success = ExamService.delete_exam(exam_id)
        if success:
            return Response({'success': True, 'message': 'Exam deleted successfully'}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)


class ExamPublishToggleView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, exam_id):
        serializer = ExamStatusSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            success = ExamService.toggle_publish_status(exam_id, new_status)
            if success:
                return Response({'success': True, 'message': f'Exam status updated to {new_status}'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ExamSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, exam_id):
        serializer = StudentExamSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = ExamService.submit_student_exam(exam_id, serializer.validated_data)
                return Response({'success': True, 'message': 'Exam submitted successfully', 'result': result}, status=status.HTTP_201_CREATED)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ExamResultsSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, exam_id):
        results = ExamService.get_exam_results_summary(exam_id)
        return Response({'success': True, 'count': len(results), 'data': results}, status=status.HTTP_200_OK)


class ExamAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, exam_id):
        analytics = ExamService.get_exam_analytics(exam_id)
        if analytics:
            return Response({'success': True, 'analytics': analytics}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Exam analytics not found'}, status=status.HTTP_404_NOT_FOUND)