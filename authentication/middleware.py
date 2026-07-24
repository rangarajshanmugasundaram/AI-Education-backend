from django.conf import settings
import jwt
from rest_framework import status
from rest_framework.response import Response

from db_connection import db

# DEV FLAG: Set to True to instantly bypass all 403 authorization restrictions for testing
BYPASS_RBAC_FOR_TESTING = False

JWT_SECRET = getattr(
    settings, 'SECRET_KEY', 'your-fallback-secret-key-change-in-production'
)
JWT_ALGORITHM = 'HS256'


def check_role(allowed_roles):

  def decorator(view_func):

    def wrapper(self, request, *args, **kwargs):
      # 0. SAFE PASS FOR CORS PREFLIGHT OPTIONS REQUESTS
      if request.method == 'OPTIONS':
        return view_func(self, request, *args, **kwargs)

      # DEV OVERRIDE LOGIC
      if BYPASS_RBAC_FOR_TESTING:
        return view_func(self, request, *args, **kwargs)

      # 1. Real JWT Token Extraction & Verification
      auth_header = request.headers.get('Authorization', '')
      token = (
          auth_header.split(' ')[1]
          if auth_header.startswith('Bearer ')
          else auth_header
      )

      if not token:
        return Response(
            {'error': 'Unauthorized: Missing token'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

      try:
        # Decode and verify token signature and expiration
        decoded_payload = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        token_email = decoded_payload.get('email')
        token_role = decoded_payload.get('role')
      except jwt.ExpiredSignatureError:
        return Response(
            {'error': 'Unauthorized: Token has expired'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
      except jwt.InvalidTokenError:
        return Response(
            {'error': 'Unauthorized: Invalid token signature'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

      # 2. Extract & Cross-Check Header / Token Email
      user_email = (
          request.headers.get('X-User-Email') or token_email
      ).strip().lower()
      if not user_email:
        return Response(
            {
                'error': (
                    'Bad Request: Missing X-User-Email header or invalid token'
                    ' payload'
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

      # 3. RBAC Assessment against Database
      user = db.users.find_one({'email': user_email})
      if not user:
        return Response(
            {'error': 'Forbidden: User account context not found'},
            status=status.HTTP_403_FORBIDDEN,
        )

      normalized_user_role = str(
          user.get('role', token_role or 'Student')
      ).strip().lower()
      normalized_allowed_roles = [
          str(r).strip().lower() for r in allowed_roles
      ]

      if normalized_user_role not in normalized_allowed_roles:
        return Response(
            {
                'error': (
                    'Forbidden: You do not have permission'
                    f" ({', '.join(allowed_roles)})"
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

      # Attach validated claims directly to request context
      request.user_email = user_email
      request.user_role = normalized_user_role

      return view_func(self, request, *args, **kwargs)

    return wrapper

  return decorator