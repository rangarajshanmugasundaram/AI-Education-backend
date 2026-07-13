import random
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import bcrypt

from .serializers import UserSerializer, AttendanceSerializer
from db_connection import db
from .middleware import check_role


# ==================== AUTHENTICATION VIEWS ====================

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
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

        if user and bcrypt.checkpw(password.encode('utf-8'), user.get('password', '').encode('utf-8')):
            return Response({
                "message": "Login successful!",
                "token": "mock-jwt-token-from-backend-xyz123",
                "email": user.get("email"),
                "role": user.get("role", "Student")
            }, status=settings.HTTP_200_OK if hasattr(settings, 'HTTP_200_OK') else status.HTTP_200_OK)

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

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        result = db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}, "$unset": {"otp": ""}}
        )

        if result.modified_count > 0:
            return Response({"message": "Password updated successfully!"}, status=status.HTTP_200_OK)
        return Response({"error": "Update failed"}, status=status.HTTP_400_BAD_REQUEST)


# ==================== ATTENDANCE MANAGEMENT VIEWS ====================

class MarkAttendanceView(APIView):
    @check_role(["Student", "Admin", "Trainer"])
    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_id = str(data['user_id']).strip()
        session_id = str(data['session_id']).strip()

        # Prevent duplicate attendance records
        existing_record = db.attendance.find_one({"user_id": user_id, "session_id": session_id})
        if existing_record:
            return Response({"error": "Attendance record already exists for this student in this session!"},
                            status=status.HTTP_400_BAD_REQUEST)

        duration_str = "0 mins"
        join_str = data.get('join_time')
        leave_str = data.get('leave_time')

        # Compute session timeline tracking metrics
        if join_str and leave_str:
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                join_dt = datetime.strptime(str(join_str).strip(), fmt)
                leave_dt = datetime.strptime(str(leave_str).strip(), fmt)
                duration_minutes = round((leave_dt - join_dt).total_seconds() / 60, 2)
                duration_str = f"{duration_minutes} mins"
            except ValueError:
                return Response(
                    {"error": "Invalid date format setup. Use strict YYYY-MM-DD HH:MM:SS format specifications."},
                    status=status.HTTP_400_BAD_REQUEST)

        attendance_record = {
            "user_id": user_id,
            "session_id": session_id,
            "join_time": join_str if join_str else None,
            "leave_time": leave_str if leave_str else None,
            "duration": duration_str,
            "status": data.get('status', 'Present')
        }

        db.attendance.insert_one(attendance_record)
        attendance_record.pop('_id', None)

        return Response({"message": "Attendance marked successfully!", "data": attendance_record},
                        status=status.HTTP_201_CREATED)


class GetSessionAttendanceView(APIView):
    @check_role(["Admin", "Trainer"])
    def get(self, request, session_id):
        target_session = str(session_id).strip()
        records = list(db.attendance.find({"session_id": target_session}))

        for r in records:
            r.pop('_id', None)

        return Response({"session_id": target_session, "records": records}, status=status.HTTP_200_OK)


class GetStudentAttendanceView(APIView):
    @check_role(["Student", "Admin", "Trainer"])
    def get(self, request, student_id):
        target_student = str(student_id).strip()
        records = list(db.attendance.find({"user_id": target_student}))

        for r in records:
            r.pop('_id', None)

        return Response({"student_id": target_student, "records": records}, status=status.HTTP_200_OK)


class UpdateAttendanceView(APIView):
    @check_role(["Admin", "Trainer"])
    def put(self, request):
        user_id = request.data.get('user_id')
        session_id = request.data.get('session_id')
        new_status = request.data.get('status')
        leave_str = request.data.get('leave_time')

        if not user_id or not session_id:
            return Response({"error": "Both user_id and session_id tracking parameters are required fields"},
                            status=status.HTTP_400_BAD_REQUEST)

        user_id = str(user_id).strip()
        session_id = str(session_id).strip()

        record = db.attendance.find_one({"user_id": user_id, "session_id": session_id})
        if not record:
            return Response({"error": "Attendance record targeted for update could not be found"},
                            status=status.HTTP_404_NOT_FOUND)

        update_fields = {}
        if new_status:
            update_fields["status"] = str(new_status).strip()

        if leave_str:
            leave_str = str(leave_str).strip()
            update_fields["leave_time"] = leave_str
            join_str = record.get('join_time')
            if join_str:
                try:
                    fmt = "%Y-%m-%d %H:%M:%S"
                    join_dt = datetime.strptime(str(join_str).strip(), fmt)
                    leave_dt = datetime.strptime(leave_str, fmt)
                    update_fields["duration"] = f"{round((leave_dt - join_dt).total_seconds() / 60, 2)} mins"
                except ValueError:
                    return Response(
                        {"error": "Invalid date format specified. Use YYYY-MM-DD HH:MM:SS format parameters."},
                        status=status.HTTP_400_BAD_REQUEST)

        if not update_fields:
            return Response({"message": "No modification properties were provided. Nothing to update."},
                            status=status.HTTP_200_OK)

        db.attendance.update_one({"user_id": user_id, "session_id": session_id}, {"$set": update_fields})
        return Response({"message": "Attendance record updated successfully!"}, status=status.HTTP_200_OK)