import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ClassroomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.classroom_id = self.scope['url_route']['kwargs']['classroom_id']
        self.room_group_name = f'classroom_{self.classroom_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action_type = data.get('type')
            payload = data.get('payload', data)

            # Broadcast custom event to room group
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
        # Send direct normalized payload structure to client
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'payload': event['payload']
        }))