import uuid
from datetime import datetime, timezone


class CertificateMongoModel:
    """Document schema helper for MongoDB 'certificates' collection."""

    COLLECTION_NAME = 'certificates'

    @staticmethod
    def create_document(data, issued_by="admin@aieducation.com"):
        now_iso = datetime.now(timezone.utc).isoformat()

        # Generate clean human-readable Certificate Code (e.g., CERT-2026-A8B9C0)
        short_id = str(uuid.uuid4())[:8].upper()
        certificate_id = data.get("certificate_id") or f"CERT-{datetime.now().year}-{short_id}"

        return {
            "_id": certificate_id,
            "certificate_id": certificate_id,
            "student_name": data.get("student_name", "").strip(),
            "student_email": data.get("student_email", "").strip().lower(),
            "course_name": data.get("course_name", "").strip(),
            "batch_code": data.get("batch_code", "").strip(),
            "completion_date": data.get("completion_date", now_iso[:10]),
            "issue_date": data.get("issue_date", now_iso[:10]),
            "grade_achieved": data.get("grade_achieved", "Pass").strip(),
            "status": data.get("status", "Valid"),  # Valid, Revoked, Expired
            "issued_by": issued_by,
            "created_at": now_iso,
            "updated_at": now_iso
        }