import uuid
from datetime import datetime, timezone


class AssignmentMongoModel:
    """Document schema helper for MongoDB 'assignments' collection."""

    COLLECTION_NAME = 'assignments'

    @staticmethod
    def create_document(data, created_by="trainer@aieducation.com"):
        now_iso = datetime.now(timezone.utc).isoformat()
        assignment_id = str(uuid.uuid4())

        return {
            "_id": assignment_id,
            "id": assignment_id,
            "title": data.get("title", "Untitled Assignment").strip(),
            "course_name": data.get("course_name", "General Curriculum").strip(),
            "batch_code": data.get("batch_code", "").strip(),
            "description": data.get("description", "").strip(),
            "total_marks": int(data.get("total_marks", 100)),
            "passing_marks": int(data.get("passing_marks", 40)),
            "due_date": data.get("due_date", now_iso),
            "status": data.get("status", "Draft"),  # Draft, Published, Open, Closed, Completed
            "instructions": data.get("instructions", "").strip(),
            "attachments": data.get("attachments", []),
            "created_by": created_by,
            "created_at": now_iso,
            "updated_at": now_iso,
        }


class AssignmentSubmissionMongoModel:
    """Document schema helper for MongoDB 'assignment_submissions' collection."""

    COLLECTION_NAME = 'assignment_submissions'

    @staticmethod
    def create_document(assignment_id, student_name, student_email, submission_text="", file_urls=None, is_late=False):
        now_iso = datetime.now(timezone.utc).isoformat()
        submission_id = str(uuid.uuid4())

        return {
            "_id": submission_id,
            "id": submission_id,
            "assignment_id": str(assignment_id),
            "student_name": student_name.strip(),
            "student_email": student_email.lower().strip(),
            "submission_text": submission_text,
            "file_urls": file_urls or [],
            "submitted_at": now_iso,
            "is_late": is_late,
            "submission_status": "Late" if is_late else "Pending Evaluation",  # Pending Evaluation, Graded, Late
            "obtained_marks": None,
            "percentage": None,
            "grade": None,
            "feedback": "",
            "evaluated_at": None,
            "evaluated_by": None
        }