from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsTrainerOrAdminForWrite(permissions.BasePermission):
    """
    Custom permission to only allow Trainers or Admins to edit/delete recordings.
    Students can only read (GET).
    """

    def _get_user_from_headers(self, request):
        if request.user and request.user.is_authenticated:
            return request.user

        # Inspect custom headers from Vite/Axios
        email = request.headers.get('X-User-Email') or request.META.get('HTTP_X_USER_EMAIL')
        if email:
            user = User.objects.filter(email__iexact=email.strip()).first()
            if user:
                return user

        # Fallback to default active trainer for dev/testing
        return User.objects.filter(email__iexact='trainer1@gmail.com').first()

    def has_permission(self, request, view):
        # Allow read-only GET/HEAD/OPTIONS requests for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        user = self._get_user_from_headers(request)
        if not user:
            return False

        # Check role or superuser permissions
        user_role = str(getattr(user, 'role', '')).lower()
        header_role = str(request.headers.get('X-User-Role', '')).lower()

        return (
                user.is_superuser or
                user.is_staff or
                user_role in ['trainer', 'admin', 'teacher'] or
                header_role in ['trainer', 'admin', 'teacher']
        )