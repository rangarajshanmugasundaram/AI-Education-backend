from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class WebSocketJWTAuthMiddleware:
    """
    Custom WebSocket middleware to extract token and email from connection scope query strings.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)

        token = query_params.get('token', [None])[0]
        email = query_params.get('email', [None])[0]

        # In testing/development, attach parameters to connection scope
        scope['user_token'] = token
        scope['user_email'] = email

        return await self.inner(scope, receive, send)