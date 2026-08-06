import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db


class CourseService:
    @staticmethod
    def get_courses_collection():
        return db['courses']

    @staticmethod
    def get_users_collection():
        return db['users']

    @classmethod
    def get_all_courses(cls, search_query=None, category_filter=None, status_filter=None, include_archived=False):
        collection = cls.get_courses_collection()
        users_col = cls.get_users_collection()
        query = {}

        # 🌟 Include archived items if include_archived is True or status_filter is 'all' or 'archived'
        if not include_archived and status_filter and status_filter.lower() not in ['all', 'archived']:
            query['isArchived'] = {'$ne': True}

        if search_query:
            regex_pattern = re.compile(search_query, re.IGNORECASE)
            query['$or'] = [
                {'title': regex_pattern},
                {'code': regex_pattern},
                {'category': regex_pattern}
            ]

        if category_filter and category_filter.lower() != 'all':
            query['category'] = {'$regex': f'^{category_filter}$', '$options': 'i'}

        if status_filter and status_filter.lower() != 'all':
            if status_filter.lower() == 'archived':
                query['isArchived'] = True
            else:
                query['status'] = {'$regex': f'^{status_filter}$', '$options': 'i'}

        cursor = collection.find(query).sort('_id', -1)
        courses = []

        for doc in cursor:
            trainer_id = doc.get('trainer_id')
            trainer_name = 'Unassigned'
            trainer_email = ''

            if trainer_id:
                try:
                    trainer_obj = users_col.find_one({'_id': ObjectId(trainer_id)})
                except Exception:
                    trainer_obj = users_col.find_one({'_id': trainer_id})

                if trainer_obj:
                    trainer_name = trainer_obj.get('name') or f"{trainer_obj.get('first_name', '')} {trainer_obj.get('last_name', '')}".strip()
                    trainer_email = trainer_obj.get('email', '')

            created = doc.get('createdAt')
            created_str = created.isoformat() if isinstance(created, datetime) else str(created or '')

            courses.append({
                '_id': str(doc['_id']),
                'title': doc.get('title', ''),
                'code': doc.get('code', ''),
                'category': doc.get('category', 'General'),
                'description': doc.get('description', ''),
                'duration': doc.get('duration', ''),
                'prerequisites': doc.get('prerequisites', ''),
                'trainer_id': str(trainer_id) if trainer_id else None,
                'trainer_name': trainer_name,
                'trainer_email': trainer_email,
                'isArchived': doc.get('isArchived', False),
                'status': doc.get('status', 'Active'),
                'createdAt': created_str
            })

        return courses

    @classmethod
    def get_course_by_id(cls, course_id):
        collection = cls.get_courses_collection()
        users_col = cls.get_users_collection()

        try:
            query = {'_id': ObjectId(course_id)}
        except Exception:
            query = {'_id': course_id}

        doc = collection.find_one(query)
        if not doc:
            return None

        trainer_id = doc.get('trainer_id')
        trainer_name = 'Unassigned'
        trainer_email = ''

        if trainer_id:
            try:
                trainer_obj = users_col.find_one({'_id': ObjectId(trainer_id)})
            except Exception:
                trainer_obj = users_col.find_one({'_id': trainer_id})

            if trainer_obj:
                trainer_name = trainer_obj.get('name') or f"{trainer_obj.get('first_name', '')} {trainer_obj.get('last_name', '')}".strip()
                trainer_email = trainer_obj.get('email', '')

        created = doc.get('createdAt')
        created_str = created.isoformat() if isinstance(created, datetime) else str(created or '')

        return {
            '_id': str(doc['_id']),
            'title': doc.get('title', ''),
            'code': doc.get('code', ''),
            'category': doc.get('category', 'General'),
            'description': doc.get('description', ''),
            'duration': doc.get('duration', ''),
            'prerequisites': doc.get('prerequisites', ''),
            'trainer_id': str(trainer_id) if trainer_id else None,
            'trainer_name': trainer_name,
            'trainer_email': trainer_email,
            'isArchived': doc.get('isArchived', False),
            'status': doc.get('status', 'Active'),
            'createdAt': created_str
        }

    @classmethod
    def create_course(cls, data):
        collection = cls.get_courses_collection()
        code_clean = data['code'].strip().upper()

        if collection.find_one({'code': code_clean}):
            raise ValueError("A course with this code already exists.")

        now = datetime.now(timezone.utc)
        doc = {
            'title': data['title'].strip(),
            'code': code_clean,
            'category': data.get('category', 'General'),
            'description': data.get('description', ''),
            'duration': data.get('duration', ''),
            'prerequisites': data.get('prerequisites', ''),
            'trainer_id': data.get('trainer_id'),
            'isArchived': False,
            'status': data.get('status', 'Active'),
            'createdAt': now,
            'updatedAt': now
        }

        result = collection.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        doc['createdAt'] = now.isoformat()
        return doc

    @classmethod
    def update_course(cls, course_id, data):
        collection = cls.get_courses_collection()
        now = datetime.now(timezone.utc)
        update_fields = {'updatedAt': now}

        for field in ['title', 'code', 'category', 'description', 'duration', 'prerequisites', 'trainer_id', 'status', 'isArchived']:
            if field in data:
                if field == 'code':
                    update_fields[field] = data[field].strip().upper()
                else:
                    update_fields[field] = data[field]

        try:
            query = {'_id': ObjectId(course_id)}
        except Exception:
            query = {'_id': course_id}

        result = collection.update_one(query, {'$set': update_fields})
        return result.modified_count > 0 or result.matched_count > 0

    @classmethod
    def assign_trainer(cls, course_id, trainer_id):
        collection = cls.get_courses_collection()
        try:
            query = {'_id': ObjectId(course_id)}
        except Exception:
            query = {'_id': course_id}

        result = collection.update_one(
            query,
            {'$set': {'trainer_id': trainer_id, 'updatedAt': datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0 or result.matched_count > 0

    @classmethod
    def archive_course(cls, course_id):
        collection = cls.get_courses_collection()
        try:
            query = {'_id': ObjectId(course_id)}
        except Exception:
            query = {'_id': course_id}

        course = collection.find_one(query)
        if not course:
            return None

        new_archive_state = not course.get('isArchived', False)
        collection.update_one(
            query,
            {'$set': {'isArchived': new_archive_state, 'status': 'Archived' if new_archive_state else 'Active', 'updatedAt': datetime.now(timezone.utc)}}
        )
        return new_archive_state

    @classmethod
    def delete_course(cls, course_id):
        collection = cls.get_courses_collection()
        try:
            query = {'_id': ObjectId(course_id)}
        except Exception:
            query = {'_id': course_id}

        result = collection.delete_one(query)
        return result.deleted_count > 0

    @classmethod
    def get_course_stats(cls, course_id=None):
        courses_col = cls.get_courses_collection()
        users_col = cls.get_users_collection()

        total_courses = courses_col.count_documents({})
        active_courses = courses_col.count_documents({'isArchived': False, 'status': 'Active'})
        archived_courses = courses_col.count_documents({'isArchived': True})
        assigned_trainers = len(courses_col.distinct('trainer_id', {'trainer_id': {'$ne': None}}))
        total_students = users_col.count_documents({'role': {'$regex': '^student$', '$options': 'i'}})

        return {
            'total_courses': total_courses,
            'active_courses': active_courses,
            'archived_courses': archived_courses,
            'assigned_trainers': assigned_trainers,
            'total_students': total_students
        }