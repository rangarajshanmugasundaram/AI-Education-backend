from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('session/<str:session_id>/', views.get_session_feedback, name='get_session_feedback'),
    path('trainer/<str:trainer_id>/', views.get_trainer_feedback, name='get_trainer_feedback'),
]