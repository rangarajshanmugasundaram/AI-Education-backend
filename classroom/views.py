from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ClassroomSession, Participant, WaitingRoomUser, ActivityLog
from .serializers import (
    ClassroomSessionSerializer, ParticipantSerializer,
    WaitingRoomUserSerializer, ActivityLogSerializer
)


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
def get_session_details(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)

    user_email = request.headers.get('X-User-Email', '').strip().lower()

    if user_email:
        name_part = user_email.split('@')[0].capitalize()
        # Explicit role check (e.g., student/trainer via email or explicit headers)
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


@api_view(['POST'])
def start_session(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_live = True
    session.save()
    log_action(session, "Trainer started live session")
    broadcast_ws(id, 'SESSION_CONTROL', {'isLive': True, 'action': 'started'})
    return Response({'status': 'Session Started'})


@api_view(['POST'])
def end_session(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_live = False
    session.save()
    log_action(session, "Trainer ended live session")
    broadcast_ws(id, 'SESSION_CONTROL', {'isLive': False, 'action': 'ended'})
    return Response({'status': 'Session Ended'})


@api_view(['POST'])
def toggle_session_lock(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)
    session.is_locked = not session.is_locked
    session.save()
    log_action(session, f"Trainer {'locked' if session.is_locked else 'unlocked'} session")
    broadcast_ws(id, 'SESSION_CONTROL', {'isLocked': session.is_locked, 'action': 'lock_toggled'})
    return Response({'isLocked': session.is_locked})


# --- Raise Hand Management ---

@api_view(['POST'])
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
def get_participants(request, id):
    participants = Participant.objects.filter(session_id=id)
    return Response(ParticipantSerializer(participants, many=True).data)


@api_view(['DELETE'])
def remove_participant(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=participantId)
    participant.status = 'Removed'
    participant.save()

    log_action(session, f"Trainer removed {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Participant removed'})


@api_view(['POST'])
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
def toggle_self_mute(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, email=email)
    participant.is_muted = not participant.is_muted
    participant.save()

    broadcast_participant_list(session)
    return Response({'isMuted': participant.is_muted})


@api_view(['POST'])
def toggle_self_camera(request, id):
    email = request.data.get('email')
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, email=email)
    participant.is_camera_on = not participant.is_camera_on
    participant.save()

    broadcast_participant_list(session)
    return Response({'isCameraOn': participant.is_camera_on})


@api_view(['POST'])
def mute_participant(request, id, participantId):
    session = ClassroomSession.objects.get(id=id)
    participant = Participant.objects.get(session=session, id=participantId)
    participant.is_muted = True
    participant.save()

    log_action(session, f"Trainer muted {participant.name}")
    broadcast_participant_list(session)
    return Response({'status': 'Muted participant'})


# ✅ MUTE ALL STUDENTS & BROADCAST IMMEDIATELY
@api_view(['POST'])
def mute_all_participants(request, id):
    session, _ = ClassroomSession.objects.get_or_create(id=id)

    # 1. Update database records for all students in session
    Participant.objects.filter(session=session, role='Student').update(is_muted=True)

    # 2. Log activity
    log_action(session, "Trainer muted all students")

    # 3. Broadcast updated participant list across WebSockets
    broadcast_participant_list(session)

    return Response({'status': 'Muted all participants'}, status=status.HTTP_200_OK)


# --- Permissions & Waiting Room ---

@api_view(['PUT'])
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
def get_waiting_room(request, id):
    waiting_users = WaitingRoomUser.objects.filter(session_id=id)
    return Response(WaitingRoomUserSerializer(waiting_users, many=True).data)


@api_view(['POST'])
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

    # Update Waiting Room across WebSockets
    waiting_list = WaitingRoomUser.objects.filter(session=session)
    broadcast_ws(id, 'WAITING_ROOM_UPDATE', {
        'waitingList': WaitingRoomUserSerializer(waiting_list, many=True).data
    })
    return Response({'status': 'User approved'})


@api_view(['POST'])
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
def get_activity_logs(request, id):
    logs = ActivityLog.objects.filter(session_id=id)
    return Response(ActivityLogSerializer(logs, many=True).data)