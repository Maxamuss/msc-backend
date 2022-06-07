from rest_framework import serializers

from .models import Release


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = [
            'id',
            'release_version',
            'release_notes',
            'released_at',
            'released_by',
            'current_release',
            'parent',
        ]
