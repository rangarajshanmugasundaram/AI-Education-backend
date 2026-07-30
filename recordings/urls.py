from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecordingViewSet

router = DefaultRouter(trailing_slash=True)
router.register(r'', RecordingViewSet, basename='recording')

urlpatterns = [
    path('', include(router.urls)),
]