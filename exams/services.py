import uuid
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db
from .mongo_models import ExamMongoModel, ExamResultMongoModel


class ExamService:
    @staticmethod
    def get_exams_col():
        return db['exams']

    @staticmethod
    def get_results_col():
        return db['exam_results']

    @staticmethod
    def get_batches_col():
        return db['batches']

    @classmethod
    def get_all_exams(cls, user_role='Trainer', batch_code=None, status_filter=None):
        """Fetches exams from MongoDB 'exams' collection with RBAC status filtering."""
        query = {}

        # Students can only access Published or Ongoing exams
        if user_role.lower() == 'student':
            query['status'] = {'$in': ['Published', 'Ongoing']}
            if batch_code:
                query['batch_code'] = batch_code
        elif status_filter and status_filter.lower() != 'all':
            query['status'] = status_filter

        cursor = cls.get_exams_col().find(query).sort('_id', -1)
        exams = []

        for doc in cursor:
            exam_id = str(doc.get('_id'))
            attempts_count = cls.get_results_col().count_documents({'exam_id': exam_id})

            exams.append({
                'exam_id': exam_id,
                'title': doc.get('title', 'Untitled Exam'),
                'course_name': doc.get('course_name', 'General Curriculum'),
                'batch_code': doc.get('batch_code', 'BATCH-2026-A'),
                'duration_minutes': doc.get('duration_minutes', 60),
                'total_marks': doc.get('total_marks', 100),
                'passing_marks': doc.get('passing_marks', 40),
                'scheduled_date': str(doc.get('scheduled_date', '')),
                'status': doc.get('status', 'Draft'),
                'total_questions': len(doc.get('questions', [])),
                'total_attempts': attempts_count,
                'created_at': str(doc.get('created_at', ''))
            })

        return exams

    @classmethod
    def create_exam(cls, data, trainer_email='trainer@aieducation.com'):
        """Inserts a new exam directly into MongoDB."""
        doc = ExamMongoModel.create_document(data=data, created_by=trainer_email)
        cls.get_exams_col().insert_one(doc)
        return doc

    @classmethod
    def get_exam_by_id(cls, exam_id):
        """Retrieves a document from MongoDB by string ID or ObjectId."""
        try:
            query = {'$or': [{'_id': exam_id}, {'_id': ObjectId(exam_id)}]}
        except Exception:
            query = {'_id': exam_id}

        exam = cls.get_exams_col().find_one(query)
        if exam:
            exam['_id'] = str(exam['_id'])
        return exam

    @classmethod
    def update_exam(cls, exam_id, data):
        """Updates an exam document in MongoDB."""
        now_iso = datetime.now(timezone.utc).isoformat()
        update_data = {
            'title': data.get('title'),
            'course_name': data.get('course_name'),
            'batch_code': data.get('batch_code'),
            'duration_minutes': int(data.get('duration_minutes', 60)),
            'total_marks': int(data.get('total_marks', 100)),
            'passing_marks': int(data.get('passing_marks', 40)),
            'scheduled_date': data.get('scheduled_date'),
            'status': data.get('status', 'Draft'),
            'updated_at': now_iso
        }

        if 'questions' in data:
            update_data['questions'] = data['questions']

        res = cls.get_exams_col().update_one({'_id': exam_id}, {'$set': update_data})
        return res.modified_count > 0 or res.matched_count > 0

    @classmethod
    def toggle_publish_status(cls, exam_id, new_status):
        """Updates status between Published, Unpublished, Draft, etc."""
        res = cls.get_exams_col().update_one(
            {'_id': exam_id},
            {'$set': {'status': new_status, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0 or res.matched_count > 0

    @classmethod
    def delete_exam(cls, exam_id):
        """Deletes exam and associated result records from MongoDB."""
        res = cls.get_exams_col().delete_one({'_id': exam_id})
        cls.get_results_col().delete_many({'exam_id': exam_id})
        return res.deleted_count > 0

    @classmethod
    def submit_student_exam(cls, exam_id, submission_data):
        """Auto-grades submission and saves result to MongoDB 'exam_results' collection."""
        exam = cls.get_exam_by_id(exam_id)
        if not exam:
            raise ValueError("Exam not found")

        student_answers = submission_data.get('answers', {})
        questions = exam.get('questions', [])

        obtained_marks = 0
        total_exam_marks = exam.get('total_marks', 100)
        passing_marks = exam.get('passing_marks', 40)

        for q in questions:
            q_id = q.get('question_id')
            correct_idx = q.get('correct_option_index')
            q_marks = q.get('marks', 1)

            if q_id in student_answers and student_answers[q_id] == correct_idx:
                obtained_marks += q_marks

        percentage = round((obtained_marks / total_exam_marks) * 100, 1) if total_exam_marks > 0 else 0.0
        is_passed = obtained_marks >= passing_marks

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

        result_doc = ExamResultMongoModel.create_document(
            exam_id=exam_id,
            student_name=submission_data.get('student_name'),
            student_email=submission_data.get('student_email'),
            total_marks=total_exam_marks,
            obtained_marks=obtained_marks,
            percentage=percentage,
            grade=grade,
            is_passed=is_passed
        )

        cls.get_results_col().insert_one(result_doc)
        return result_doc

    @classmethod
    def get_exam_results_summary(cls, exam_id):
        """Fetches student result summaries from MongoDB."""
        cursor = cls.get_results_col().find({'exam_id': exam_id}).sort('submitted_at', -1)
        results = []

        for doc in cursor:
            results.append({
                'result_id': str(doc.get('_id')),
                'exam_id': doc.get('exam_id'),
                'student_name': doc.get('student_name', 'Student'),
                'student_email': doc.get('student_email', ''),
                'total_marks': doc.get('total_marks', 100),
                'obtained_marks': doc.get('obtained_marks', 0),
                'percentage': doc.get('percentage', 0.0),
                'grade': doc.get('grade', 'F'),
                'status': doc.get('status', 'Failed'),
                'completion_status': doc.get('completion_status', 'Completed'),
                'submitted_at': doc.get('submitted_at', '')
            })

        return results

    @classmethod
    def get_exam_analytics(cls, exam_id):
        """Calculates performance analytics from MongoDB."""
        exam = cls.get_exam_by_id(exam_id)
        if not exam:
            return None

        batch_code = exam.get('batch_code')
        results = cls.get_exam_results_summary(exam_id)

        total_enrolled = 25
        if batch_code:
            batch_doc = cls.get_batches_col().find_one({'batch_code': batch_code})
            if batch_doc and 'student_ids' in batch_doc:
                total_enrolled = len(batch_doc['student_ids'])

        attempted_count = len(results)
        scores = [r['obtained_marks'] for r in results]
        passed_count = sum(1 for r in results if r['status'] == 'Passed')
        failed_count = attempted_count - passed_count

        avg_score = round(sum(scores) / attempted_count, 1) if attempted_count > 0 else 0.0
        highest_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0

        pass_pct = round((passed_count / attempted_count) * 100, 1) if attempted_count > 0 else 0.0
        fail_pct = round((failed_count / attempted_count) * 100, 1) if attempted_count > 0 else 0.0
        completion_rate = round((attempted_count / total_enrolled) * 100, 1) if total_enrolled > 0 else 0.0

        histogram = {'0-25%': 0, '26-50%': 0, '51-75%': 0, '76-100%': 0}
        for r in results:
            pct = r['percentage']
            if pct <= 25:
                histogram['0-25%'] += 1
            elif pct <= 50:
                histogram['26-50%'] += 1
            elif pct <= 75:
                histogram['51-75%'] += 1
            else:
                histogram['76-100%'] += 1

        return {
            'exam_id': exam_id,
            'title': exam.get('title'),
            'batch_code': batch_code,
            'total_enrolled_students': total_enrolled,
            'total_attempts': attempted_count,
            'completion_rate': f"{completion_rate}%",
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'pass_percentage': f"{pass_pct}%",
            'fail_percentage': f"{fail_pct}%",
            'score_distribution': histogram
        }