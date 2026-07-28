import json
import asyncio
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings

# Read configurable timeout (defaults to 120s / 2 minutes)
RECONNECT_TIMEOUT_SECONDS = getattr(settings, 'RECONNECT_TIMEOUT_SECONDS', 120)


class ClassroomConsumer(AsyncWebsocketConsumer):
    # Active timer tasks mapped by classroom_id: { 'session_101': Task }
    disconnect_timers = {}

    async def connect(self):
        self.classroom_id = self.scope['url_route']['kwargs']['classroom_id']
        self.room_group_name = f'classroom_{self.classroom_id}'

        # Extract role & email parameters from query string safely
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)

        self.user_role = params.get('role', ['Student'])[0].strip().capitalize()
        self.user_email = params.get('email', [''])[0].strip().lower()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # 🌟 TRAINER RECONNECT HANDSHAKE: Cancel timer if trainer returns within timeout
        if self.user_role.lower() == 'trainer':
            if self.classroom_id in ClassroomConsumer.disconnect_timers:
                timer_task = ClassroomConsumer.disconnect_timers.pop(self.classroom_id, None)
                if timer_task:
                    timer_task.cancel()

                await self.mark_reconnect_restored(self.classroom_id, self.user_email)

                # Broadcast reconnection notice to students in the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_event',
                        'event_type': 'TRAINER_RECONNECTED',
                        'payload': {
                            'message': 'Trainer has reconnected! Resuming session state...',
                            'trainerEmail': self.user_email
                        }
                    }
                )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # 🌟 ONLY start 2-min timeout if TRAINER drops UNEXPECTEDLY (close_code != 1000)
        # 1000 = Normal explicit disconnect (e.g. Trainer clicked "End Meeting")
        if getattr(self, 'user_role', '').lower() == 'trainer' and close_code != 1000:
            # Log disconnect entry in database
            await self.log_reconnect_start(self.classroom_id, getattr(self, 'user_email', 'trainer1@gmail.com'))

            # Broadcast disconnect alert to waiting students
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_event',
                    'event_type': 'TRAINER_DISCONNECTED',
                    'payload': {
                        'message': 'Trainer lost connection. Attempting auto-reconnection...',
                        'timeoutSeconds': RECONNECT_TIMEOUT_SECONDS
                    }
                }
            )

            # Start background countdown timer task
            timer_task = asyncio.create_task(self.start_recovery_timer(self.classroom_id))
            ClassroomConsumer.disconnect_timers[self.classroom_id] = timer_task

    async def start_recovery_timer(self, session_id):
        try:
            await asyncio.sleep(RECONNECT_TIMEOUT_SECONDS)
            # Timer expired: Auto-end the live session
            await self.auto_end_session(session_id)

            await self.channel_layer.group_send(
                f'classroom_{session_id}',
                {
                    'type': 'broadcast_event',
                    'event_type': 'SESSION_TIMEOUT_ENDED',
                    'payload': {
                        'message': 'Trainer failed to reconnect within timeout. Session ended.'
                    }
                }
            )
        except asyncio.CancelledError:
            # Trainer returned before timer expired!
            pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action_type = data.get('type')
            payload = data.get('payload', data)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_event',
                    'event_type': action_type,
                    'payload': payload
                }
            )
        except Exception as e:
            print(f"Error receiving WS message: {e}")

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'payload': event['payload']
        }))

    @database_sync_to_async
    def log_reconnect_start(self, session_id, email):
        from .models import SessionReconnectLog, ClassroomSession, ActivityLog
        session = ClassroomSession.objects.filter(id=session_id).first()
        if session:
            SessionReconnectLog.objects.create(
                session=session,
                user_email=email,
                user_role='Trainer',
                status='Reconnecting'
            )
            ActivityLog.objects.create(session=session, action="Trainer connection dropped (Reconnecting...)")

    @database_sync_to_async
    def mark_reconnect_restored(self, session_id, email):
        from .models import SessionReconnectLog, ClassroomSession, ActivityLog
        session = ClassroomSession.objects.filter(id=session_id).first()
        log = SessionReconnectLog.objects.filter(
            session_id=session_id,
            status='Reconnecting'
        ).first()

        now_local = timezone.localtime(timezone.now())
        if log:
            log.status = 'Restored'
            log.reconnected_at = now_local
            log.save()

        if session:
            ActivityLog.objects.create(session=session, action="Trainer reconnected successfully")

    @database_sync_to_async
    def auto_end_session(self, session_id):
        from .models import ClassroomSession, SessionReconnectLog, ActivityLog
        session = ClassroomSession.objects.filter(id=session_id).first()
        if session:
            session.is_live = False
            session.save()
            ActivityLog.objects.create(session=session, action="Session ended automatically due to disconnect timeout")

        log = SessionReconnectLog.objects.filter(
            session_id=session_id,
            status='Reconnecting'
        ).first()
        if log:
            log.status = 'TimedOut'
            log.save()