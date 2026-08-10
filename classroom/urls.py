from django.urls import path
from . import views

urlpatterns = [
    # 🌟 MUST BE TOP-MOST: Collection routes for Postman POST creation & GET listing
    path('sessions/', views.ClassroomSessionListCreateView.as_view(), name='classroom_sessions_root'),
    path('sessions', views.ClassroomSessionListCreateView.as_view(), name='classroom_sessions_noslash'),

    # 🔴 TASK 5: ADMIN LIVE SESSION MONITORING ROUTES
    path('live-monitoring/', views.AdminLiveSessionsView.as_view(), name='admin-live-sessions'),
    path('live-monitoring/stats/', views.AdminSessionStatsView.as_view(), name='admin-live-stats-global'),
    path('live-monitoring/<str:session_id>/stats/', views.AdminSessionStatsView.as_view(), name='admin-live-stats-session'),
    path('live-monitoring/<str:session_id>/attendance-summary/', views.AdminAttendanceSummaryView.as_view(), name='admin-attendance-summary'),
    path('live-monitoring/<str:session_id>/force-end/', views.AdminForceEndSessionView.as_view(), name='admin-force-end-session'),

    # --- Your Existing Routes Below ---
    # Session
    path('<str:id>/', views.get_session_details, name='session_details'),
    path('<str:id>/start/', views.start_session, name='start_session'),
    path('<str:id>/end/', views.end_session, name='end_session'),
    path('<str:id>/lock/', views.toggle_session_lock, name='toggle_lock'),

    path('<str:id>/recovery-state/', views.get_recovery_state, name='get_recovery_state'),

    # Hands
    path('<str:id>/raise-hand/', views.raise_hand, name='raise_hand'),
    path('<str:id>/lower-hand/', views.lower_hand, name='lower_hand'),
    path('<str:id>/hand-requests/<int:studentId>/dismiss/', views.dismiss_hand_request, name='dismiss_hand'),

    # Participants
    path('<str:id>/participants/', views.get_participants, name='get_participants'),
    path('<str:id>/participants/<int:participantId>/', views.remove_participant, name='remove_participant'),
    path('<str:id>/participants/<int:participantId>/allow-rejoin/', views.allow_rejoin, name='allow_rejoin'),
    path('<str:id>/participants/<int:participantId>/mute/', views.mute_participant, name='mute_participant'),
    path('<str:id>/participants/<int:participantId>/permissions/', views.update_participant_permissions, name='update_permissions'),

    # Media
    path('<str:id>/media/mute/', views.toggle_self_mute, name='toggle_self_mute'),
    path('<str:id>/media/camera/', views.toggle_self_camera, name='toggle_self_camera'),
    path('<str:id>/mute-all/', views.mute_all_participants, name='mute_all'),

    # Waiting Room
    path('<str:id>/waiting-room/', views.get_waiting_room, name='get_waiting_room'),
    path('<str:id>/waiting-room/<int:userId>/approve/', views.approve_join_request, name='approve_waiting'),
    path('<str:id>/waiting-room/<int:userId>/reject/', views.reject_join_request, name='reject_waiting'),

    # Activity Logs
    path('<str:id>/activity-logs/', views.get_activity_logs, name='get_activity_logs'),
]