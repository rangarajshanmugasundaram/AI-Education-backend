from django.urls import path
from .views import SendMessageView, SessionMessagesView, DeleteMessageView

urlpatterns = [
    path('send', SendMessageView.as_view(), name='chat-send'),
    path('session/<str:session_id>', SessionMessagesView.as_view(), name='session-messages'),
    path('<str:message_id>', DeleteMessageView.as_view(), name='delete-message'),
]