# whiteboard/urls.py
from django.urls import path
from .views import WhiteboardSaveView, WhiteboardDetailView

urlpatterns = [
    path('save/', WhiteboardSaveView.as_view(), name='whiteboard-save'),
    path('<str:session_id>/', WhiteboardDetailView.as_view(), name='whiteboard-detail'),
]