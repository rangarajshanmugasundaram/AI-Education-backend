from django.urls import path
from .views import AdminDashboardOverviewView

urlpatterns = [
    path('dashboard', AdminDashboardOverviewView.as_view(), name='admin-dashboard-overview'),
    path('dashboard/', AdminDashboardOverviewView.as_view(), name='admin-dashboard-overview-slash'),
]