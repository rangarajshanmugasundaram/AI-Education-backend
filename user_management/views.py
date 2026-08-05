from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import UserService
from .serializers import (
    UserSerializer, UserCreateSerializer,
    UserUpdateSerializer, PasswordResetSerializer
)
from .pagination import UserPagination


class UserListCreateView(APIView):
    permission_classes = [AllowAny]
    pagination_class = UserPagination

    def get(self, request):
        search = request.query_params.get('search', '')
        role = request.query_params.get('role', 'all')
        is_active = request.query_params.get('isActive', 'all')

        users = UserService.get_all_users(search_query=search, role_filter=role, status_filter=is_active)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = UserService.create_user(serializer.validated_data)
                return Response({'success': True, 'data': user}, status=status.HTTP_201_CREATED)
            except ValueError as err:
                return Response({'success': False, 'message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, user_id):
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = UserService.update_user(user_id, serializer.validated_data)
            if updated:
                return Response({'success': True, 'message': 'User updated successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        deleted = UserService.delete_user(user_id)
        if deleted:
            return Response({'success': True, 'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserToggleStatusView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, user_id):
        new_status = UserService.toggle_status(user_id)
        if new_status is not None:
            return Response({
                'success': True,
                'isActive': new_status,
                'message': f"User status set to {'Active' if new_status else 'Inactive'}"
            }, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            success = UserService.reset_password(user_id, serializer.validated_data['new_password'])
            if success:
                return Response({'success': True, 'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)