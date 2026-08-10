import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db
from .models import ClassroomSession, Participant, ActivityLog


class LiveMonitoringService:
    @staticmethod
    def get_classroom_sessions_col():
        return db['sessions']

    @staticmethod
    def get_participants_col():
        return db['classroom_participants']

    @staticmethod
    def get_attendance_col():
        return db['attendance']

    @staticmethod
    def get_batches_col():
        return db['batches']

    @classmethod
    def _get_batch_student_count(cls, batch_code):
        """Helper method to fetch total enrolled students for a batch from MongoDB."""
        if not batch_code:
            return 25

        try:
            batch_doc = cls.get_batches_col().find_one({
                '$or': [
                    {'batch_code': batch_code},
                    {'batch_name': batch_code},
                    {'name': batch_code},
                    {'_id': ObjectId(batch_code) if ObjectId.is_valid(batch_code) else batch_code}
                ]
            })

            if batch_doc:
                # Check different possible array/number schema representations for student count
                if 'student_ids' in batch_doc and isinstance(batch_doc['student_ids'], list):
                    return len(batch_doc['student_ids'])
                elif 'students' in batch_doc and isinstance(batch_doc['students'], list):
                    return len(batch_doc['students'])
                elif 'total_students' in batch_doc:
                    return int(batch_doc['total_students'])
                elif 'student_count' in batch_doc:
                    return int(batch_doc['student_count'])
        except Exception as err:
            print(f"[Batch Count Fetch Warning]: {err}")

        return 25  # Default fallback if batch is not found or has no enrolled list

    @classmethod
    def get_active_live_sessions(cls):
        """
        Fetches all active live sessions with trainer name, batch details, real-time participant counts,
        duration, and dynamic attendance breakdown calculated against total batch enrollment.
        Checks both SQLite ORM and MongoDB collections.
        """
        active_sessions = []
        now_utc = datetime.now(timezone.utc)

        # 1. Fetch from SQLite ORM
        orm_sessions = ClassroomSession.objects.filter(is_live=True).order_by('-created_at')
        for s in orm_sessions:
            session_id = str(s.id)

            # Fetch connected active participants from SQLite ORM
            participants_qs = Participant.objects.filter(session=s, status='Active')
            participants_data = []
            trainer_name = 'Assigned Trainer'

            for p in participants_qs:
                if p.role.lower() == 'trainer':
                    trainer_name = p.name

                participants_data.append({
                    '_id': str(p.id),
                    'name': p.name,
                    'email': p.email,
                    'role': p.role,
                    'status': p.status,
                    'is_muted': p.is_muted,
                    'is_camera_on': p.is_camera_on,
                    'has_raised_hand': p.has_raised_hand
                })

            batch_code = 'BATCH-2026-A'
            total_enrolled = cls._get_batch_student_count(batch_code)

            # Attendance Metrics from MongoDB 'attendance' collection
            attendance_records = list(cls.get_attendance_col().find({'session_id': session_id}))
            total_students_logged = len(attendance_records)

            if total_students_logged > 0:
                present_count = sum(1 for r in attendance_records if r.get('status') in ['Present', 'Late'])
                late_count = sum(1 for r in attendance_records if r.get('status') == 'Late')
                absent_count = max(0, total_enrolled - present_count)
            else:
                # Fallback calculation based on connected live participants vs total batch size
                present_count = sum(1 for p in participants_data if p['role'].lower() == 'student')
                late_count = 0
                absent_count = max(0, total_enrolled - present_count)

            attendance_pct = 0.0
            if total_enrolled > 0:
                attendance_pct = round((present_count / total_enrolled) * 100, 1)

            duration_minutes = round((now_utc - s.created_at).total_seconds() / 60) if s.created_at else 0

            active_sessions.append({
                'session_id': session_id,
                'title': s.title,
                'batch_code': batch_code,
                'trainer_name': trainer_name,
                'course_name': 'Live Interactive Classroom',
                'is_live': True,
                'is_locked': s.is_locked,
                'active_participant_count': len(participants_data),
                'duration_minutes': duration_minutes,
                'started_at': s.created_at.isoformat() if s.created_at else '',
                'attendance_summary': {
                    'total_logged': total_enrolled,
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'attendance_percentage': f"{attendance_pct}%"
                },
                'participants': participants_data
            })

        # 2. Fetch from MongoDB 'sessions' collection if SQLite yielded no sessions or as fallback
        if not active_sessions:
            cursor = cls.get_classroom_sessions_col().find({
                '$or': [
                    {'status': {'$regex': '^(live|active|ongoing)$', '$options': 'i'}},
                    {'is_live': True}
                ]
            }).sort('_id', -1)

            for doc in cursor:
                session_id = str(doc.get('_id'))
                batch_code = doc.get('batch_code') or doc.get('batchName') or 'BATCH-2026-FS1'

                # Total students expected in this batch
                total_enrolled = doc.get('total_batch_students') or cls._get_batch_student_count(batch_code)

                # Fetch connected participants for this MongoDB session
                participants_cursor = cls.get_participants_col().find({'session_id': session_id, 'status': 'Active'})
                mongo_participants = []
                trainer_name = doc.get('trainerName') or doc.get('trainer_name') or 'Assigned Trainer'

                for p in participants_cursor:
                    role = p.get('role', 'Student')
                    if role.lower() == 'trainer':
                        trainer_name = p.get('name', trainer_name)

                    mongo_participants.append({
                        '_id': str(p.get('_id')),
                        'name': p.get('name', 'Participant'),
                        'email': p.get('email', ''),
                        'role': role,
                        'status': p.get('status', 'Active'),
                        'is_muted': p.get('is_muted', True),
                        'is_camera_on': p.get('is_camera_on', False),
                        'has_raised_hand': p.get('has_raised_hand', False)
                    })

                # Check attendance logs
                attendance_records = list(cls.get_attendance_col().find({'session_id': session_id}))

                if attendance_records:
                    present_count = sum(1 for r in attendance_records if r.get('status') in ['Present', 'Late'])
                    late_count = sum(1 for r in attendance_records if r.get('status') == 'Late')
                    absent_count = max(0, total_enrolled - present_count)
                else:
                    present_count = len(mongo_participants)
                    late_count = doc.get('late_count', 0)
                    absent_count = max(0, total_enrolled - present_count)

                attendance_pct = 0.0
                if total_enrolled > 0:
                    attendance_pct = round((present_count / total_enrolled) * 100, 1)

                created_at = doc.get('created_at') or doc.get('createdAt') or now_utc
                if isinstance(created_at, str):
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        duration_minutes = round((now_utc - created_dt).total_seconds() / 60)
                        created_str = created_at
                    except Exception:
                        duration_minutes = 30
                        created_str = created_at
                elif isinstance(created_at, datetime):
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    duration_minutes = round((now_utc - created_at).total_seconds() / 60)
                    created_str = created_at.isoformat()
                else:
                    duration_minutes = 30
                    created_str = now_utc.isoformat()

                active_sessions.append({
                    'session_id': session_id,
                    'title': doc.get('title') or doc.get('sessionName') or 'Live Session',
                    'batch_code': batch_code,
                    'trainer_name': trainer_name,
                    'course_name': doc.get('course_name') or doc.get('topic') or 'General Curriculum',
                    'is_live': True,
                    'is_locked': doc.get('is_locked', False),
                    'active_participant_count': len(mongo_participants),
                    'duration_minutes': max(0, duration_minutes),
                    'started_at': created_str,
                    'attendance_summary': {
                        'total_logged': total_enrolled,
                        'present': present_count,
                        'absent': absent_count,
                        'late': late_count,
                        'attendance_percentage': f"{attendance_pct}%"
                    },
                    'participants': mongo_participants
                })

        return active_sessions

    @classmethod
    def force_end_session(cls, session_id):
        """Administrative action to forcibly end an ongoing live session."""
        ended = False

        # 1. Update SQLite ORM
        orm_session = ClassroomSession.objects.filter(id=session_id).first()
        if orm_session:
            orm_session.is_live = False
            orm_session.save()
            Participant.objects.filter(session=orm_session).update(status='Disconnected')
            ActivityLog.objects.create(session=orm_session, action="Session forcibly terminated by Admin")
            ended = True

        # 2. Update MongoDB 'sessions'
        sessions_col = cls.get_classroom_sessions_col()
        try:
            query = {'$or': [{'id': session_id}, {'_id': ObjectId(session_id)}]}
        except Exception:
            query = {'$or': [{'id': session_id}, {'_id': session_id}]}

        res = sessions_col.update_one(
            query,
            {'$set': {'is_live': False, 'status': 'Ended', 'ended_at': datetime.now(timezone.utc),
                      'ended_by_admin': True}}
        )

        if res.modified_count > 0 or res.matched_count > 0:
            ended = True

        return ended

    @classmethod
    def get_single_session_stats(cls, session_id):
        active_sessions = cls.get_active_live_sessions()
        for s in active_sessions:
            if s['session_id'] == session_id:
                return s
        return None

    @classmethod
    def get_global_live_stats(cls):
        active_sessions = cls.get_active_live_sessions()
        total_active_count = len(active_sessions)
        total_live_participants = sum(s['active_participant_count'] for s in active_sessions)

        avg_attendance = 0.0
        if total_active_count > 0:
            pct_sum = sum(
                float(s['attendance_summary']['attendance_percentage'].replace('%', '')) for s in active_sessions)
            avg_attendance = round(pct_sum / total_active_count, 1)

        return {
            'total_active_sessions': total_active_count,
            'total_live_participants': total_live_participants,
            'average_attendance_rate': f"{avg_attendance}%",
            'system_health_status': 'Optimal' if total_active_count < 20 else 'High Load'
        }