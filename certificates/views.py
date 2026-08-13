from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import CertificateService
from .serializers import GenerateCertificateSerializer, VerifyCertificateSerializer
from .pdf_generator import generate_certificate_pdf_bytes


class CertificateListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_role = request.headers.get('X-User-Role', 'Trainer')
        user_email = request.headers.get('X-User-Email', '')
        search = request.query_params.get('search', None)

        certs = CertificateService.get_all_certificates(
            user_role=user_role,
            user_email=user_email,
            search_query=search
        )
        return Response({'success': True, 'count': len(certs), 'data': certs}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = GenerateCertificateSerializer(data=request.data)
        if serializer.is_valid():
            issued_by = request.headers.get('X-User-Email', 'admin@aieducation.com')
            cert = CertificateService.generate_certificate(serializer.validated_data, issued_by=issued_by)
            return Response({'success': True, 'message': 'Certificate generated successfully', 'data': cert},
                            status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class VerifyCertificateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCertificateSerializer(data=request.data)
        if serializer.is_valid():
            cert_id = serializer.validated_data['certificate_id']
            result = CertificateService.verify_certificate(cert_id)
            if result.get('is_valid'):
                return Response({'success': True, 'valid': True, 'data': result['certificate']},
                                status=status.HTTP_200_OK)
            return Response({'success': False, 'valid': False, 'message': result.get('message', 'Invalid certificate')},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DownloadCertificatePDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, certificate_id):
        cert = CertificateService.get_certificate_by_id(certificate_id)
        if not cert:
            return Response({'success': False, 'message': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        pdf_bytes = generate_certificate_pdf_bytes(cert)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"Certificate_{cert.get('certificate_id')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response