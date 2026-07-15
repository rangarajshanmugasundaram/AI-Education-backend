import datetime
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# Direct link to your active MongoDB client configuration
from db_connection import db


def validate_mock_auth(request):
    """
    Validates the mock token and extracts user metadata from the custom frontend headers.
    Returns (user_context, None) if successful, or (None, error_response) if unauthorized.
    """
    auth_header = request.headers.get('Authorization', '')
    email = request.headers.get('X-User-Email', '').strip().lower()

    # 1. Enforce mock token validation rule
    if not auth_header.startswith('Bearer mock-jwt-token-from-backend-xyz123'):
        return None, Response(
            {"detail": "Unauthorized access: Invalid or missing token verification."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not email:
        return None, Response(
            {"detail": "Authentication context missing: X-User-Email header required."},
            status=status.HTTP_403_FORBIDDEN
        )

    username = email.split('@')[0]
    user_context = {
        "email": email,
        "username": username,
        "sender_name": username.capitalize()
    }
    return user_context, None


class SendMessageView(APIView):
    """
    POST /api/chat/send
    Saves the incoming message document directly into your MongoDB chat collection.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user, error_response = validate_mock_auth(request)
        if error_response:
            return error_response

        session_id = request.data.get('session_id', '').strip()
        message = request.data.get('message', '').strip()
        message_type = request.data.get('message_type', 'Text')

        # Business Rule Validations
        if not session_id:
            return Response({"session_id": "Session ID cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({"message": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if len(message) > 1000:
            return Response({"message": "Message size cannot exceed 1000 characters."}, status=status.HTTP_400_BAD_REQUEST)

        # Build clean NoSQL document matching target payload requirements
        chat_document = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "sender_name": user["sender_name"],
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "date_created": datetime.date.today().isoformat()
        }

        # Write record straight into MongoDB (Creates 'chat' collection if missing)
        db.chat.insert_one(chat_document)

        # Strip standard BSON unique object reference pointer to avoid JSON generation errors
        chat_document.pop('_id', None)
        return Response(chat_document, status=status.HTTP_201_CREATED)


class SessionMessagesView(APIView):
    """
    GET /api/chat/session/<str:session_id>
    Fetches room logs out of MongoDB sorted in clean chronological order.
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        user, error_response = validate_mock_auth(request)
        if error_response:
            return error_response

        # Find matching documents in your collection and sort ascending (1) by time
        cursor = db.chat.find({"session_id": session_id}).sort("timestamp", 1)

        messages = []
        for doc in cursor:
            doc.pop('_id', None)
            messages.append(doc)

        return Response(messages, status=status.HTTP_200_OK)


class DeleteMessageView(APIView):
    """
    DELETE /api/chat/<str:message_id>
    Removes target chat record from MongoDB collection.
    """
    permission_classes = [AllowAny]

    def delete(self, request, message_id):
        user, error_response = validate_mock_auth(request)
        if error_response:
            return error_response

        # Role restriction checking targeting your custom frontend authentication
        if 'trainer' not in user["email"]:
            return Response(
                {"error": "Forbidden: Only Trainers or Staff accounts possess message deletion access privileges."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Wipe matching message document directly out of MongoDB
        result = db.chat.delete_one({"message_id": str(message_id)})

        if result.deleted_count > 0:
            return Response({"detail": "Message successfully removed from MongoDB records."}, status=status.HTTP_200_OK)

        return Response({"error": "Message structural resource not found."}, status=status.HTTP_404_NOT_FOUND)