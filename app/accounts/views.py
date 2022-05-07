from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework import serializers
from rest_framework.authtoken.models import Token


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        # Check if passed login credentials are valid.
        username = attrs['username']
        password = attrs['password']
        request = self.context['request']
        user = authenticate(request, username=username, password=password)
        if user is None:
            raise serializers.ValidationError('Incorrect login details provided.')

        login(request, user)
        return attrs


class LoginAPIView(GenericAPIView):
    """
    View for users to pass their username and password. If valid, they will receive their Token as
    well as a boolean flag to indicate if they need a password change.
    """

    serializer_class = LoginSerializer
    permission_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = {
            'auth_token': str(Token.objects.get_or_create(user=user)[0]),
            'email': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(data, status=status.HTTP_200_OK)
