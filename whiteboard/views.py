import uuid
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from db_connection import db

collection = db['whiteboard']


class WhiteboardSaveView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if not data.get('session_id') or not data.get('drawing_data'):
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        doc = {
            "whiteboard_id": str(uuid.uuid4()),
            "session_id": data['session_id'],
            "user_email": request.headers.get('X-User-Email', 'unknown'),
            "drawing_data": data['drawing_data'],  # Now expects { path: [...] }
            "tool_type": data.get('tool_type', 'pen'),
            "color": data.get('color', '#000000'),
            "stroke_width": int(data.get('stroke_width', 2)),
            "timestamp": datetime.datetime.utcnow()
        }
        collection.insert_one(doc)
        return Response({"success": True}, status=status.HTTP_201_CREATED)


class WhiteboardDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        drawings = list(collection.find({"session_id": session_id}))
        for d in drawings: d['_id'] = str(d['_id'])
        return Response(drawings, status=status.HTTP_200_OK)

    def delete(self, request, session_id):
        user_email = request.headers.get('X-User-Email', '').lower()
        if 'trainer' not in user_email:
            return Response({"error": "Only Trainers can clear the board"}, status=status.HTTP_403_FORBIDDEN)

        collection.delete_many({"session_id": session_id})
        return Response({"message": "Cleared successfully"}, status=status.HTTP_200_OK)