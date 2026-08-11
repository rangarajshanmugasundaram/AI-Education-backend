from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import BatchService
from .serializers import (
    BatchSerializer, BatchCreateSerializer, BatchUpdateSerializer,
    AllocateStudentsSerializer, AllocateTrainerSerializer
)
from .pagination import BatchPagination


class BatchListCreateView(APIView):
    permission_classes = [AllowAny]
    pagination_class = BatchPagination

    def get(self, request):
        search = request.query_params.get('search', '')
        status_param = request.query_params.get('status', 'all')
        include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'

        user_role = request.headers.get('X-User-Role', 'Trainer')
        user_email = request.headers.get('X-User-Email', '')

        batches = BatchService.get_all_batches(
            search_query=search,
            status_filter=status_param,
            include_archived=include_archived
        )

        # If accessed by a student, filter batch list to show their assigned batches
        if user_role and user_role.lower() == 'student' and user_email:
            user_doc = BatchService.get_users_col().find_one({'email': user_email.strip().lower()})
            if user_doc and 'batch_ids' in user_doc:
                student_batch_ids = [str(b_id) for b_id in user_doc.get('batch_ids', [])]
                batches = [b for b in batches if
                           str(b['_id']) in student_batch_ids or b.get('code') in student_batch_ids]

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(batches, request)
        if page is not None:
            serializer = BatchSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BatchSerializer(batches, many=True)
        return Response({'success': True, 'count': len(batches), 'data': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                batch = BatchService.create_batch(serializer.validated_data)
                return Response({'success': True, 'message': 'Batch created successfully', 'data': batch},
                                status=status.HTTP_201_CREATED)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BatchDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, batch_id):
        batch = BatchService.get_batch_by_id(batch_id)
        if batch:
            return Response({'success': True, 'data': batch}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, batch_id):
        serializer = BatchUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = BatchService.update_batch(batch_id, serializer.validated_data)
            if updated:
                return Response({'success': True, 'message': 'Batch updated successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AllocateStudentsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, batch_id):
        serializer = AllocateStudentsSerializer(data=request.data)
        if serializer.is_valid():
            success = BatchService.allocate_students(batch_id, serializer.validated_data['student_ids'])
            if success:
                return Response({'success': True, 'message': 'Students allocated successfully'},
                                status=status.HTTP_200_OK)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AllocateTrainerView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, batch_id):
        serializer = AllocateTrainerSerializer(data=request.data)
        if serializer.is_valid():
            success = BatchService.allocate_trainer(batch_id, serializer.validated_data['trainer_id'])
            if success:
                return Response({'success': True, 'message': 'Trainer allocated successfully'},
                                status=status.HTTP_200_OK)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BatchStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, batch_id=None):
        stats = BatchService.get_batch_stats(batch_id)
        return Response({'success': True, 'stats': stats}, status=status.HTTP_200_OK)