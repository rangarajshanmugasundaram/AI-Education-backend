import uuid
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db
from .mongo_models import AssignmentMongoModel, AssignmentSubmissionMongoModel


class AssignmentService:
    @staticmethod
    def get_assignments_col():
        return db['assignments']

    @staticmethod
    def get_submissions_col():
        return db['assignment_submissions']

    @staticmethod
    def get_batches_col():
        return db['batches']

    @staticmethod
    def get_users_col():
        return db['users']

    @classmethod
    def get_all_assignments(cls, user_role='Trainer', user_email=None, batch_code=None, status_filter=None):
        """Fetches assignments with RBAC batch filtering."""
        query = {}

        if user_role and user_role.lower() == 'student':
            query['status'] = {'$in': ['Published', 'Open', 'Closed']}
            allowed_batch_identifiers = set()

            if user_email:
                user_doc = cls.get_users_col().find_one({'email': user_email.strip().lower()})
                if user_doc and 'batch_ids' in user_doc:
                    for b_id in user_doc.get('batch_ids', []):
                        allowed_batch_identifiers.add(str(b_id))
                        try:
                            b_obj = cls.get_batches_col().find_one({
                                '$or': [{'_id': ObjectId(b_id)}, {'_id': str(b_id)}]
                            })
                        except Exception:
                            b_obj = cls.get_batches_col().find_one({'_id': str(b_id)})

                        if b_obj:
                            if b_obj.get('code'):
                                allowed_batch_identifiers.add(b_obj.get('code').strip())
                                allowed_batch_identifiers.add(b_obj.get('code').strip().upper())
                            if b_obj.get('name'):
                                allowed_batch_identifiers.add(b_obj.get('name').strip())

            if batch_code and batch_code != 'undefined':
                allowed_batch_identifiers.add(batch_code.strip())
                allowed_batch_identifiers.add(batch_code.strip().upper())

            if allowed_batch_identifiers:
                query['batch_code'] = {'$in': list(allowed_batch_identifiers)}
            else:
                return []

        elif status_filter and status_filter.lower() != 'all':
            query['status'] = status_filter

        cursor = cls.get_assignments_col().find(query).sort('_id', -1)
        assignments = []

        for doc in cursor:
            assign_id = str(doc.get('_id'))
            submissions_count = cls.get_submissions_col().count_documents({'assignment_id': assign_id})

            # Check if student has already submitted
            student_submission = None
            if user_email and user_role.lower() == 'student':
                sub_doc = cls.get_submissions_col().find_one({
                    'assignment_id': assign_id,
                    'student_email': user_email.strip().lower()
                })
                if sub_doc:
                    student_submission = {
                        'submission_id': str(sub_doc['_id']),
                        'submitted_at': sub_doc.get('submitted_at'),
                        'is_late': sub_doc.get('is_late', False),
                        'submission_status': sub_doc.get('submission_status'),
                        'obtained_marks': sub_doc.get('obtained_marks'),
                        'grade': sub_doc.get('grade'),
                        'feedback': sub_doc.get('feedback', '')
                    }

            assignments.append({
                'assignment_id': assign_id,
                'title': doc.get('title', 'Untitled Assignment'),
                'course_name': doc.get('course_name', 'General Curriculum'),
                'batch_code': doc.get('batch_code', ''),
                'description': doc.get('description', ''),
                'total_marks': doc.get('total_marks', 100),
                'passing_marks': doc.get('passing_marks', 40),
                'due_date': str(doc.get('due_date', '')),
                'status': doc.get('status', 'Draft'),
                'instructions': doc.get('instructions', ''),
                'attachments': doc.get('attachments', []),
                'total_submissions': submissions_count,
                'student_submission': student_submission,
                'created_at': str(doc.get('created_at', ''))
            })

        return assignments

    @classmethod
    def create_assignment(cls, data, trainer_email='trainer@aieducation.com'):
        """Inserts a new assignment document into MongoDB."""
        doc = AssignmentMongoModel.create_document(data=data, created_by=trainer_email)
        cls.get_assignments_col().insert_one(doc)
        return doc

    @classmethod
    def get_assignment_by_id(cls, assignment_id):
        """Retrieves assignment document by string ID or ObjectId."""
        try:
            query = {'$or': [{'_id': assignment_id}, {'_id': ObjectId(assignment_id)}]}
        except Exception:
            query = {'_id': assignment_id}

        doc = cls.get_assignments_col().find_one(query)
        if doc:
            doc['assignment_id'] = str(doc['_id'])
            doc['_id'] = str(doc['_id'])
        return doc

    @classmethod
    def update_assignment(cls, assignment_id, data):
        """Updates an existing assignment document."""
        now_iso = datetime.now(timezone.utc).isoformat()
        update_data = {
            'title': data.get('title'),
            'course_name': data.get('course_name'),
            'batch_code': data.get('batch_code'),
            'description': data.get('description'),
            'total_marks': int(data.get('total_marks', 100)),
            'passing_marks': int(data.get('passing_marks', 40)),
            'due_date': data.get('due_date'),
            'status': data.get('status', 'Draft'),
            'instructions': data.get('instructions'),
            'attachments': data.get('attachments', []),
            'updated_at': now_iso
        }

        try:
            query = {'$or': [{'_id': assignment_id}, {'_id': ObjectId(assignment_id)}]}
        except Exception:
            query = {'_id': assignment_id}

        res = cls.get_assignments_col().update_one(query, {'$set': update_data})
        return res.modified_count > 0 or res.matched_count > 0

    @classmethod
    def toggle_status(cls, assignment_id, new_status):
        """Updates status (e.g. Published, Open, Closed, Completed)."""
        try:
            query = {'$or': [{'_id': assignment_id}, {'_id': ObjectId(assignment_id)}]}
        except Exception:
            query = {'_id': assignment_id}

        res = cls.get_assignments_col().update_one(
            query,
            {'$set': {'status': new_status, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0 or res.matched_count > 0

    @classmethod
    def delete_assignment(cls, assignment_id):
        """Deletes assignment and associated submission records."""
        try:
            query = {'$or': [{'_id': assignment_id}, {'_id': ObjectId(assignment_id)}]}
        except Exception:
            query = {'_id': assignment_id}

        res = cls.get_assignments_col().delete_one(query)
        cls.get_submissions_col().delete_many({'assignment_id': str(assignment_id)})
        return res.deleted_count > 0

    @classmethod
    def submit_assignment(cls, assignment_id, data):
        """Saves student submission and automatically flags late status if submitted past due date."""
        assignment = cls.get_assignment_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.get('status') in ['Closed', 'Draft']:
            raise ValueError("This assignment is closed for new submissions.")

        now = datetime.now(timezone.utc)
        due_str = assignment.get('due_date')

        # Check deadline
        is_late = False
        if due_str:
            try:
                due_dt = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
                if now > due_dt:
                    is_late = True
            except Exception:
                pass

        doc = AssignmentSubmissionMongoModel.create_document(
            assignment_id=str(assignment_id),
            student_name=data.get('student_name'),
            student_email=data.get('student_email'),
            submission_text=data.get('submission_text', ''),
            file_urls=data.get('file_urls', []),
            is_late=is_late
        )

        # Upsert submission so student can resubmit
        cls.get_submissions_col().replace_one(
            {
                'assignment_id': str(assignment_id),
                'student_email': data.get('student_email').lower().strip()
            },
            doc,
            upsert=True
        )
        return doc

    @classmethod
    def get_assignment_submissions_roster(cls, assignment_id):
        """Returns roster of submissions for an assignment."""
        cursor = cls.get_submissions_col().find({'assignment_id': str(assignment_id)}).sort('submitted_at', -1)
        submissions = []

        for doc in cursor:
            submissions.append({
                'submission_id': str(doc.get('_id')),
                'assignment_id': doc.get('assignment_id'),
                'student_name': doc.get('student_name', 'Student'),
                'student_email': doc.get('student_email', ''),
                'submission_text': doc.get('submission_text', ''),
                'file_urls': doc.get('file_urls', []),
                'submitted_at': doc.get('submitted_at', ''),
                'is_late': doc.get('is_late', False),
                'submission_status': doc.get('submission_status', 'Pending Evaluation'),
                'obtained_marks': doc.get('obtained_marks'),
                'percentage': doc.get('percentage'),
                'grade': doc.get('grade'),
                'feedback': doc.get('feedback', ''),
                'evaluated_at': doc.get('evaluated_at')
            })

        return submissions

    @classmethod
    def grade_submission(cls, submission_id, data, evaluator_email="trainer@aieducation.com"):
        """Evaluates student submission, records marks, feedback, and letter grade."""
        try:
            query = {'$or': [{'_id': submission_id}, {'_id': ObjectId(submission_id)}]}
        except Exception:
            query = {'_id': submission_id}

        submission = cls.get_submissions_col().find_one(query)
        if not submission:
            raise ValueError("Submission not found")

        assignment = cls.get_assignment_by_id(submission.get('assignment_id'))
        total_marks = assignment.get('total_marks', 100) if assignment else 100
        passing_marks = assignment.get('passing_marks', 40) if assignment else 40

        obtained_marks = int(data.get('obtained_marks', 0))
        percentage = round((obtained_marks / total_marks) * 100, 1) if total_marks > 0 else 0.0

        if percentage >= 90:
            grade = 'A+'
        elif percentage >= 75:
            grade = 'A'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 50:
            grade = 'C'
        elif percentage >= passing_marks:
            grade = 'D'
        else:
            grade = 'F'

        update_fields = {
            'obtained_marks': obtained_marks,
            'percentage': percentage,
            'grade': grade,
            'feedback': data.get('feedback', '').strip(),
            'submission_status': 'Graded',
            'evaluated_at': datetime.now(timezone.utc).isoformat(),
            'evaluated_by': evaluator_email
        }

        res = cls.get_submissions_col().update_one(query, {'$set': update_fields})
        return res.modified_count > 0 or res.matched_count > 0

    @classmethod
    def get_assignment_analytics(cls, assignment_id):
        """Calculates submission metrics and grading overview."""
        assignment = cls.get_assignment_by_id(assignment_id)
        if not assignment:
            return None

        batch_code = assignment.get('batch_code')
        submissions = cls.get_assignment_submissions_roster(assignment_id)

        total_enrolled = 25
        if batch_code:
            try:
                batch_doc = cls.get_batches_col().find_one({
                    '$or': [{'code': batch_code}, {'name': batch_code}, {'_id': ObjectId(batch_code)},
                            {'_id': batch_code}]
                })
            except Exception:
                batch_doc = cls.get_batches_col().find_one({
                    '$or': [{'code': batch_code}, {'name': batch_code}, {'_id': batch_code}]
                })

            if batch_doc:
                b_id_str = str(batch_doc['_id'])
                total_enrolled = cls.get_users_col().count_documents({
                    'batch_ids': {'$in': [b_id_str, ObjectId(b_id_str) if ObjectId.is_valid(b_id_str) else b_id_str]}
                })

        total_submitted = len(submissions)
        late_count = sum(1 for s in submissions if s.get('is_late'))
        graded_count = sum(1 for s in submissions if s.get('submission_status') == 'Graded')
        pending_count = total_submitted - graded_count

        scores = [s['obtained_marks'] for s in submissions if s.get('obtained_marks') is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        highest_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0

        submission_rate = round((total_submitted / total_enrolled) * 100, 1) if total_enrolled > 0 else 0.0

        return {
            'assignment_id': str(assignment_id),
            'title': assignment.get('title'),
            'batch_code': batch_code,
            'total_enrolled_students': total_enrolled,
            'total_submissions': total_submitted,
            'late_submissions': late_count,
            'graded_submissions': graded_count,
            'pending_evaluations': pending_count,
            'submission_rate': f"{submission_rate}%",
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score
        }