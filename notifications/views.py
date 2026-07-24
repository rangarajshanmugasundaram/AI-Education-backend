from datetime import datetime
import uuid
from db_connection import db  # PyMongo collection reference
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import NotificationSerializer


class NotificationListCreateView(APIView):
  """POST /api/notifications - Create Notification GET /api/notifications -

  Get All Notifications (Filtered)
  """

  def get(self, request):
    try:
      # Filtering query parameters
      priority = request.query_params.get('priority')
      recipient_type = request.query_params.get('recipient_type')
      read_status = request.query_params.get('read_status')
      search = request.query_params.get('search')

      query = {'is_deleted': {'$ne': True}}

      if priority:
        query['priority'] = priority
      if recipientType := recipient_type:
        query['recipient_type'] = recipientType
      if read_status is not None and read_status != '':
        query['read_status'] = read_status.lower() == 'true'
      if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'message': {'$regex': search, '$options': 'i'}},
        ]

      notifications = list(
          db.notifications.find(query, {'_id': 0}).sort('created_at', -1)
      )
      return Response(notifications, status=status.HTTP_200_OK)
    except Exception as e:
      return Response(
          {'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

  def post(self, request):
    serializer = NotificationSerializer(data=request.data)
    if serializer.is_valid():
      data = serializer.validated_data
      now_iso = datetime.utcnow().isoformat()

      notification_doc = {
          'id': str(uuid.uuid4()),
          'title': data['title'],
          'message': data['message'],
          'sender_id': request.data.get('sender_id', 'admin@aieducation.com'),
          'sender_role': request.data.get('sender_role', 'Trainer'),
          'recipient_type': data.get('recipient_type', 'All'),
          'recipient_id': data.get('recipient_id'),
          'batch_id': data.get('batch_id'),
          'priority': data.get('priority', 'Medium'),
          'read_status': False,
          'is_deleted': False,
          'created_at': now_iso,
          'updated_at': now_iso,
      }

      db.notifications.insert_one(notification_doc)
      # Remove Mongo _id before returning
      notification_doc.pop('_id', None)

      return Response(notification_doc, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyNotificationsView(APIView):
  """GET /api/notifications/my - Get Logged-in User Notifications."""

  def get(self, request):
    try:
      user_email = request.headers.get(
          'X-User-Email', request.query_params.get('email', '')
      ).lower()

      query = {
          'is_deleted': {'$ne': True},
          '$or': [{'recipient_type': 'All'}, {'recipient_id': user_email}],
      }

      notifications = list(
          db.notifications.find(query, {'_id': 0}).sort('created_at', -1)
      )
      return Response(notifications, status=status.HTTP_200_OK)
    except Exception as e:
      return Response(
          {'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )


class NotificationDetailView(APIView):
  """GET /api/notifications/<id>/ - Get Details PUT /api/notifications/<id>/ -

  Update DELETE /api/notifications/<id>/ - Soft Delete
  """

  def get(self, request, pk):
    notification = db.notifications.find_one({'id': pk}, {'_id': 0})
    if not notification:
      return Response(
          {'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND
      )
    return Response(notification, status=status.HTTP_200_OK)

  def put(self, request, pk):
    notification = db.notifications.find_one({'id': pk})
    if not notification:
      return Response(
          {'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND
      )

    update_fields = {}
    if 'title' in request.data:
      update_fields['title'] = request.data['title']
    if 'message' in request.data:
      update_fields['message'] = request.data['message']
    if 'priority' in request.data:
      update_fields['priority'] = request.data['priority']
    update_fields['updated_at'] = datetime.utcnow().isoformat()

    db.notifications.update_one({'id': pk}, {'$set': update_fields})
    updated_doc = db.notifications.find_one({'id': pk}, {'_id': 0})
    return Response(updated_doc, status=status.HTTP_200_OK)

  def delete(self, request, pk):
    result = db.notifications.update_one(
        {'id': pk},
        {'$set': {'is_deleted': True, 'updated_at': datetime.utcnow().isoformat()}},
    )
    if result.matched_count == 0:
      return Response(
          {'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND
      )
    return Response(
        {'message': 'Notification deleted successfully'},
        status=status.HTTP_200_OK,
    )


class MarkNotificationReadView(APIView):
  """PUT /api/notifications/<id>/read/ - Mark Notification as Read."""

  def put(self, request, pk):
    result = db.notifications.update_one(
        {'id': pk},
        {
            '$set': {
                'read_status': True,
                'updated_at': datetime.utcnow().isoformat(),
            }
        },
    )
    if result.matched_count == 0:
      return Response(
          {'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND
      )
    return Response(
        {'message': 'Notification marked as read'}, status=status.HTTP_200_OK
    )