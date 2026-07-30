import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.groups_joined = []

        # Always join global notifications channel
        await self.channel_layer.group_add('notifications_global', self.channel_name)
        self.groups_joined.append('notifications_global')

        # Extract user email / batch info from query params or headers if available
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)

        user_email = params.get('email')
        batch_id = params.get('batch_id')

        if user_email:
            # Clean email for valid channel group name
            clean_email = user_email.replace('@', '_at_').replace('.', '_')
            user_group = f"user_{clean_email}"
            await self.channel_layer.group_add(user_group, self.channel_name)
            self.groups_joined.append(user_group)

        if batch_id:
            batch_group = f"batch_{batch_id}"
            await self.channel_layer.group_add(batch_group, self.channel_name)
            self.groups_joined.append(batch_group)

        await self.accept()

    async def disconnect(self, close_code):
        for group in getattr(self, 'groups_joined', []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data):
        # Client ping handler to keep connection alive
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    # Real-Time Broadcast Event Handler
    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps({
            'type': event.get('event_type', 'NEW_NOTIFICATION'),
            'payload': event.get('payload', {})
        }))