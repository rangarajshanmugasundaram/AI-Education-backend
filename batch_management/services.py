import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db


class BatchService:
    @staticmethod
    def get_batches_col():
        return db['batches']

    @staticmethod
    def get_users_col():
        return db['users']

    @staticmethod
    def get_courses_col():
        return db['courses']

    @classmethod
    def get_all_batches(cls, search_query=None, status_filter=None, include_archived=False):
        batches_col = cls.get_batches_col()
        users_col = cls.get_users_col()
        courses_col = cls.get_courses_col()
        query = {}

        if not include_archived and status_filter and status_filter.lower() not in ['all', 'archived']:
            query['isArchived'] = {'$ne': True}

        if search_query:
            regex_pattern = re.compile(search_query, re.IGNORECASE)
            query['$or'] = [
                {'name': regex_pattern},
                {'code': regex_pattern}
            ]

        if status_filter and status_filter.lower() != 'all':
            if status_filter.lower() == 'archived':
                query['isArchived'] = True
            else:
                query['status'] = {'$regex': f'^{status_filter}$', '$options': 'i'}

        cursor = batches_col.find(query).sort('_id', -1)
        batches = []

        for doc in cursor:
            batch_id_str = str(doc['_id'])

            # Resolve Course info
            course_id = doc.get('course_id')
            course_name, course_code = 'Unassigned', ''
            if course_id:
                try:
                    c_obj = courses_col.find_one({'_id': ObjectId(course_id)})
                except Exception:
                    c_obj = courses_col.find_one({'_id': course_id})
                if c_obj:
                    course_name = c_obj.get('title', '')
                    course_code = c_obj.get('code', '')

            # Resolve Trainer info
            trainer_id = doc.get('trainer_id')
            trainer_name, trainer_email = 'Unassigned', ''
            if trainer_id:
                try:
                    t_obj = users_col.find_one({'_id': ObjectId(trainer_id)})
                except Exception:
                    t_obj = users_col.find_one({'_id': trainer_id})
                if t_obj:
                    trainer_name = t_obj.get(
                        'name') or f"{t_obj.get('first_name', '')} {t_obj.get('last_name', '')}".strip()
                    trainer_email = t_obj.get('email', '')

            # Calculate Enrolled Students
            enrolled_count = users_col.count_documents({
                'batch_ids': batch_id_str,
                'role': {'$regex': '^student$', '$options': 'i'}
            })

            created = doc.get('createdAt')
            created_str = created.isoformat() if isinstance(created, datetime) else str(created or '')

            batches.append({
                '_id': batch_id_str,
                'name': doc.get('name', ''),
                'code': doc.get('code', ''),
                'course_id': str(course_id) if course_id else None,
                'course_name': course_name,
                'course_code': course_code,
                'trainer_id': str(trainer_id) if trainer_id else None,
                'trainer_name': trainer_name,
                'trainer_email': trainer_email,
                'max_capacity': doc.get('max_capacity', 30),
                'enrolled_students_count': enrolled_count,
                'start_date': str(doc.get('start_date', '')),
                'end_date': str(doc.get('end_date', '')),
                'status': doc.get('status', 'Active'),
                'isArchived': doc.get('isArchived', False),
                'createdAt': created_str
            })

        return batches

    @classmethod
    def get_batch_by_id(cls, batch_id):
        batches_col = cls.get_batches_col()
        users_col = cls.get_users_col()
        courses_col = cls.get_courses_col()

        try:
            query = {'_id': ObjectId(batch_id)}
        except Exception:
            query = {'_id': batch_id}

        doc = batches_col.find_one(query)
        if not doc:
            return None

        batch_id_str = str(doc['_id'])

        # Resolve Course
        course_id = doc.get('course_id')
        course_name, course_code = 'Unassigned', ''
        if course_id:
            try:
                c_obj = courses_col.find_one({'_id': ObjectId(course_id)})
            except Exception:
                c_obj = courses_col.find_one({'_id': course_id})
            if c_obj:
                course_name = c_obj.get('title', '')
                course_code = c_obj.get('code', '')

        # Resolve Trainer
        trainer_id = doc.get('trainer_id')
        trainer_name, trainer_email = 'Unassigned', ''
        if trainer_id:
            try:
                t_obj = users_col.find_one({'_id': ObjectId(trainer_id)})
            except Exception:
                t_obj = users_col.find_one({'_id': trainer_id})
            if t_obj:
                trainer_name = t_obj.get(
                    'name') or f"{t_obj.get('first_name', '')} {t_obj.get('last_name', '')}".strip()
                trainer_email = t_obj.get('email', '')

        # Fetch Enrolled Students List
        students_cursor = users_col.find({
            'batch_ids': batch_id_str,
            'role': {'$regex': '^student$', '$options': 'i'}
        })
        enrolled_students = []
        for s in students_cursor:
            enrolled_students.append({
                '_id': str(s['_id']),
                'name': s.get('name') or f"{s.get('first_name', '')} {s.get('last_name', '')}".strip(),
                'email': s.get('email', ''),
                'isActive': s.get('isActive', True)
            })

        created = doc.get('createdAt')
        created_str = created.isoformat() if isinstance(created, datetime) else str(created or '')

        return {
            '_id': batch_id_str,
            'name': doc.get('name', ''),
            'code': doc.get('code', ''),
            'course_id': str(course_id) if course_id else None,
            'course_name': course_name,
            'course_code': course_code,
            'trainer_id': str(trainer_id) if trainer_id else None,
            'trainer_name': trainer_name,
            'trainer_email': trainer_email,
            'max_capacity': doc.get('max_capacity', 30),
            'enrolled_students': enrolled_students,
            'enrolled_students_count': len(enrolled_students),
            'start_date': str(doc.get('start_date', '')),
            'end_date': str(doc.get('end_date', '')),
            'status': doc.get('status', 'Active'),
            'isArchived': doc.get('isArchived', False),
            'createdAt': created_str
        }

    @classmethod
    def create_batch(cls, data):
        batches_col = cls.get_batches_col()
        code_clean = data['code'].strip().upper()

        if batches_col.find_one({'code': code_clean}):
            raise ValueError("A batch with this code already exists.")

        now = datetime.now(timezone.utc)
        doc = {
            'name': data['name'].strip(),
            'code': code_clean,
            'course_id': data.get('course_id'),
            'trainer_id': data.get('trainer_id'),
            'max_capacity': data.get('max_capacity', 30),
            'start_date': data.get('start_date', ''),
            'end_date': data.get('end_date', ''),
            'status': data.get('status', 'Active'),
            'isArchived': False,
            'createdAt': now,
            'updatedAt': now
        }

        result = batches_col.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        doc['createdAt'] = now.isoformat()
        return doc

    @classmethod
    def update_batch(cls, batch_id, data):
        batches_col = cls.get_batches_col()
        now = datetime.now(timezone.utc)
        update_fields = {'updatedAt': now}

        for field in ['name', 'code', 'course_id', 'trainer_id', 'max_capacity', 'start_date', 'end_date', 'status',
                      'isArchived']:
            if field in data:
                if field == 'code':
                    update_fields[field] = data[field].strip().upper()
                else:
                    update_fields[field] = data[field]

        try:
            query = {'_id': ObjectId(batch_id)}
        except Exception:
            query = {'_id': batch_id}

        result = batches_col.update_one(query, {'$set': update_fields})
        return result.modified_count > 0 or result.matched_count > 0

    @classmethod
    def allocate_students(cls, batch_id, student_ids):
        users_col = cls.get_users_col()
        batch_id_str = str(batch_id)

        # 1. Remove this batch_id from all students currently in the batch
        users_col.update_many(
            {'batch_ids': batch_id_str},
            {'$pull': {'batch_ids': batch_id_str}}
        )

        # 2. Add batch_id to selected student IDs
        if student_ids:
            obj_ids = []
            for sid in student_ids:
                try:
                    obj_ids.append(ObjectId(sid))
                except Exception:
                    obj_ids.append(sid)

            users_col.update_many(
                {'_id': {'$in': obj_ids}},
                {'$addToSet': {'batch_ids': batch_id_str}}
            )

        return True

    @classmethod
    def allocate_trainer(cls, batch_id, trainer_id):
        batches_col = cls.get_batches_col()
        try:
            query = {'_id': ObjectId(batch_id)}
        except Exception:
            query = {'_id': batch_id}

        result = batches_col.update_one(
            query,
            {'$set': {'trainer_id': trainer_id, 'updatedAt': datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0 or result.matched_count > 0

    @classmethod
    def get_batch_stats(cls, batch_id=None):
        batches_col = cls.get_batches_col()
        users_col = cls.get_users_col()

        total_batches = batches_col.count_documents({})
        active_batches = batches_col.count_documents({'isArchived': False, 'status': 'Active'})
        total_enrolled = users_col.count_documents(
            {'batch_ids': {'$exists': True, '$ne': []}, 'role': {'$regex': '^student$', '$options': 'i'}})
        total_students = users_col.count_documents({'role': {'$regex': '^student$', '$options': 'i'}})

        return {
            'total_batches': total_batches,
            'active_batches': active_batches,
            'total_enrolled_students': total_enrolled,
            'total_students': total_students
        }