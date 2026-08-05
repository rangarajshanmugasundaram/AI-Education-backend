from db_connection import db  # Native PyMongo connection Singleton
from datetime import datetime, timedelta


class DashboardAggregationService:
    @staticmethod
    def fetch_dashboard_metrics():
        # Collections references
        users_col = db['users']
        courses_col = db['courses']
        batches_col = db['batches']
        sessions_col = db['sessions']
        exams_col = db['exams']
        certificates_col = db['certificates']
        assignments_col = db['assignments']

        # 1. Primary Statistics Counts
        total_students = users_col.count_documents({
            'role': {'$regex': '^student$', '$options': 'i'}
        })
        total_trainers = users_col.count_documents({
            'role': {'$regex': '^(trainer|teacher)$', '$options': 'i'}
        })
        total_courses = courses_col.count_documents({})
        total_batches = batches_col.count_documents({})

        active_live_sessions = sessions_col.count_documents({
            'status': {'$in': ['live', 'active', 'IN_PROGRESS', 'LIVE']}
        })
        completed_sessions = sessions_col.count_documents({
            'status': {'$in': ['completed', 'ended', 'FINISHED', 'COMPLETED']}
        })

        total_exams = exams_col.count_documents({})
        total_certificates = certificates_col.count_documents({})
        pending_assignments = assignments_col.count_documents({
            'status': {'$in': ['pending', 'submitted', 'NEEDS_GRADING', 'PENDING']}
        })

        # 2. Registration Trend (Last 7 Days)
        today = datetime.utcnow().date()
        registration_trend = []
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)
            start_dt = datetime.combine(day_date, datetime.min.time())
            end_dt = datetime.combine(day_date, datetime.max.time())

            count = users_col.count_documents({
                '$or': [
                    {'createdAt': {'$gte': start_dt, '$lte': end_dt}},
                    {'created_at': {'$gte': start_dt, '$lte': end_dt}}
                ]
            })
            registration_trend.append({
                'label': day_date.strftime('%d %b'),
                'date': day_date.strftime('%Y-%m-%d'),
                'count': count
            })

        # 3. Session Status Breakdown
        session_status = [
            {'status': 'Completed', 'count': completed_sessions},
            {'status': 'Live', 'count': active_live_sessions}
        ]

        # 4. Recent User Registrations (Last 5 registered users)
        recent_users_cursor = users_col.find(
            {},
            {
                '_id': 1,
                'name': 1,
                'first_name': 1,
                'last_name': 1,
                'email': 1,
                'role': 1,
                'isActive': 1,
                'createdAt': 1,
                'created_at': 1
            }
        ).sort('_id', -1).limit(5)

        recent_registrations = []
        for user in recent_users_cursor:
            full_name = user.get('name')
            if not full_name:
                first = user.get('first_name', '')
                last = user.get('last_name', '')
                full_name = f"{first} {last}".strip() or 'N/A'

            raw_date = user.get('createdAt') or user.get('created_at')
            created_str = raw_date.isoformat() if isinstance(raw_date, datetime) else str(raw_date or 'Recently')

            recent_registrations.append({
                '_id': str(user.get('_id')),
                'name': full_name,
                'email': user.get('email', 'N/A'),
                'role': user.get('role', 'Student'),
                'isActive': user.get('isActive', True),
                'createdAt': created_str
            })

        # 5. Recent Session Activity Stream
        recent_sessions_cursor = sessions_col.find(
            {},
            {
                '_id': 1,
                'title': 1,
                'sessionName': 1,
                'batch_name': 1,
                'trainerName': 1,
                'trainer_email': 1,
                'status': 1,
                'updatedAt': 1,
                'startTime': 1,
                'created_at': 1
            }
        ).sort('_id', -1).limit(5)

        recent_sessions = []
        for s in recent_sessions_cursor:
            s_name = s.get('sessionName') or s.get('title') or s.get('batch_name') or 'Classroom Session'
            t_name = s.get('trainerName') or s.get('trainer_email') or 'Assigned Trainer'
            raw_time = s.get('updatedAt') or s.get('startTime') or s.get('created_at')
            time_str = raw_time.isoformat() if isinstance(raw_time, datetime) else str(raw_time or 'Recently')

            recent_sessions.append({
                '_id': str(s.get('_id')),
                'sessionName': s_name,
                'trainerName': t_name,
                'status': str(s.get('status', 'Completed')).capitalize(),
                'updatedAt': time_str
            })

        return {
            'statistics': {
                'totalStudents': total_students,
                'totalTrainers': total_trainers,
                'totalCourses': total_courses,
                'totalBatches': total_batches,
                'activeLiveSessions': active_live_sessions,
                'completedSessions': completed_sessions,
                'totalExams': total_exams,
                'totalCertificates': total_certificates,
                'pendingAssignments': pending_assignments,
            },
            'recentRegistrations': recent_registrations,
            'recentActivity': {
                'sessions': recent_sessions
            },
            'charts': {
                'registrationTrend': registration_trend,
                'sessionStatus': session_status
            },
            'generatedAt': datetime.utcnow().isoformat()
        }