from django.contrib.auth import authenticate, login

from rest_framework import serializers


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
