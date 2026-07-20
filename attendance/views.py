from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from db_connection import db
from authentication.middleware import check_role
from .serializers import AttendanceSerializer


class MarkAttendanceView(APIView):
    @check_role(["Student", "Admin", "Trainer"])
    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_id = str(data['user_id']).strip()
        session_id = str(data['session_id']).strip()
        student_name = str(data.get('student_name', 'Unknown')).strip()

        # Prevent duplicate attendance records
        existing_record = db.attendance.find_one({"user_id": user_id, "session_id": session_id})
        if existing_record:
            return Response(
                {"error": "Attendance record already exists for this student in this session!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        duration_str = "0 mins"
        join_str = data.get('join_time')
        leave_str = data.get('leave_time')

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
                    status=status.HTTP_400_BAD_REQUEST
                )

        attendance_record = {
            "user_id": user_id,
            "student_name": student_name,
            "session_id": session_id,
            "join_time": join_str if join_str else None,
            "leave_time": leave_str if leave_str else None,
            "duration": duration_str,
            "status": data.get('status', 'Present')
        }

        db.attendance.insert_one(attendance_record)
        attendance_record.pop('_id', None)

        return Response(
            {"message": "Attendance marked successfully!", "data": attendance_record},
            status=status.HTTP_201_CREATED
        )


class GetSessionAttendanceView(APIView):
    @check_role(["Admin", "Trainer"])
    def get(self, request, session_id):
        target_session = str(session_id).strip()

        # Pull everything globally if "all" keyword parameters are intercepted
        if target_session.lower() == "all":
            records = list(db.attendance.find({}))
        else:
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
            return Response(
                {"error": "Both user_id and session_id tracking parameters are required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = str(user_id).strip()
        session_id = str(session_id).strip()

        record = db.attendance.find_one({"user_id": user_id, "session_id": session_id})
        if not record:
            return Response(
                {"error": "Attendance record targeted for update could not be found"},
                status=status.HTTP_404_NOT_FOUND
            )

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
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if not update_fields:
            return Response(
                {"message": "No modification properties were provided. Nothing to update."},
                status=status.HTTP_200_OK
            )

        db.attendance.update_one({"user_id": user_id, "session_id": session_id}, {"$set": update_fields})
        return Response({"message": "Attendance record updated successfully!"}, status=status.HTTP_200_OK)


class GetSessionAttendanceReportView(APIView):
    @check_role(["Admin", "Trainer"])
    def get(self, request, session_id):
        target_session = str(session_id).strip()

        # Global metrics arithmetic fallback block for collective dashboard cards
        if target_session.lower() == "all":
            records = list(db.attendance.find({}))
        else:
            records = list(db.attendance.find({"session_id": target_session}))

        total_records = len(records)
        present_count = sum(1 for r in records if r.get('status') == 'Present')
        absent_count = sum(1 for r in records if r.get('status') == 'Absent')
        late_count = sum(1 for r in records if r.get('status') == 'Late')

        attendance_percentage = 0
        if total_records > 0:
            attendance_percentage = round(((present_count + late_count) / total_records) * 100, 2)

        durations = []
        for r in records:
            dur_str = r.get('duration', '0 mins')
            try:
                val = float(str(dur_str).split()[0])
                durations.append(val)
            except (ValueError, IndexError):
                continue

        avg_duration = round(sum(durations) / len(durations), 2) if durations else 0

        report_data = {
            "session_id": target_session,
            "metrics": {
                "total_students_logged": total_records,
                "presence_count": present_count,
                "absence_count": absent_count,
                "lateness_count": late_count,
                "attendance_percentage": f"{attendance_percentage}%"
            },
            "duration_report": {
                "average_duration_minutes": f"{avg_duration} mins",
                "tracked_durations": [r.get('duration', '0 mins') for r in records]
            }
        }
        return Response(report_data, status=status.HTTP_200_OK)


class GetStudentAttendanceReportView(APIView):
    @check_role(["Student", "Admin", "Trainer"])
    def get(self, request, student_id):
        target_student = str(student_id).strip()
        records = list(db.attendance.find({"user_id": target_student}))

        total_records = len(records)
        present_count = sum(1 for r in records if r.get('status') == 'Present')
        absent_count = sum(1 for r in records if r.get('status') == 'Absent')
        late_count = sum(1 for r in records if r.get('status') == 'Late')

        attendance_percentage = 0
        if total_records > 0:
            attendance_percentage = round(((present_count + late_count) / total_records) * 100, 2)

        durations = []
        session_breakdown = []
        for r in records:
            dur_str = r.get('duration', '0 mins')
            session_breakdown.append({
                "session_id": r.get('session_id'),
                "status": r.get('status'),
                "duration": dur_str
            })
            try:
                val = float(str(dur_str).split()[0])
                durations.append(val)
            except (ValueError, IndexError):
                continue

        total_time_spent = round(sum(durations), 2)
        avg_time_per_session = round(total_time_spent / len(durations), 2) if durations else 0

        report_data = {
            "student_id": target_student,
            "student_name": records[0].get('student_name', 'Unknown') if records else "Unknown",
            "metrics": {
                "total_sessions_tracked": total_records,
                "presence_count": present_count,
                "absence_count": absent_count,
                "lateness_count": late_count,
                "overall_attendance_percentage": f"{attendance_percentage}%"
            },
            "duration_report": {
                "total_time_spent": f"{total_time_spent} mins",
                "average_duration_per_session": f"{avg_time_per_session} mins"
            },
            "session_history": session_breakdown
        }
        return Response(report_data, status=status.HTTP_200_OK)