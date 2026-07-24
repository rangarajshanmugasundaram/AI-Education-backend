import datetime
import uuid
from django.conf import settings
import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from db_connection import db

collection = db['whiteboard']

JWT_SECRET = getattr(
    settings, 'SECRET_KEY', 'your-fallback-secret-key-change-in-production'
)
JWT_ALGORITHM = 'HS256'


def get_user_role_from_request(request):
  """Extracts role cleanly from JWT token, falling back to database query or headers."""
  auth_header = request.headers.get('Authorization', '')
  if auth_header and auth_header.startswith('Bearer '):
    token = auth_header.split(' ')[1]
    try:
      decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
      if decoded.get('role'):
        return decoded.get('role')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
      pass

  # Fallback: Query MongoDB user account by email header
  email = request.headers.get('X-User-Email', '').strip().lower()
  if email:
    user = db.users.find_one({'email': email})
    if user:
      return user.get('role', 'Student')

  return 'Student'


class WhiteboardSaveView(APIView):

  permission_classes = [AllowAny]

  def post(self, request):
    data = request.data
    if not data.get('session_id') or not data.get('drawing_data'):
      return Response(
          {'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST
      )

    doc = {
        'whiteboard_id': str(uuid.uuid4()),
        'session_id': data['session_id'],
        'user_email': request.headers.get('X-User-Email', 'unknown'),
        'drawing_data': data['drawing_data'],
        'tool_type': data.get('tool_type', 'pen'),
        'color': data.get('color', '#000000'),
        'stroke_width': int(data.get('stroke_width', 2)),
        'timestamp': datetime.datetime.utcnow(),
    }
    collection.insert_one(doc)
    return Response({'success': True}, status=status.HTTP_201_CREATED)


class WhiteboardDetailView(APIView):

  permission_classes = [AllowAny]

  def get(self, request, session_id):
    drawings = list(collection.find({'session_id': session_id}))
    for d in drawings:
      d['_id'] = str(d['_id'])
    return Response(drawings, status=status.HTTP_200_OK)

  def delete(self, request, session_id):
    user_role = get_user_role_from_request(request)

    # 🌟 Allow Trainers, Teachers, and Admins to clear the board
    normalized_role = str(user_role).strip().lower()
    if normalized_role not in ['trainer', 'teacher', 'admin']:
      return Response(
          {'error': 'Forbidden: Only Trainers can clear the board'},
          status=status.HTTP_403_FORBIDDEN,
      )

    collection.delete_many({'session_id': session_id})
    return Response(
        {'message': 'Board cleared successfully'}, status=status.HTTP_200_OK
    )