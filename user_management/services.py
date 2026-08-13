import bcrypt
import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from db_connection import db


class UserService:
    @staticmethod
    def get_users_collection():
        return db['users']

    @classmethod
    def get_all_users(cls, search_query=None, role_filter=None, status_filter=None):
        collection = cls.get_users_collection()
        query = {}

        # Search filter (Name or Email)
        if search_query:
            regex_pattern = re.compile(search_query, re.IGNORECASE)
            query['$or'] = [
                {'name': regex_pattern},
                {'first_name': regex_pattern},
                {'last_name': regex_pattern},
                {'email': regex_pattern}
            ]

        # Role filter
        if role_filter and role_filter.lower() != 'all':
            query['$or'] = [
                {'role': {'$regex': f'^{role_filter}$', '$options': 'i'}},
                {'previous_role': {'$regex': f'^{role_filter}$', '$options': 'i'}}
            ]

        # Status filter
        if status_filter is not None and status_filter != 'all':
            query['isActive'] = (str(status_filter).lower() == 'true')

        cursor = collection.find(query).sort('_id', -1)
        users = []
        for doc in cursor:
            full_name = doc.get('name')
            if not full_name:
                f_name = doc.get('first_name', '')
                l_name = doc.get('last_name', '')
                full_name = f"{f_name} {l_name}".strip() or doc.get('email', 'User')

            created = doc.get('createdAt') or doc.get('created_at')
            created_str = created.isoformat() if isinstance(created, datetime) else str(created or '')

            # Display original role in User Management table even when inactive
            current_role = doc.get('role', 'Student')
            display_role = doc.get('previous_role') if current_role == 'Inactive' else current_role

            users.append({
                '_id': str(doc['_id']),
                'name': full_name,
                'first_name': doc.get('first_name', ''),
                'last_name': doc.get('last_name', ''),
                'email': doc.get('email', ''),
                'role': display_role,
                'isActive': doc.get('isActive', True),
                'createdAt': created_str
            })
        return users

    @classmethod
    def create_user(cls, data):
        collection = cls.get_users_collection()
        email_clean = data['email'].strip().lower()

        # Check if user already exists
        if collection.find_one({'email': email_clean}):
            raise ValueError("A user with this email address already exists.")

        full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        now = datetime.now(timezone.utc)

        # Hash password using bcrypt
        raw_password = data['password']
        hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_role = data.get('role', 'Student')
        user_doc = {
            'name': full_name,
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'email': email_clean,
            'password': hashed_password,
            'role': user_role,
            'previous_role': user_role,
            'isActive': data.get('isActive', True),
            'createdAt': now,
            'updatedAt': now
        }

        result = collection.insert_one(user_doc)
        user_doc['_id'] = str(result.inserted_id)
        user_doc['createdAt'] = now.isoformat()
        return user_doc

    @classmethod
    def update_user(cls, user_id, data):
        collection = cls.get_users_collection()
        now = datetime.now(timezone.utc)

        update_fields = {'updatedAt': now}
        if 'first_name' in data or 'last_name' in data:
            f_name = data.get('first_name', '')
            l_name = data.get('last_name', '')
            update_fields['first_name'] = f_name
            update_fields['last_name'] = l_name
            update_fields['name'] = f"{f_name} {l_name}".strip()

        if 'role' in data:
            update_fields['role'] = data['role']
            update_fields['previous_role'] = data['role']
        if 'isActive' in data:
            update_fields['isActive'] = data['isActive']

        try:
            query = {'_id': ObjectId(user_id)}
        except Exception:
            query = {'_id': user_id}

        result = collection.update_one(query, {'$set': update_fields})
        return result.modified_count > 0 or result.matched_count > 0

    @classmethod
    def toggle_status(cls, user_id):
        collection = cls.get_users_collection()
        try:
            query = {'_id': ObjectId(user_id)}
        except Exception:
            query = {'_id': user_id}

        user = collection.find_one(query)
        if not user:
            return None

        current_status = user.get('isActive', True)
        new_status = not current_status

        if not new_status:
            # 🛑 DEACTIVATION (Soft Delete)
            # Store current active role into 'previous_role' and set active role to 'Inactive'
            current_role = user.get('role', 'Student')
            previous_role = current_role if current_role != 'Inactive' else user.get('previous_role', 'Student')

            update_payload = {
                'isActive': False,
                'role': 'Inactive',
                'previous_role': previous_role,
                'updatedAt': datetime.now(timezone.utc)
            }
        else:
            # 🌟 REACTIVATION
            # Restore original role from 'previous_role'
            restored_role = user.get('previous_role', 'Student')
            if restored_role == 'Inactive':
                restored_role = 'Student'

            update_payload = {
                'isActive': True,
                'role': restored_role,
                'updatedAt': datetime.now(timezone.utc)
            }

        collection.update_one(query, {'$set': update_payload})
        return new_status

    @classmethod
    def reset_password(cls, user_id, new_password):
        collection = cls.get_users_collection()
        try:
            query = {'_id': ObjectId(user_id)}
        except Exception:
            query = {'_id': user_id}

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        result = collection.update_one(
            query,
            {'$set': {'password': hashed_password, 'updatedAt': datetime.now(timezone.utc)}}
        )
        return result.matched_count > 0

    @classmethod
    def delete_user(cls, user_id):
        collection = cls.get_users_collection()
        try:
            query = {'_id': ObjectId(user_id)}
        except Exception:
            query = {'_id': user_id}

        result = collection.delete_one(query)
        return result.deleted_count > 0