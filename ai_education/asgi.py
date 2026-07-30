import os
from django.core.asgi import get_asgi_application

# 1. Set environment settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_education.settings')

# 2. MUST initialize Django ASGI application FIRST before importing routing/models
django_asgi_app = get_asgi_application()

# 3. Import app routers & middleware ONLY AFTER get_asgi_application()
import classroom.routing
import notifications.routing
from classroom.middleware import WebSocketJWTAuthMiddleware

# 4. Combine websocket patterns safely
combined_websocket_patterns = (
    classroom.routing.websocket_urlpatterns +
    notifications.routing.websocket_urlpatterns
)

from channels.routing import ProtocolTypeRouter, URLRouter

# 5. Define root application protocol router
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WebSocketJWTAuthMiddleware(
        URLRouter(
            combined_websocket_patterns
        )
    ),
})