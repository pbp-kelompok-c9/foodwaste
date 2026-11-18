"""Endpoint Django REST Framework modul User & Authentication untuk aplikasi mobile.

Autentikasi memakai token: klien mengirim `Authorization: Token <key>` setelah login.
"""

from django.contrib.auth import logout
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import AccountSerializer, LoginSerializer, RegisterSerializer


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Akun berhasil dibuat. Silakan login.', 'username': user.username},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message': f'Selamat datang, {user.username}!',
            'token': token.key,
            'user': AccountSerializer(user).data,
        })


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({'message': 'Berhasil logout.'})


class MeAPIView(APIView):
    """Akun yang sedang login; dipakai aplikasi untuk memulihkan sesi dari token."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': AccountSerializer(request.user).data})
