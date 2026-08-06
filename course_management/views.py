from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import CourseService
from .serializers import (
    CourseSerializer, CourseCreateSerializer,
    CourseUpdateSerializer, AssignTrainerSerializer
)
from .pagination import CoursePagination


class CourseListCreateView(APIView):
    permission_classes = [AllowAny]
    pagination_class = CoursePagination

    def get(self, request):
        search = request.query_params.get('search', '')
        category = request.query_params.get('category', 'all')
        status_param = request.query_params.get('status', 'all')
        include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'

        courses = CourseService.get_all_courses(
            search_query=search,
            category_filter=category,
            status_filter=status_param,
            include_archived=include_archived
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(courses, request)
        if page is not None:
            serializer = CourseSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                course = CourseService.create_course(serializer.validated_data)
                return Response({'success': True, 'data': course}, status=status.HTTP_201_CREATED)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        course = CourseService.get_course_by_id(course_id)
        if course:
            return Response({'success': True, 'data': course}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, course_id):
        serializer = CourseUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = CourseService.update_course(course_id, serializer.validated_data)
            if updated:
                return Response({'success': True, 'message': 'Course updated successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id):
        deleted = CourseService.delete_course(course_id)
        if deleted:
            return Response({'success': True, 'message': 'Course deleted successfully'}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)


class CourseAssignTrainerView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, course_id):
        serializer = AssignTrainerSerializer(data=request.data)
        if serializer.is_valid():
            assigned = CourseService.assign_trainer(course_id, serializer.validated_data['trainer_id'])
            if assigned:
                return Response({'success': True, 'message': 'Trainer assigned successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CourseArchiveView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, course_id):
        new_archive_state = CourseService.archive_course(course_id)
        if new_archive_state is not None:
            return Response({
                'success': True,
                'isArchived': new_archive_state,
                'message': f"Course {'archived' if new_archive_state else 'restored'} successfully"
            }, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)


class CourseStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id=None):
        stats = CourseService.get_course_stats(course_id)
        return Response({'success': True, 'stats': stats}, status=status.HTTP_200_OK)