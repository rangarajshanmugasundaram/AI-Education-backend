from django.urls import path
from .views import (
    CertificateListCreateView,
    VerifyCertificateView,
    DownloadCertificatePDFView
)

urlpatterns = [
    # Certificate Generation & List Roster
    path('', CertificateListCreateView.as_view(), name='certificate-list-create'),

    # Public Certificate Verification API
    path('verify/', VerifyCertificateView.as_view(), name='certificate-verify'),

    # Download Certificate PDF API
    path('<str:certificate_id>/download/', DownloadCertificatePDFView.as_view(), name='certificate-download'),
]