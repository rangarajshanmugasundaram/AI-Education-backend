import uuid
from datetime import datetime, timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView  # 🌟 REQUIRED IMPORT FOR APIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ClassroomSession, Participant, WaitingRoomUser, ActivityLog, SessionReconnectLog
from .serializers import (
    ClassroomSessionSerializer, ParticipantSerializer,
    WaitingRoomUserSerializer, ActivityLogSerializer
)

# MongoDB Connection instance
from db_connection import db


def broadcast_ws(session_id, event_type, payload):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'classroom_{session_id}',
        {
            'type': 'broadcast_event',
            'event_type': event_type,
            'payload': payload
        }
    )


def broadcast_global_notification(notification_doc):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications_global",
            {
                'type': 'broadcast_event',
                'event_type': 'NEW_NOTIFICATION',
                'payload': notification_doc
            }
        )
    except Exception as err:
        print(f"[Global Notification Broadcast Error]: {err}")


def log_action(session, action_text):
    log = ActivityLog.objects.create(session=session, action=action_text)
    return ActivityLogSerializer(log).data


def broadcast_participant_list(session):
    all_participants = Participant.objects.filter(session=session)
    participants_data = ParticipantSerializer(all_participants, many=True).data
    broadcast_ws(session.id, 'PARTICIPANTS_UPDATE', {
        'participants': participants_data
    })


# --- Session Details & Auto Join ---

@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_details(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)

    user_email = request.headers.get('X-User-Email', '').strip().lower()

    if user_email:
        name_part = user_email.split('@')[0].capitalize()
        user_role = 'Trainer' if 'trainer' in user_email else 'Student'

        participant, created = Participant.objects.get_or_create(
            session=session,
            email=user_email,
            defaults={
                'name': name_part,
                'role': user_role,
                'status': 'Active',
                'is_muted': True,
                'is_camera_on': False,
            }
        )
        if created:
            log_action(session, f"{participant.name} ({participant.role}) joined")
            broadcast_participant_list(session)

    serializer = ClassroomSessionSerializer(session)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recovery_state(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)

    participants = Participant.objects.filter(session=session)
    raised_hands = participants.filter(has_raised_hand=True)
    waiting_users = WaitingRoomUser.objects.filter(session=session)
    logs = ActivityLog.objects.filter(session=session)

    chat_cursor = db.chat.find({'session_id': id}).sort('timestamp', 1)
    chat_logs = []
    for doc in chat_cursor:
        doc.pop('_id', None)
        chat_logs.append(doc)

    return Response({
        'session': ClassroomSessionSerializer(session).data,
        'participants': ParticipantSerializer(participants, many=True).data,
        'raised_hands': ParticipantSerializer(raised_hands, many=True).data,
        'waiting_room': WaitingRoomUserSerializer(waiting_users, many=True).data,
        'activity_logs': ActivityLogSerializer(logs, many=True).data,
        'chat_logs': chat_logs
    }, status=status.HTTP_200_OK)


# --- Session Control Views ---

@api_view(['POST'])
@permission_classes([AllowAny])
def start_session(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_live = True
    session.save()
    log_action(session, "Trainer started live session")

    broadcast_ws(id, 'SESSION_CONTROL', {'isLive': True, 'action': 'started'})

    now_iso = datetime.now(timezone.utc).isoformat()
    notification_doc = {
        'id': str(uuid.uuid4()),
        'title': f'🔴 Live Session Started ({id})',
        'message': f'Trainer has initiated the live classroom ({id}). Click to join now!',
        'sender_id': 'trainer@aieducation.com',
        'sender_role': 'Trainer',
        'recipient_type': 'All',
        'batch_id': str(id),
        'priority': 'Emergency',
        'read_status': False,
        'is_deleted': False,
        'created_at': now_iso,
        'updated_at': now_iso,
    }

    try:
        db.notifications.insert_one(notification_doc)
        notification_doc.pop('_id', None)
        broadcast_global_notification(notification_doc)
    except Exception as err:
        print(f"[Database/Notification Error]: {err}")

    return Response({'status': 'Session Started', 'notification': notification_doc}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def end_session(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_live = False
    session.save()
    log_action(session, "Trainer ended live session")

    broadcast_ws(id, 'SESSION_CONTROL', {'isLive': False, 'action': 'ended'})

    now_iso = datetime.now(timezone.utc).isoformat()
    notification_doc = {
        'id': str(uuid.uuid4()),
        'title': f'⏹️ Live Session Ended ({id})',
        'message': f'The live classroom session ({id}) has been closed by the trainer.',
        'sender_id': 'trainer@aieducation.com',
        'sender_role': 'Trainer',
        'recipient_type': 'All',
        'batch_id': str(id),
        'priority': 'Low',
        'read_status': False,
        'is_deleted': False,
        'created_at': now_iso,
        'updated_at': now_iso,
    }

    try:
        db.notifications.insert_one(notification_doc)
        notification_doc.pop('_id', None)
        broadcast_global_notification(notification_doc)
    except Exception as err:
        print(f"[Database/Notification Error]: {err}")

    return Response({'status': 'Session Ended'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_session_lock(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_locked = not session.is_locked
    session.save()
    log_action(session, f"Trainer {'locked' if session.is_locked else 'unlocked'} session")
    broadcast_ws(id, 'SESSION_CONTROL', {'isLocked': session.is_locked, 'action': 'lock_toggled'})
    return Response({'isLocked': session.is_locked})


# --- Raise Hand Management ---

@api_view(['POST'])
@permission_classes([AllowAny])
def raise_hand(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant, _ = Participant.objects.get_or_create(session=session, email=email)
    participant.has_raised_hand = not participant.has_raised_hand
    participant.save()

    action = "raised hand" if participant.has_raised_hand else "lowered hand"
    log_action(session, f"{participant.name} {action}")

    broadcast_participant_list(session)
    broadcast_ws(id, 'RAISE_HAND', {'student': ParticipantSerializer(participant).data})
    return Response({'status': f'Hand {action}'})


@api_view(['POST'])
@permission_classes([AllowAny])
def lower_hand(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, email=email)
    participant.has_raised_hand = False
    participant.save()

    log_action(session, f"{participant.name} lowered hand")
    broadcast_participant_list(session)
    return Response({'status': 'Hand lowered'})


@api_view(['POST'])
@permission_classes([AllowAny])
def dismiss_hand_request(request, id, studentId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=studentId)
    participant.has_raised_hand = False
    participant.save()

    log_action(session, f"Trainer dismissed hand request for {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Hand dismissed'})


# --- Participant Roster & Actions ---

@api_view(['GET'])
@permission_classes([AllowAny])
def get_participants(request, id):
    participants = Participant.objects.filter(session_id=id)
    return Response(ParticipantSerializer(participants, many=True).data)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_participant(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=participantId)
    participant.status = 'Removed'
    participant.save()

    log_action(session, f"Trainer removed {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Participant removed'})


@api_view(['POST'])
@permission_classes([AllowAny])
def allow_rejoin(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=participantId)
    participant.status = 'Active'
    participant.save()

    log_action(session, f"Trainer permitted {participant.name} to rejoin")
    broadcast_participant_list(session)
    return Response({'status': 'Allowed rejoin'})


# --- Media Controls ---

@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_self_mute(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, email=email)
    participant.is_muted = not participant.is_muted
    participant.save()

    broadcast_participant_list(session)
    return Response({'isMuted': participant.is_muted})


@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_self_camera(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, email=email)
    participant.is_camera_on = not participant.is_camera_on
    participant.save()

    broadcast_participant_list(session)
    return Response({'isCameraOn': participant.is_camera_on})


@api_view(['POST'])
@permission_classes([AllowAny])
def mute_participant(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=participantId)
    participant.is_muted = True
    participant.save()

    log_action(session, f"Trainer muted {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Muted participant'})


@api_view(['POST'])
@permission_classes([AllowAny])
def mute_all_participants(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    Participant.objects.filter(session=session, role='Student').update(is_muted=True)
    log_action(session, "Trainer muted all students")
    broadcast_participant_list(session)
    return Response({'status': 'Muted all participants'}, status=status.HTTP_200_OK)


# --- Permissions & Waiting Room ---

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_participant_permissions(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    perms = request.data.get('permissions', {})
    participant = Participant.objects.get(session=session, id=participantId)
    participant.can_speak = perms.get('canSpeak', participant.can_speak)
    participant.can_chat = perms.get('canChat', participant.can_chat)
    participant.can_screen_share = perms.get('canScreenShare', participant.can_screen_share)
    participant.save()

    log_action(session, f"Updated permissions for {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Permissions updated'})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_waiting_room(request, id):
    waiting_users = WaitingRoomUser.objects.filter(session_id=id)
    return Response(WaitingRoomUserSerializer(waiting_users, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def approve_join_request(request, id, userId):
    waiting_user = WaitingRoomUser.objects.get(id=userId)
    session = ClassroomSession.objects.get(id=id)

    Participant.objects.create(
        session=session,
        name=waiting_user.name,
        email=waiting_user.email,
        role='Student',
        status='Active'
    )
    waiting_user.delete()
    log_action(session, f"Approved {waiting_user.name} to join classroom")

    broadcast_participant_list(session)

    waiting_list = WaitingRoomUser.objects.filter(session=session)
    broadcast_ws(id, 'WAITING_ROOM_UPDATE', {
        'waitingList': WaitingRoomUserSerializer(waiting_list, many=True).data
    })
    return Response({'status': 'User approved'})


@api_view(['POST'])
@permission_classes([AllowAny])
def reject_join_request(request, id, userId):
    waiting_user = WaitingRoomUser.objects.get(id=userId)
    session = waiting_user.session
    waiting_user.delete()

    waiting_list = WaitingRoomUser.objects.filter(session=session)
    broadcast_ws(id, 'WAITING_ROOM_UPDATE', {
        'waitingList': WaitingRoomUserSerializer(waiting_list, many=True).data
    })
    return Response({'status': 'User rejected'})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_activity_logs(request, id):
    logs = ActivityLog.objects.filter(session_id=id)
    return Response(ActivityLogSerializer(logs, many=True).data)


# 🌟 CLASS-BASED VIEW FOR POSTMAN INGESTION
class ClassroomSessionListCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            sessions_col = db['sessions']

            now_iso = datetime.now(timezone.utc).isoformat()
            session_id = str(uuid.uuid4())

            new_session = {
                "_id": session_id,
                "title": data.get("title", "Classroom Session"),
                "sessionName": data.get("sessionName", data.get("title", "Classroom Session")),
                "trainerName": data.get("trainerName", "Assigned Trainer"),
                "trainer_email": data.get("trainer_email", ""),
                "status": data.get("status", "completed"),
                "scheduled_at": data.get("scheduled_at", now_iso),
                "updatedAt": now_iso,
                "created_at": datetime.now(timezone.utc)
            }

            sessions_col.insert_one(new_session)

            return Response({
                "success": True,
                "message": "Session created successfully in MongoDB",
                "_id": session_id,
                "session": {
                    "title": new_session["title"],
                    "sessionName": new_session["sessionName"],
                    "trainerName": new_session["trainerName"],
                    "trainer_email": new_session["trainer_email"],
                    "status": new_session["status"],
                    "scheduled_at": new_session["scheduled_at"],
                    "updatedAt": new_session["updatedAt"]
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            sessions_col = db['sessions']
            cursor = sessions_col.find(
                {},
                {'_id': 1, 'title': 1, 'sessionName': 1, 'trainerName': 1, 'trainer_email': 1, 'status': 1,
                 'scheduled_at': 1, 'updatedAt': 1, 'created_at': 1}
            ).sort('_id', -1)

            sessions = []
            for s in cursor:
                sessions.append({
                    "_id": str(s.get('_id')),
                    "title": s.get("title", ""),
                    "sessionName": s.get("sessionName", s.get("title", "")),
                    "trainerName": s.get("trainerName", ""),
                    "trainer_email": s.get("trainer_email", ""),
                    "status": s.get("status", "completed"),
                    "scheduled_at": s.get("scheduled_at", ""),
                    "updatedAt": s.get("updatedAt") or s.get("created_at") or datetime.now(timezone.utc).isoformat()
                })

            return Response(sessions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)