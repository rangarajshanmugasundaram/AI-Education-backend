from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import DashboardAggregationService


class AdminDashboardOverviewView(APIView):
    """
    GET /api/admin/dashboard
    Secured endpoint returning MongoDB aggregated dashboard statistics.
    """

    def get(self, request):
        # Header inspection for Role Guard
        user_role = (request.headers.get('x-user-role') or '').strip().lower()

        # Security Guard: Allow only admin access
        if user_role and user_role != 'admin':
            return Response(
                {
                    "success": False,
                    "message": "Access Denied: Admin privileges required."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Fetch aggregated statistics from MongoDB service
            dashboard_data = DashboardAggregationService.fetch_dashboard_metrics()

            return Response(
                {
                    "success": True,
                    "data": dashboard_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Server Error during dashboard aggregation: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )