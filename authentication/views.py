import random
import bcrypt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from db_connection import db
from .serializers import UserSerializer


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Check if email is already registered
            existing_user = db.users.find_one({"email": data['email']})
            if existing_user:
                return Response(
                    {"error": "A user with this email address already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Hash the password cleanly on registration
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            data['password'] = hashed_password
            data['email'] = data['email'].strip().lower()

            db.users.insert_one(data)
            return Response(
                {
                    "message": "User registered successfully!",
                    "role": data.get("role")
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        user = db.users.find_one({"email": email})
        if not user:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        stored_password = user.get('password', '')

        try:
            # Check if password exists and has a valid bcrypt structural prefix ($2b$ or $2a$)
            if stored_password and isinstance(stored_password, str) and stored_password.startswith('$2'):
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    return Response({
                        "message": "Login successful!",
                        "token": "mock-jwt-token-from-backend-xyz123",
                        "email": user.get("email"),
                        "role": user.get("role", "Student")
                    }, status=status.HTTP_200_OK)
            else:
                print(f"Warning: User {email} has an unhashed or invalid password format in database.")
        except ValueError:
            # Prevent malformed strings in the database from crashing the Django process
            pass

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        user = db.users.find_one({"email": email})
        if not user:
            return Response({"error": "Email address not found"}, status=status.HTTP_404_NOT_FOUND)

        otp = str(random.randint(100000, 999999))
        db.users.update_one({"email": email}, {"$set": {"otp": otp}})

        try:
            send_mail(
                subject='Password Reset OTP',
                message=f'Your verification code for password reset is: {otp}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({"message": "OTP sent to your email!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp')
        new_password = request.data.get('password', '')

        user = db.users.find_one({"email": email, "otp": otp})
        if not user:
            return Response({"error": "Invalid OTP or Email"}, status=status.HTTP_400_BAD_REQUEST)

        # Safely hash the new password string cleanly using bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        result = db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}, "$unset": {"otp": ""}}
        )

        if result.modified_count > 0:
            return Response({"message": "Password updated successfully!"}, status=status.HTTP_200_OK)
        return Response({"error": "Update failed"}, status=status.HTTP_400_BAD_REQUEST)