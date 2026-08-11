import uuid
from datetime import datetime, timezone


class ExamMongoModel:
    """Document schema helper for MongoDB 'exams' collection."""

    COLLECTION_NAME = 'exams'

    @staticmethod
    def create_document(data, created_by="trainer@aieducation.com"):
        now_iso = datetime.now(timezone.utc).isoformat()
        exam_id = str(uuid.uuid4())

        # Format questions array safely
        questions = data.get('questions', [])
        formatted_questions = []
        for idx, q in enumerate(questions):
            formatted_questions.append({
                'question_id': q.get('question_id') or f"q_{idx + 1}",
                'question_text': q.get('question_text', ''),
                'options': q.get('options', []),
                'correct_option_index': int(q.get('correct_option_index', 0)),
                'marks': int(q.get('marks', 1))
            })

        return {
            "_id": exam_id,
            "id": exam_id,
            "title": data.get("title", "Untitled Exam"),
            "course_name": data.get("course_name", "General Curriculum"),
            "batch_code": data.get("batch_code", "BATCH-2026-A"),
            "duration_minutes": int(data.get("duration_minutes", 60)),
            "total_marks": int(data.get("total_marks", 100)),
            "passing_marks": int(data.get("passing_marks", 40)),
            "scheduled_date": data.get("scheduled_date") or now_iso,
            "status": data.get("status", "Draft"),  # Draft, Published, Ongoing, Completed, Unpublished
            "questions": formatted_questions,
            "created_by": created_by,
            "created_at": now_iso,
            "updated_at": now_iso,
        }


class ExamResultMongoModel:
    """Document schema helper for MongoDB 'exam_results' collection."""

    COLLECTION_NAME = 'exam_results'

    @staticmethod
    def create_document(exam_id, student_name, student_email, total_marks, obtained_marks, percentage, grade, is_passed):
        now_iso = datetime.now(timezone.utc).isoformat()

        return {
            "_id": str(uuid.uuid4()),
            "exam_id": str(exam_id),
            "student_name": student_name,
            "student_email": student_email.lower().strip(),
            "total_marks": int(total_marks),
            "obtained_marks": int(obtained_marks),
            "percentage": float(percentage),
            "grade": grade,  # A+, A, B, C, D, F
            "status": "Passed" if is_passed else "Failed",
            "completion_status": "Completed",
            "submitted_at": now_iso,
        }