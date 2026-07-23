import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_education.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

import classroom.routing
from classroom.middleware import WebSocketJWTAuthMiddleware

application = ProtocolTypeRouter({
    # Standard HTTP requests
    "http": django_asgi_app,

    # WebSocket requests (`ws://` and `wss://`)
    "websocket": WebSocketJWTAuthMiddleware(
        URLRouter(
            classroom.routing.websocket_urlpatterns
        )
    ),
})