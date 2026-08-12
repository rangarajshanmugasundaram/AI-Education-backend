from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import AssignmentService
from .serializers import (
    AssignmentCreateUpdateSerializer,
    AssignmentStatusToggleSerializer,
    StudentAssignmentSubmissionSerializer,
    GradeSubmissionSerializer
)


class AssignmentListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_role = request.headers.get('X-User-Role', 'Trainer')
        user_email = request.headers.get('X-User-Email', '')
        batch_code = request.query_params.get('batch_code', None)
        status_filter = request.query_params.get('status', 'all')

        assignments = AssignmentService.get_all_assignments(
            user_role=user_role,
            user_email=user_email,
            batch_code=batch_code,
            status_filter=status_filter
        )
        return Response({'success': True, 'count': len(assignments), 'data': assignments}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AssignmentCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            trainer_email = request.headers.get('X-User-Email', 'trainer@aieducation.com')
            assignment = AssignmentService.create_assignment(serializer.validated_data, trainer_email=trainer_email)
            return Response({'success': True, 'message': 'Assignment created successfully', 'data': assignment}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AssignmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        assignment = AssignmentService.get_assignment_by_id(assignment_id)
        if assignment:
            return Response({'success': True, 'data': assignment}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, assignment_id):
        serializer = AssignmentCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = AssignmentService.update_assignment(assignment_id, serializer.validated_data)
            if updated:
                return Response({'success': True, 'message': 'Assignment updated successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, assignment_id):
        success = AssignmentService.delete_assignment(assignment_id)
        if success:
            return Response({'success': True, 'message': 'Assignment deleted successfully'}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)


class AssignmentStatusToggleView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, assignment_id):
        serializer = AssignmentStatusToggleSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            success = AssignmentService.toggle_status(assignment_id, new_status)
            if success:
                return Response({'success': True, 'message': f'Assignment status updated to {new_status}'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AssignmentSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, assignment_id):
        serializer = StudentAssignmentSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                submission = AssignmentService.submit_assignment(assignment_id, serializer.validated_data)
                return Response({'success': True, 'message': 'Assignment submitted successfully', 'submission': submission}, status=status.HTTP_201_CREATED)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AssignmentSubmissionsRosterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        submissions = AssignmentService.get_assignment_submissions_roster(assignment_id)
        return Response({'success': True, 'count': len(submissions), 'data': submissions}, status=status.HTTP_200_OK)


class GradeSubmissionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, submission_id):
        serializer = GradeSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            evaluator_email = request.headers.get('X-User-Email', 'trainer@aieducation.com')
            try:
                success = AssignmentService.grade_submission(submission_id, serializer.validated_data, evaluator_email=evaluator_email)
                if success:
                    return Response({'success': True, 'message': 'Submission graded successfully'}, status=status.HTTP_200_OK)
                return Response({'success': False, 'message': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AssignmentAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assignment_id):
        analytics = AssignmentService.get_assignment_analytics(assignment_id)
        if analytics:
            return Response({'success': True, 'analytics': analytics}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Assignment analytics not found'}, status=status.HTTP_404_NOT_FOUND)