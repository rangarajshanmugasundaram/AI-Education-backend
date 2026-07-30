import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


def format_seconds_to_time(seconds: int) -> str:
    """Formats raw seconds into standard HH:MM:SS or MM:SS strings."""
    if not seconds:
        return "00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """Converts raw bytes into human-readable size labels (MB, GB)."""
    if not bytes_size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_size) < 1024.0:
            return f"{bytes_size:3.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def decode_and_validate_playback_token(token: str) -> dict:
    """
    Decodes and validates JWT streaming playback token.
    Raises standard DRF exceptions on expiration or tampering.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise PermissionDenied("Playback access token has expired. Please request a new token.")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid playback access token.")