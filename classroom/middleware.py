from urllib.parse import parse_qs
from django.conf import settings
import jwt

JWT_SECRET = getattr(
    settings, 'SECRET_KEY', 'your-fallback-secret-key-change-in-production'
)
JWT_ALGORITHM = 'HS256'


class WebSocketJWTAuthMiddleware:
  """Custom WebSocket middleware to extract and verify real JWT token and email from connection scope query strings."""

  def __init__(self, inner):
    self.inner = inner

  async def __call__(self, scope, receive, send):
    query_string = scope.get('query_string', b'').decode('utf-8')
    query_params = parse_qs(query_string)

    token = query_params.get('token', [None])[0]
    email = query_params.get('email', [None])[0]

    verified_email = email
    verified_role = None

    if token:
      try:
        # Verify and decode real JWT token in WebSocket handshake
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        verified_email = decoded.get('email', email)
        verified_role = decoded.get('role', None)
      except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Fall back to None on unverified token
        verified_email = None
        verified_role = None

    # Attach verified parameters directly to connection scope
    scope['user_token'] = token
    scope['user_email'] = verified_email
    scope['user_role'] = verified_role

    return await self.inner(scope, receive, send)