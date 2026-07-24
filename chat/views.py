import datetime
import uuid
from django.conf import settings
import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# Direct link to your active MongoDB client configuration
from db_connection import db

JWT_SECRET = getattr(
    settings, 'SECRET_KEY', 'your-fallback-secret-key-change-in-production'
)
JWT_ALGORITHM = 'HS256'


def validate_jwt_auth(request, allowed_roles=None):
  """Validates real JWT tokens from the Authorization header and extracts user payload."""
  if allowed_roles is None:
    allowed_roles = ['Student', 'Teacher', 'Trainer', 'Admin']

  auth_header = request.headers.get('Authorization', '')

  if not auth_header or not auth_header.startswith('Bearer '):
    return None, Response(
        {'detail': 'Unauthorized access: Missing Bearer token.'},
        status=status.HTTP_401_UNAUTHORIZED,
    )

  token = auth_header.split(' ')[1]

  try:
    # Decode real JWT signature
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    email = payload.get('email', '').strip().lower()
    role = payload.get('role', 'Student')
  except jwt.ExpiredSignatureError:
    return None, Response(
        {'detail': 'Unauthorized: Token has expired.'},
        status=status.HTTP_401_UNAUTHORIZED,
    )
  except jwt.InvalidTokenError:
    return None, Response(
        {'detail': 'Unauthorized: Invalid token signature.'},
        status=status.HTTP_401_UNAUTHORIZED,
    )

  # Check Role Authorization
  normalized_user_role = str(role).strip().lower()
  normalized_allowed_roles = [str(r).strip().lower() for r in allowed_roles]

  if normalized_user_role not in normalized_allowed_roles:
    return None, Response(
        {
            'detail': (
                'Forbidden: You do not have permission to access chat'
                ' resources.'
            )
        },
        status=status.HTTP_403_FORBIDDEN,
    )

  # Retrieve sender display name from DB if available
  user = db.users.find_one({'email': email})
  sender_name = (
      user.get('name') if user and user.get('name') else email.split('@')[0]
  )

  user_context = {
      'email': email,
      'role': role,
      'sender_name': sender_name.capitalize(),
  }
  return user_context, None


class SendMessageView(APIView):
  """POST /api/chat/send

  Saves the incoming message document directly into your MongoDB chat
  collection.
  """

  permission_classes = [AllowAny]

  def post(self, request):
    user, error_response = validate_jwt_auth(
        request, allowed_roles=['Student', 'Teacher', 'Trainer', 'Admin']
    )
    if error_response:
      return error_response

    session_id = request.data.get('session_id', '').strip()
    message = request.data.get('message', '').strip()
    message_type = request.data.get('message_type', 'Text')

    # Business Rule Validations
    if not session_id:
      return Response(
          {'session_id': 'Session ID cannot be empty.'},
          status=status.HTTP_400_BAD_REQUEST,
      )
    if not message:
      return Response(
          {'message': 'Message cannot be empty.'},
          status=status.HTTP_400_BAD_REQUEST,
      )
    if len(message) > 1000:
      return Response(
          {'message': 'Message size cannot exceed 1000 characters.'},
          status=status.HTTP_400_BAD_REQUEST,
      )

    # Build NoSQL document matching target requirements
    chat_document = {
        'message_id': str(uuid.uuid4()),
        'session_id': session_id,
        'sender_id': user['email'],
        'sender_name': user['sender_name'],
        'sender_role': user['role'],
        'message': message,
        'message_type': message_type,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'date_created': datetime.date.today().isoformat(),
    }

    # Write record directly into MongoDB 'chat' collection
    db.chat.insert_one(chat_document)

    # Remove internal PyMongo BSON _id field for JSON serialization
    chat_document.pop('_id', None)
    return Response(chat_document, status=status.HTTP_201_CREATED)


class SessionMessagesView(APIView):
  """GET /api/chat/session/<str:session_id>

  Fetches room logs out of MongoDB sorted in clean chronological order.
  """

  permission_classes = [AllowAny]

  def get(self, request, session_id):
    user, error_response = validate_jwt_auth(
        request, allowed_roles=['Student', 'Teacher', 'Trainer', 'Admin']
    )
    if error_response:
      return error_response

    cursor = db.chat.find({'session_id': session_id}).sort('timestamp', 1)

    messages = []
    for doc in cursor:
      doc.pop('_id', None)
      messages.append(doc)

    return Response(messages, status=status.HTTP_200_OK)


class DeleteMessageView(APIView):
  """DELETE /api/chat/<str:message_id>

  Removes target chat record from MongoDB collection (Trainers & Admins only).
  """

  permission_classes = [AllowAny]

  def delete(self, request, message_id):
    user, error_response = validate_jwt_auth(
        request, allowed_roles=['Trainer', 'Admin']
    )
    if error_response:
      return error_response

    result = db.chat.delete_one({'message_id': str(message_id)})

    if result.deleted_count > 0:
      return Response(
          {'detail': 'Message successfully removed from MongoDB records.'},
          status=status.HTTP_200_OK,
      )

    return Response(
        {'error': 'Message structural resource not found.'},
        status=status.HTTP_404_NOT_FOUND,
    )