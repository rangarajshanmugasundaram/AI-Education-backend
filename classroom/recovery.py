import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ClassroomSession, Participant, WaitingRoomUser, ActivityLog, SessionReconnectLog
from .serializers import ClassroomSessionSerializer, ParticipantSerializer, WaitingRoomUserSerializer, \
    ActivityLogSerializer
from db_connection import db

logger = logging.getLogger(__name__)


def log_reconnect_event(session_id, user_email, user_role='Trainer'):
    """
    Creates a new disconnect/reconnect tracking entry in SQLite/Database.
    """
    try:
        session, _ = ClassroomSession.objects.get_or_create(id=session_id)
        log = SessionReconnectLog.objects.create(
            session=session,
            user_email=user_email,
            user_role=user_role,
            status='Reconnecting'
        )
        return log
    except Exception as e:
        logger.error(f"Error logging reconnect event for {session_id}: {e}")
        return None


def mark_reconnect_success(session_id, user_email):
    """
    Marks the active reconnect record as Restored when trainer returns within timeout.
    """
    try:
        log = SessionReconnectLog.objects.filter(
            session_id=session_id,
            user_email=user_email,
            status='Reconnecting'
        ).first()

        if log:
            log.status = 'Restored'
            log.reconnected_at = timezone.now()
            log.save()
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating reconnect log for {session_id}: {e}")
        return False


def handle_session_timeout(session_id):
    """
    Executes auto-end logic if the trainer fails to reconnect before the timeout window expires.
    """
    try:
        session = ClassroomSession.objects.filter(id=session_id).first()
        if session:
            session.is_live = False
            session.save()

            # Record log entry
            log = SessionReconnectLog.objects.filter(session=session, status='Reconnecting').first()
            if log:
                log.status = 'TimedOut'
                log.save()

            # Broadcast session termination to room group
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'classroom_{session_id}',
                {
                    'type': 'broadcast_event',
                    'event_type': 'SESSION_TIMEOUT_ENDED',
                    'payload': {
                        'message': 'Trainer failed to reconnect within timeout. Session ended automatically.'
                    }
                }
            )
            return True
        return False
    except Exception as e:
        logger.error(f"Error handling timeout for {session_id}: {e}")
        return False


def get_full_session_recovery_payload(session_id):
    """
    Compiles full snapshot of classroom state (Participants, Raised Hands, Waiting Room, Activity Logs, Chat)
    to restore frontend UI components seamlessly on trainer reconnect.
    """
    try:
        session, _ = ClassroomSession.objects.get_or_create(id=session_id)

        participants = Participant.objects.filter(session=session)
        raised_hands = participants.filter(has_raised_hand=True)
        waiting_users = WaitingRoomUser.objects.filter(session=session)
        logs = ActivityLog.objects.filter(session=session)

        # Retrieve chat history from MongoDB 'chat' collection
        chat_cursor = db.chat.find({'session_id': session_id}).sort('timestamp', 1)
        chat_logs = []
        for doc in chat_cursor:
            doc.pop('_id', None)
            chat_logs.append(doc)

        return {
            'session': ClassroomSessionSerializer(session).data,
            'participants': ParticipantSerializer(participants, many=True).data,
            'raised_hands': ParticipantSerializer(raised_hands, many=True).data,
            'waiting_room': WaitingRoomUserSerializer(waiting_users, many=True).data,
            'activity_logs': ActivityLogSerializer(logs, many=True).data,
            'chat_logs': chat_logs
        }
    except Exception as e:
        logger.error(f"Error assembling recovery payload for {session_id}: {e}")
        return {}