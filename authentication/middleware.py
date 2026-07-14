from rest_framework.response import Response
from rest_framework import status
from db_connection import db

# 💡 DEV FLAG: Set to True to instantly bypass all 403 authorization restrictions for testing
BYPASS_RBAC_FOR_TESTING = False

def check_role(allowed_roles):
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            # 0. SAFE PASS FOR CORS PREFLIGHT OPTIONS REQUESTS
            if request.method == "OPTIONS":
                return view_func(self, request, *args, **kwargs)

            # DEV OVERRIDE LOGIC
            if BYPASS_RBAC_FOR_TESTING:
                return view_func(self, request, *args, **kwargs)

            # 1. Token Check
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header

            if not token or token != "mock-jwt-token-from-backend-xyz123":
                return Response(
                    {"error": "Unauthorized: Invalid or missing token"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # 2. Extract Identifier Header
            user_email = request.headers.get('X-User-Email')
            if not user_email:
                return Response(
                    {"error": "Bad Request: Missing X-User-Email header for authentication"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. RBAC Assessment
            user = db.users.find_one({"email": user_email.strip().lower()})
            if not user:
                return Response(
                    {"error": "Forbidden: User account context not found"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Clean roles list and target user value for robust comparison
            normalized_user_role = str(user.get("role", "Student")).strip().lower()
            normalized_allowed_roles = [str(r).strip().lower() for r in allowed_roles]

            if normalized_user_role not in normalized_allowed_roles:
                return Response(
                    {"error": f"Forbidden: You do not have permission ({', '.join(allowed_roles)})"},
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator