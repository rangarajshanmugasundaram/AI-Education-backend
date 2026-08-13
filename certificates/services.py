from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db
from .mongo_models import CertificateMongoModel


class CertificateService:
    @staticmethod
    def get_certificates_col():
        return db['certificates']

    @staticmethod
    def get_users_col():
        return db['users']

    @classmethod
    def get_all_certificates(cls, user_role='Trainer', user_email=None, search_query=None):
        """Fetches certificate roster based on role."""
        query = {}

        if user_role and user_role.lower() == 'student' and user_email:
            query['student_email'] = user_email.strip().lower()

        if search_query:
            regex_query = {'$regex': search_query.strip(), '$options': 'i'}
            query['$or'] = [
                {'student_name': regex_query},
                {'student_email': regex_query},
                {'course_name': regex_query},
                {'certificate_id': regex_query}
            ]

        cursor = cls.get_certificates_col().find(query).sort('created_at', -1)
        certs = []

        for doc in cursor:
            certs.append({
                'certificate_id': doc.get('certificate_id'),
                'student_name': doc.get('student_name', ''),
                'student_email': doc.get('student_email', ''),
                'course_name': doc.get('course_name', ''),
                'batch_code': doc.get('batch_code', ''),
                'completion_date': str(doc.get('completion_date', '')),
                'issue_date': str(doc.get('issue_date', '')),
                'grade_achieved': doc.get('grade_achieved', 'Pass'),
                'status': doc.get('status', 'Valid'),
                'created_at': str(doc.get('created_at', ''))
            })

        return certs

    @classmethod
    def generate_certificate(cls, data, issued_by="admin@aieducation.com"):
        """Generates a new certificate document."""
        doc = CertificateMongoModel.create_document(data=data, issued_by=issued_by)
        cls.get_certificates_col().insert_one(doc)
        return doc

    @classmethod
    def verify_certificate(cls, certificate_id):
        """Verifies if a certificate ID is valid."""
        clean_id = certificate_id.strip().upper()

        doc = cls.get_certificates_col().find_one({
            '$or': [
                {'certificate_id': clean_id},
                {'certificate_id': certificate_id.strip()}
            ]
        })

        if not doc:
            return {'is_valid': False, 'message': 'Certificate ID not found'}

        return {
            'is_valid': doc.get('status') == 'Valid',
            'certificate': {
                'certificate_id': doc.get('certificate_id'),
                'student_name': doc.get('student_name'),
                'student_email': doc.get('student_email'),
                'course_name': doc.get('course_name'),
                'batch_code': doc.get('batch_code'),
                'completion_date': str(doc.get('completion_date')),
                'issue_date': str(doc.get('issue_date')),
                'grade_achieved': doc.get('grade_achieved', 'Pass'),
                'status': doc.get('status', 'Valid')
            }
        }

    @classmethod
    def get_certificate_by_id(cls, certificate_id):
        """Fetches certificate record for PDF generation."""
        clean_id = certificate_id.strip()
        doc = cls.get_certificates_col().find_one({
            '$or': [
                {'certificate_id': clean_id.upper()},
                {'certificate_id': clean_id}
            ]
        })
        return doc