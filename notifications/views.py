import uuid
from datetime import datetime, timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from db_connection import db  # PyMongo collection reference
from .serializers import NotificationSerializer


class NotificationListCreateView(APIView):
    """
    POST /api/notifications/ - Create Notification & Broadcast Event
    GET  /api/notifications/ - Get All Notifications (Filtered)
    """

    def get(self, request):
        try:
            priority = request.query_params.get('priority')
            recipient_type = request.query_params.get('recipient_type')
            read_status = request.query_params.get('read_status')
            search = request.query_params.get('search')

            query = {'is_deleted': {'$ne': True}}

            if priority:
                query['priority'] = priority
            if recipient_type:
                query['recipient_type'] = recipient_type
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
            now_iso = datetime.now(timezone.utc).isoformat()

            # Dynamically resolve sender details
            sender_id = getattr(request.user, 'email', request.data.get('sender_id', 'admin@aieducation.com'))
            sender_role = getattr(request.user, 'role', request.data.get('sender_role', 'Trainer'))

            notification_doc = {
                'id': str(uuid.uuid4()),
                'title': data['title'],
                'message': data['message'],
                'sender_id': sender_id,
                'sender_role': sender_role,
                'recipient_type': data.get('recipient_type', 'All'),
                'recipient_id': data.get('recipient_id'),
                'batch_id': data.get('batch_id'),
                'priority': data.get('priority', 'Medium'),
                'read_status': False,
                'is_deleted': False,
                'created_at': now_iso,
                'updated_at': now_iso,
            }

            # 1. Save to MongoDB
            db.notifications.insert_one(notification_doc)
            notification_doc.pop('_id', None)

            # 2. 🌟 REAL-TIME WEBSOCKET BROADCAST
            try:
                channel_layer = get_channel_layer()
                target_group = "notifications_global"

                # Route to specific target group if specified
                recipient_type = notification_doc.get('recipient_type')
                if recipient_type == 'Batch' and notification_doc.get('batch_id'):
                    target_group = f"batch_{notification_doc['batch_id']}"
                elif recipient_type == 'User' and notification_doc.get('recipient_id'):
                    clean_email = notification_doc['recipient_id'].replace('@', '_at_').replace('.', '_')
                    target_group = f"user_{clean_email}"

                async_to_sync(channel_layer.group_send)(
                    target_group,
                    {
                        'type': 'broadcast_event',
                        'event_type': 'NEW_NOTIFICATION',
                        'payload': notification_doc
                    }
                )
            except Exception as ws_err:
                print(f"[WebSocket Broadcast Error]: {ws_err}")

            return Response(notification_doc, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyNotificationsView(APIView):
    """GET /api/notifications/my/ - Get Logged-in User Notifications."""

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
    """
    GET /api/notifications/<id>/ - Get Details
    PUT /api/notifications/<id>/ - Update
    DELETE /api/notifications/<id>/ - Soft Delete
    """

    def get(self, request, pk):
        notification = db.notifications.find_one({'id': pk, 'is_deleted': {'$ne': True}}, {'_id': 0})
        if not notification:
            return Response(
                {'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(notification, status=status.HTTP_200_OK)

    def put(self, request, pk):
        notification = db.notifications.find_one({'id': pk, 'is_deleted': {'$ne': True}})
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

        update_fields['updated_at'] = datetime.now(timezone.utc).isoformat()

        db.notifications.update_one({'id': pk}, {'$set': update_fields})
        updated_doc = db.notifications.find_one({'id': pk}, {'_id': 0})
        return Response(updated_doc, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        now_iso = datetime.now(timezone.utc).isoformat()
        result = db.notifications.update_one(
            {'id': pk},
            {'$set': {'is_deleted': True, 'updated_at': now_iso}},
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
        now_iso = datetime.now(timezone.utc).isoformat()
        result = db.notifications.update_one(
            {'id': pk},
            {
                '$set': {
                    'read_status': True,
                    'updated_at': now_iso,
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