import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .serializers import UserSerializer
from db_connection import db


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            db.users.insert_one(serializer.validated_data)
            return Response(
                {
                    "message": "User registered successfully!",
                    "role": serializer.validated_data.get("role")
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password')

        user = db.users.find_one({"email": email})

        if user and user.get('password') == password:
            return Response({
                "message": "Login successful!",
                "token": "mock-jwt-token-from-backend-xyz123",
                "email": user.get("email"),
                "role": user.get("role", "Student")
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        user = db.users.find_one({"email": email})
        if not user:
            return Response({"error": "Email address not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # 2. Save OTP to MongoDB user document
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
        new_password = request.data.get('password')

        # 1. Verify OTP and User
        user = db.users.find_one({"email": email, "otp": otp})
        if not user:
            return Response({"error": "Invalid OTP or Email"}, status=status.HTTP_400_BAD_REQUEST)

        result = db.users.update_one(
            {"email": email},
            {"$set": {"password": new_password}, "$unset": {"otp": ""}}
        )

        if result.modified_count > 0:
            return Response({"message": "Password updated successfully!"}, status=status.HTTP_200_OK)
        return Response({"error": "Update failed"}, status=status.HTTP_400_BAD_REQUEST)